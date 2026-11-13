"""Registration, email OTP, login, sessions and password reset."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db import models
from app.db.database import get_ist_time
from qf_testutils import PASSWORD, login, make_user, next_phone, register_verified, signup


def latest_otp(db, email, purpose="registration"):
    db.expire_all()
    return db.execute(select(models.EmailOTP).where(models.EmailOTP.email == email, models.EmailOTP.purpose == purpose)
                      .order_by(models.EmailOTP.id.desc())).scalars().first()


# --- registration validation ----------------------------------------------------

def test_valid_registration_creates_pending_not_account(client, db):
    res = signup(client, "  Asha@Example.COM ", phone="9876543210")
    assert res.status_code == 202
    body = res.json()
    assert body["email"] == "asha@example.com" and body["expires_in"] == 300 and body["resend_after"] == 60
    assert "otp" not in str(body).lower().replace("requires_otp", "")
    assert db.execute(select(models.User)).first() is None  # no account before verification
    pending = db.execute(select(models.PendingRegistration)).scalar_one()
    assert pending.email == "asha@example.com" and pending.phone == "9876543210"
    assert pending.password_hash.startswith("$argon2")
    assert len(client.outbox.to("asha@example.com")) == 1


@pytest.mark.parametrize("payload,fragment", [
    ({"full_name": "A Rao", "phone": "9876543210", "password": PASSWORD}, "email"),
    ({"full_name": "A Rao", "email": "a@x.com", "password": PASSWORD}, "Mobile number is required"),
    ({"full_name": "A Rao", "email": "not-an-email", "phone": "9876543210", "password": PASSWORD}, "Invalid email"),
    ({"full_name": "A Rao", "email": "", "phone": "9876543210", "password": PASSWORD}, "Email is required"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "987654321", "password": PASSWORD}, "too short"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "98765432101", "password": PASSWORD}, "too long"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "5876543210", "password": PASSWORD}, "start with 6, 7, 8 or 9"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "98765 4321", "password": PASSWORD}, "digits only"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "98765abcde", "password": PASSWORD}, "digits only"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "+919876543210", "password": PASSWORD}, "digits only"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "9876543210", "password": "short1"}, "at least 8"),
    ({"full_name": "A Rao", "email": "a@x.com", "phone": "9876543210", "password": "lettersonly"}, "letter and one number"),
])
def test_registration_validation(client, payload, fragment):
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 422
    assert fragment.lower() in str(res.json()).lower()
    assert "password" not in res.json() and PASSWORD not in res.text  # body never echoed


def test_role_cannot_be_supplied_at_registration(client):
    res = client.post("/auth/register", json={"full_name": "Eve", "email": "eve@x.com", "phone": "9876543210",
                                              "password": PASSWORD, "role": "admin"})
    assert res.status_code == 422


def test_duplicate_email_rejected(client, db):
    make_user(db, "taken@x.com")
    res = signup(client, "TAKEN@x.com")
    assert res.status_code == 409 and res.json()["code"] == "EMAIL_TAKEN"


def test_duplicate_mobile_rejected(client, db):
    make_user(db, "first@x.com", phone="9123456789")
    res = signup(client, "second@x.com", phone="9123456789")
    assert res.status_code == 409 and res.json()["code"] == "PHONE_TAKEN"


# --- OTP verification ------------------------------------------------------------

def test_correct_otp_activates_and_signs_in(client, db):
    tokens = register_verified(client, "new@x.com", phone="9988776655")
    assert tokens["user"]["email_verified"] is True and tokens["user"]["role"] == "customer"
    assert tokens["access_token"] and tokens["refresh_token"]
    user = db.execute(select(models.User).where(models.User.email == "new@x.com")).scalar_one()
    assert user.email_verified and user.role == "customer"
    assert db.execute(select(models.PendingRegistration)).first() is None
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "new@x.com"


def test_otp_stored_only_as_hash(client, db):
    signup(client, "hash@x.com")
    code = client.outbox.last_code("hash@x.com")
    row = latest_otp(db, "hash@x.com")
    assert code not in row.code_hash and len(row.code_hash) == 64
    assert code not in client.outbox.to("hash@x.com")[0]["subject"]


def test_incorrect_otp(client, db):
    signup(client, "wrong@x.com")
    code = client.outbox.last_code("wrong@x.com")
    bad = "000000" if code != "000000" else "111111"
    res = client.post("/auth/verify-registration", json={"email": "wrong@x.com", "otp": bad})
    assert res.status_code == 400 and res.json()["code"] == "OTP_INVALID"
    assert "4 attempts left" in res.json()["detail"]
    assert db.execute(select(models.User)).first() is None


def test_malformed_otp_rejected(client):
    signup(client, "fmt@x.com")
    assert client.post("/auth/verify-registration", json={"email": "fmt@x.com", "otp": "12ab56"}).status_code == 422


def test_expired_otp(client, db):
    signup(client, "late@x.com")
    code = client.outbox.last_code("late@x.com")
    row = latest_otp(db, "late@x.com")
    row.expires_at = get_ist_time() - timedelta(seconds=1)
    db.commit()
    res = client.post("/auth/verify-registration", json={"email": "late@x.com", "otp": code})
    assert res.status_code == 400 and res.json()["code"] == "OTP_EXPIRED"


def test_reused_otp(client, db):
    signup(client, "reuse@x.com")
    code = client.outbox.last_code("reuse@x.com")
    assert client.post("/auth/verify-registration", json={"email": "reuse@x.com", "otp": code}).status_code == 200
    # Same code against the same purpose again (e.g. a replayed request): already used.
    db.add(models.PendingRegistration(email="reuse2@x.com", full_name="R", phone=next_phone(), password_hash="x",
                                      created_at=get_ist_time(), expires_at=get_ist_time() + timedelta(hours=1)))
    db.commit()
    res = client.post("/auth/verify-registration", json={"email": "reuse@x.com", "otp": code})
    assert res.status_code == 409 and res.json()["code"] == "ALREADY_VERIFIED"
    # Reuse at the OTP layer directly
    from app.services import otp_service
    from app.core.errors import AppError
    with pytest.raises(AppError) as err:
        otp_service.verify(db, "reuse@x.com", "registration", code)
    assert err.value.code == "OTP_ALREADY_USED"


def test_attempt_limit_per_code(client, db):
    signup(client, "brute@x.com")
    code = client.outbox.last_code("brute@x.com")
    bad = "000000" if code != "000000" else "111111"
    for _ in range(5):
        client.post("/auth/verify-registration", json={"email": "brute@x.com", "otp": bad})
    res = client.post("/auth/verify-registration", json={"email": "brute@x.com", "otp": code})
    assert res.status_code == 400 and res.json()["code"] == "OTP_ATTEMPTS_EXCEEDED"


def test_failed_attempts_lock_email_across_codes(client, db, monkeypatch):
    monkeypatch.setenv("OTP_RESEND_COOLDOWN_SECONDS", "0")
    signup(client, "lock@x.com")
    for _ in range(2):
        code = client.outbox.last_code("lock@x.com")
        bad = "000000" if code != "000000" else "111111"
        for _ in range(5):
            client.post("/auth/verify-registration", json={"email": "lock@x.com", "otp": bad})
        from app.core.config import get_settings
        get_settings.cache_clear()
        assert client.post("/auth/resend-otp", json={"email": "lock@x.com", "purpose": "registration"}).status_code == 200
    res = client.post("/auth/verify-registration", json={"email": "lock@x.com", "otp": client.outbox.last_code("lock@x.com")})
    assert res.status_code == 429 and res.json()["code"] == "OTP_LOCKED"


def test_resend_cooldown(client, db):
    signup(client, "cool@x.com")
    res = client.post("/auth/resend-otp", json={"email": "cool@x.com", "purpose": "registration"})
    assert res.status_code == 429 and res.json()["code"] == "OTP_COOLDOWN"
    assert int(res.headers["Retry-After"]) <= 61


def test_resend_invalidates_previous_code(client, db):
    signup(client, "again@x.com")
    first = client.outbox.last_code("again@x.com")
    row = latest_otp(db, "again@x.com")
    row.created_at = get_ist_time() - timedelta(seconds=61)
    db.commit()
    assert client.post("/auth/resend-otp", json={"email": "again@x.com", "purpose": "registration"}).status_code == 200
    second = client.outbox.last_code("again@x.com")
    if first != second:
        res = client.post("/auth/verify-registration", json={"email": "again@x.com", "otp": first})
        assert res.status_code == 400 and res.json()["code"] in ("OTP_SUPERSEDED", "OTP_INVALID")
    assert client.post("/auth/verify-registration", json={"email": "again@x.com", "otp": second}).status_code == 200


def test_hourly_otp_limit(client, db):
    signup(client, "many@x.com")
    for _ in range(4):
        row = latest_otp(db, "many@x.com")
        row.created_at = row.created_at - timedelta(seconds=61)
        db.commit()
        assert client.post("/auth/resend-otp", json={"email": "many@x.com", "purpose": "registration"}).status_code == 200
    row = latest_otp(db, "many@x.com")
    row.created_at = row.created_at - timedelta(seconds=61)
    db.commit()
    res = client.post("/auth/resend-otp", json={"email": "many@x.com", "purpose": "registration"})
    assert res.status_code == 429 and res.json()["code"] == "OTP_RATE_LIMITED"


def test_email_failure_does_not_activate(client, db, monkeypatch):
    from app.services import email_transport

    def broken(*a, **k):
        raise email_transport.EmailDeliveryError("smtp down")

    monkeypatch.setattr(email_transport, "send", broken)
    res = signup(client, "nomail@x.com")
    assert res.status_code == 503 and res.json()["code"] == "EMAIL_DELIVERY_FAILED"
    assert db.execute(select(models.User)).first() is None
    assert latest_otp(db, "nomail@x.com") is None  # undeliverable code discarded


# --- login -------------------------------------------------------------------------

def test_login_before_verification_impossible(client):
    signup(client, "pending@x.com")
    res = client.post("/auth/login", json={"email": "pending@x.com", "password": PASSWORD})
    assert res.status_code == 401  # no account exists until the OTP is verified


def test_legacy_unverified_account_must_verify(client, db):
    make_user(db, "legacy@x.com", verified=False)
    res = client.post("/auth/login", json={"email": "legacy@x.com", "password": PASSWORD})
    assert res.status_code == 403 and res.json()["code"] == "EMAIL_NOT_VERIFIED"
    assert client.post("/auth/resend-otp", json={"email": "legacy@x.com", "purpose": "verify_email"}).status_code == 200
    code = client.outbox.last_code("legacy@x.com")
    res = client.post("/auth/verify-email", json={"email": "legacy@x.com", "otp": code})
    assert res.status_code == 200 and res.json()["user"]["email_verified"] is True
    assert client.post("/auth/login", json={"email": "legacy@x.com", "password": PASSWORD}).status_code == 200


def test_unverified_token_cannot_reach_protected_api(client, db):
    user = make_user(db, "sneaky@x.com", verified=False)
    from app.core.security import create_access_token
    token, _ = create_access_token(user.id, "customer", 0)
    res = client.get("/complaints", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403 and res.json()["code"] == "EMAIL_NOT_VERIFIED"


def test_wrong_password_and_lockout(client, db):
    make_user(db, "locky@x.com")
    for _ in range(5):
        res = client.post("/auth/login", json={"email": "locky@x.com", "password": "Wrong-pass-1"})
        assert res.status_code == 401 and res.json()["detail"] == "Invalid email or password."
    res = client.post("/auth/login", json={"email": "locky@x.com", "password": PASSWORD})
    assert res.status_code == 429 and res.json()["code"] == "ACCOUNT_LOCKED"


def test_unknown_email_same_error_as_wrong_password(client):
    res = client.post("/auth/login", json={"email": "ghost@x.com", "password": PASSWORD})
    assert res.status_code == 401 and res.json()["detail"] == "Invalid email or password."


def test_disabled_account_cannot_login(client, db):
    make_user(db, "off@x.com", active=False)
    assert client.post("/auth/login", json={"email": "off@x.com", "password": PASSWORD}).status_code == 403


def test_legacy_bcrypt_hash_still_works_and_is_upgraded(client, db):
    import hashlib

    import bcrypt
    user = make_user(db, "old@x.com", password=None)
    user.hashed_password = bcrypt.hashpw(hashlib.sha256(PASSWORD.encode()).hexdigest().encode(), bcrypt.gensalt()).decode()
    db.commit()
    assert client.post("/auth/login", json={"email": "old@x.com", "password": PASSWORD}).status_code == 200
    db.expire_all()
    assert db.get(models.User, user.id).hashed_password.startswith("$argon2")


def test_otp_login_never_creates_accounts(client, db):
    res = client.post("/auth/request-otp", json={"email": "nobody@x.com"})
    assert res.status_code == 200
    assert db.execute(select(models.User)).first() is None
    assert client.outbox.to("nobody@x.com") == []


def test_otp_login_for_existing_user(client, db):
    make_user(db, "otp@x.com")
    client.post("/auth/request-otp", json={"email": "otp@x.com"})
    code = client.outbox.last_code("otp@x.com")
    res = client.post("/auth/verify-otp", json={"email": "otp@x.com", "otp": code})
    assert res.status_code == 200 and res.json()["user"]["email"] == "otp@x.com"


# --- sessions ----------------------------------------------------------------------

def test_refresh_rotation_and_reuse_detection(client, db):
    make_user(db, "rot@x.com")
    first = login(client, "rot@x.com")
    second = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    assert second.json()["refresh_token"] != first["refresh_token"]
    replay = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert replay.status_code == 401 and replay.json()["code"] == "REFRESH_TOKEN_REUSED"
    # the whole family is now revoked, including the token issued by the legitimate rotation
    assert client.post("/auth/refresh", json={"refresh_token": second.json()["refresh_token"]}).status_code == 401


def test_logout_revokes_access_and_refresh(client, db):
    make_user(db, "bye@x.com")
    tokens = login(client, "bye@x.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers).status_code == 200
    assert client.get("/auth/me", headers=headers).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_missing_and_expired_jwt(client, db, monkeypatch):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"}).status_code == 401
    user = make_user(db, "exp@x.com")
    import time

    import jwt
    from app.core.config import get_settings
    token = jwt.encode({"sub": str(user.id), "role": "customer", "tv": 0, "jti": "x", "type": "access",
                        "iat": int(time.time()) - 3600, "exp": int(time.time()) - 60, "iss": "quickfix-api"},
                       get_settings().jwt_secret_key, algorithm="HS256")
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401 and res.json()["code"] == "TOKEN_EXPIRED"
    forged = jwt.encode({"sub": str(user.id), "role": "admin", "tv": 0, "jti": "y", "type": "access",
                         "iat": int(time.time()), "exp": int(time.time()) + 60, "iss": "quickfix-api"},
                        "attacker-secret", algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


# --- password reset ------------------------------------------------------------------

def test_password_reset_flow(client, db):
    make_user(db, "reset@x.com")
    old = login(client, "reset@x.com")
    res = client.post("/auth/forgot-password", json={"email": "reset@x.com"})
    assert res.status_code == 200
    code = client.outbox.last_code("reset@x.com")
    res = client.post("/auth/reset-password", json={"email": "reset@x.com", "otp": code, "new_password": "Brand-new-99"})
    assert res.status_code == 200
    assert client.post("/auth/login", json={"email": "reset@x.com", "password": PASSWORD}).status_code == 401
    assert client.post("/auth/login", json={"email": "reset@x.com", "password": "Brand-new-99"}).status_code == 200
    # every earlier session is revoked
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old['access_token']}"}).status_code == 401
    assert any("password was changed" in m["subject"].lower() for m in client.outbox.to("reset@x.com"))


def test_forgot_password_does_not_reveal_accounts(client):
    res = client.post("/auth/forgot-password", json={"email": "unknown@x.com"})
    assert res.status_code == 200 and client.outbox.to("unknown@x.com") == []


def test_reset_with_wrong_code(client, db):
    make_user(db, "rw@x.com")
    client.post("/auth/forgot-password", json={"email": "rw@x.com"})
    code = client.outbox.last_code("rw@x.com")
    bad = "000000" if code != "000000" else "111111"
    res = client.post("/auth/reset-password", json={"email": "rw@x.com", "otp": bad, "new_password": "Brand-new-99"})
    assert res.status_code == 400


# --- Google ---------------------------------------------------------------------------

def test_google_login_requires_server_verified_token_and_otp(client, db, monkeypatch):
    from app.services import auth_service

    make_user(db, "g@x.com")

    class Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"aud": "test-google-client-id", "email": "g@x.com", "email_verified": "true", "sub": "123"}

    monkeypatch.setattr(auth_service.requests, "get", lambda *a, **k: Resp())
    res = client.post("/auth/google", json={"access_token": "ya29.fake-token-value"})
    assert res.status_code == 200 and res.json()["requires_otp"] is True
    code = client.outbox.last_code("g@x.com")
    res = client.post("/auth/google-verify-otp", json={"email": "g@x.com", "otp": code})
    assert res.status_code == 200


def test_google_token_for_other_app_rejected(client, db, monkeypatch):
    from app.services import auth_service

    class Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"aud": "someone-else", "azp": "someone-else", "email": "g@x.com", "email_verified": "true"}

    monkeypatch.setattr(auth_service.requests, "get", lambda *a, **k: Resp())
    assert client.post("/auth/google", json={"access_token": "ya29.fake-token-value"}).status_code == 401


def test_google_unknown_email_is_sent_to_signup(client, db, monkeypatch):
    from app.services import auth_service

    class Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"aud": "test-google-client-id", "email": "fresh@x.com", "email_verified": "true"}

    monkeypatch.setattr(auth_service.requests, "get", lambda *a, **k: Resp())
    res = client.post("/auth/google", json={"access_token": "ya29.fake-token-value"})
    assert res.status_code == 404 and res.json()["code"] == "ACCOUNT_NOT_FOUND"
    assert db.execute(select(models.User)).first() is None


def test_logout_is_idempotent_for_ended_sessions(client, db):
    make_user(db, "twice@x.com")
    tokens = login(client, "twice@x.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    body = {"refresh_token": tokens["refresh_token"]}
    assert client.post("/auth/logout", json=body, headers=headers).status_code == 200
    # already signed out (e.g. after a role change revoked the session): still 200, no error noise
    assert client.post("/auth/logout", json=body, headers=headers).status_code == 200
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me", headers=headers).status_code == 401
