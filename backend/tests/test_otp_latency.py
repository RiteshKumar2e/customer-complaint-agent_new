"""
Latency budget for OTP requests. Every statement to Turso is a network round
trip (~100-250 ms), so the OTP endpoints must use few of them, and the email
must be sent while the database work happens, not after it.
"""
import time

from sqlalchemy import event

from app.db.database import engine
from qf_testutils import make_user, next_phone


class StatementCounter:
    def __init__(self):
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1


def count_statements(fn):
    counter = StatementCounter()
    event.listen(engine, "before_cursor_execute", counter)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", counter)
    return counter.count, result


def test_register_uses_few_round_trips(client):
    n, res = count_statements(lambda: client.post("/auth/register", json={
        "full_name": "Fast User", "email": "fast@x.com", "phone": next_phone(), "password": "Secure-pass-123"}))
    assert res.status_code == 202
    assert n <= 9, f"register issued {n} statements"


def test_resend_and_forgot_use_few_round_trips(client, db):
    make_user(db, "rt@x.com")
    n, res = count_statements(lambda: client.post("/auth/forgot-password", json={"email": "rt@x.com"}))
    assert res.status_code == 200
    assert n <= 7, f"forgot-password issued {n} statements"


def test_email_is_sent_concurrently_with_database_work(db, outbox, monkeypatch):
    """
    Brevo takes 0.5 s and the Turso write+commit 0.4 s. Done one after the other
    that is 0.9 s; overlapped it must be close to 0.5 s.
    """
    from app.services import email_transport, otp_service

    def slow_send(to, subject, html, text, category="notification", retries=0):
        time.sleep(0.5)
        outbox.append({"to": to, "subject": subject, "html": html, "text": text, "category": category})

    real_commit = db.commit

    def slow_commit():
        time.sleep(0.4)
        real_commit()

    monkeypatch.setattr(email_transport, "send", slow_send)
    monkeypatch.setattr(db, "commit", slow_commit)
    t0 = time.perf_counter()
    otp_service.issue(db, "par@x.com", "login", check_limits=False)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.75, f"took {elapsed:.2f}s; sequential would be ~0.9s"
    assert outbox.last_code("par@x.com")


def test_failed_parallel_send_discards_the_code(client, db, monkeypatch):
    from sqlalchemy import select

    from app.db import models
    from app.services import email_transport

    def broken(*a, **k):
        time.sleep(0.05)
        raise email_transport.EmailDeliveryError("brevo down")

    monkeypatch.setattr(email_transport, "send", broken)
    res = client.post("/auth/register", json={"full_name": "Fast User", "email": "down@x.com",
                                              "phone": next_phone(), "password": "Secure-pass-123"})
    assert res.status_code == 503
    db.expire_all()
    assert db.execute(select(models.EmailOTP).where(models.EmailOTP.email == "down@x.com")).first() is None
