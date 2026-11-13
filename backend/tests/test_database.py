"""Turso dialect, migrations, constraints, transactions and failure handling (local libSQL file)."""
import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.config import ConfigError
from app.db import libsql_dialect, models
from app.db.database import SessionLocal, engine, get_ist_time, resolve_turso_target
from app.db.migrations import run_migrations
from qf_testutils import make_user


def test_engine_uses_turso_dialect():
    assert engine.dialect.name == "sqlite" and engine.dialect.driver == "turso"


def test_schema_matches_models_after_migrations():
    insp = inspect(engine)
    for table in models.Base.metadata.sorted_tables:
        assert {c["name"] for c in insp.get_columns(table.name)} == {c.name for c in table.columns}, table.name


def test_migrations_are_idempotent():
    assert run_migrations(engine) == []


@pytest.mark.parametrize("url", ["postgresql://u:p@h/db", "mysql://h/db", "sqlite:///x.db", ""])
def test_non_turso_urls_rejected(url):
    with pytest.raises(ConfigError):
        resolve_turso_target(url, "")


def test_token_taken_from_env_or_legacy_query():
    assert resolve_turso_target("libsql://db-org.turso.io", "tok") == ("libsql://db-org.turso.io", "tok")
    assert resolve_turso_target("libsql://db-org.turso.io?authToken=legacy", "") == ("libsql://db-org.turso.io", "legacy")


def test_user_crud(db):
    user = make_user(db, "crud@x.com")
    user.full_name = "Changed"
    db.commit()
    db.expire_all()
    assert db.get(models.User, user.id).full_name == "Changed"
    db.delete(db.get(models.User, user.id))
    db.commit()
    assert db.get(models.User, user.id) is None


def test_complaint_crud_and_fk(db):
    user = make_user(db, "c@x.com")
    complaint = models.Complaint(ticket_id="QX-T-1", user_id=user.id, name="C", email=user.email,
                                 category="Other", priority="Low")
    db.add(complaint)
    db.commit()
    assert complaint.status == "open"
    db.add(models.ComplaintEvent(complaint_id=999999, event_type="x", created_at=get_ist_time()))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pytest.mark.parametrize("field,value", [("role", "superuser"), ("email", None)])
def test_constraints(db, field, value):
    data = {"email": "k@x.com", "full_name": "K", "role": "customer"}
    data[field] = value
    db.add(models.User(**data))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_unique_phone_and_email(db):
    make_user(db, "p1@x.com", phone="9000000001")
    db.add(models.User(email="p2@x.com", phone="9000000001"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(models.User(email="p1@x.com"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_transaction_rollback_is_atomic(db):
    db.add(models.User(email="atomic1@x.com", phone="9000000011"))
    db.add(models.User(email="atomic2@x.com", phone="9000000011"))  # violates unique phone
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.execute(select(models.User).where(models.User.email.like("atomic%"))).first() is None


def test_savepoint(db):
    make_user(db, "outer@x.com")
    with db.begin_nested():
        db.add(models.User(email="inner@x.com"))
    nested = db.begin_nested()
    db.add(models.User(email="discard@x.com"))
    nested.rollback()
    db.commit()
    emails = set(db.execute(select(models.User.email)).scalars())
    assert {"outer@x.com", "inner@x.com"} <= emails and "discard@x.com" not in emails


def test_otp_lifecycle_rows(client, db):
    from qf_testutils import signup
    signup(client, "life@x.com")
    row = db.execute(select(models.EmailOTP)).scalar_one()
    assert row.consumed_at is None and row.attempts == 0 and row.purpose == "registration"
    client.post("/auth/verify-registration", json={"email": "life@x.com", "otp": client.outbox.last_code("life@x.com")})
    db.expire_all()
    assert db.get(models.EmailOTP, row.id).consumed_at is not None


def test_driver_errors_are_translated():
    assert isinstance(libsql_dialect.translate_error(ValueError("UNIQUE constraint failed: users.email")),
                      libsql_dialect.IntegrityError)
    hrana = ValueError('Hrana: `api error: `status=404 Not Found, body=Host not found``')
    assert isinstance(libsql_dialect.translate_error(hrana), libsql_dialect.OperationalError)


def test_unreachable_database_returns_503(client, monkeypatch):
    from app.api import deps

    def down(*a, **k):
        raise OperationalError("SELECT 1", {}, libsql_dialect.OperationalError("database unavailable: timeout"))

    monkeypatch.setattr(deps, "decode_access_token", lambda token: (_ for _ in ()).throw(down()))
    res = client.get("/complaints", headers={"Authorization": "Bearer x"})
    assert res.status_code == 503 and res.json()["code"] == "DATABASE_UNAVAILABLE"
    assert "SELECT" not in res.text


def test_readiness_reports_database_failure(client, monkeypatch):
    import app.main as main

    def broken():
        raise OperationalError("SELECT 1", {}, Exception("down"))

    monkeypatch.setattr(main, "check_database", broken)
    assert client.get("/health/ready").status_code == 503


def test_datetime_round_trip():
    with SessionLocal() as s:
        s.execute(text("CREATE TEMP TABLE IF NOT EXISTS t_dt (v DATETIME)"))
        now = get_ist_time()
        s.execute(text("INSERT INTO t_dt VALUES (:v)"), {"v": now})
        assert s.execute(text("SELECT v FROM t_dt")).scalar().startswith(now.isoformat(" ")[:19])


def test_idle_dead_connection_is_replaced_transparently():
    engine.dispose()
    with engine.connect() as conn:
        record = conn.connection._connection_record
        raw = conn.connection.dbapi_connection
    record.info["last_used"] = 0  # idle for a long time
    raw._raw.close()              # the server dropped it meanwhile
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_recently_used_connection_is_not_pinged():
    from sqlalchemy import event as sa_event

    statements = []
    listener = lambda *a, **k: statements.append(a[2])  # noqa: E731
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    sa_event.listen(engine, "before_cursor_execute", listener)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 2"))
    finally:
        sa_event.remove(engine, "before_cursor_execute", listener)
    assert statements == ["SELECT 2"]  # no extra ping round trip
