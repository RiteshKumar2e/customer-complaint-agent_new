# Full-Stack Audit Report

**Project:** Quickfix Agentic AI — Customer Complaint Agent
**Date:** 2026-07-15
**Auditor:** FullStack Guardian (automated senior full-stack / QA / security review)
**Scope:** `full` (frontend + backend + API + security), with `--fix` applied to safe, confirmed backend defects.

---

## Executive Summary

The application **builds and runs**. The React/Vite frontend compiles to a production bundle, and the FastAPI backend starts, connects to the database, runs migrations, and serves all routers. The AI pipeline degrades gracefully to local fallbacks when no LLM API keys are present.

During live API testing I found and **fixed two confirmed backend defects** that broke error handling on every write endpoint:

1. The global validation handler crashed on any malformed request body, so clients received a dropped connection instead of an HTTP 422. **Fixed and re-verified.**
2. Four complaint endpoints swallowed their own `HTTPException(404)` in a broad `except Exception`, returning HTTP 500 with an empty body instead of a clean 404. **Fixed and re-verified.**

The audit also surfaced one **critical security theme that was not auto-fixed** because it requires an authentication redesign (out of safe-fix scope): **no backend route verifies the JWT.** Authorization is performed entirely by trusting a client-supplied `email`/`agent_email` query parameter. Admin endpoints that expose every user's email, phone, IP address, and location are reachable with **zero credentials** — I confirmed this by calling them directly during testing.

**Verdict: WORKING WITH CRITICAL ISSUES.** The confirmed functional bugs are fixed, but the broken access-control model must be addressed before this can be considered production-ready.

---

## Project Architecture

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite (rolldown-vite 7.2.5), Framer Motion, Recharts, Three.js, jsPDF, axios |
| Backend | FastAPI 0.104 / 0.115, Uvicorn, SQLAlchemy 2.0, Pydantic 2 |
| Database | SQLite by default; supports Postgres, MySQL/Aiven, Turso (libsql) via `DATABASE_URL` |
| AI | Groq (primary) → Gemini (fallback) → local scikit-learn/TextBlob fallback |
| Auth | JWT (python-jose) + bcrypt (passlib, SHA-256 pre-hash), OTP email, Google OAuth |
| Email | Brevo API (with Resend/SMTP fallbacks) |
| Cache | Redis (optional; fails silent if unavailable) |
| Deploy | Docker Compose, Vercel (frontend), Render (backend) |

**Frontend → backend contract:** `frontend/src/api.js` (axios, base URL `VITE_API_URL`).
**Routers mounted (`app/main.py`):** `api/routes` (complaints), `api/chat`, `routes/feedback`, `routes/auth`, `routes/agent_module`.
**Not mounted (dead code):** `app/routes/agent_routes.py`, `app/routes/admin_login_history.py` — never imported.

---

## Commands Executed

| Command | Result |
|---|---|
| `npm run build` (frontend) | ✅ Built in ~5s, 2927 modules |
| `npx eslint src` | ⚠️ ~90 problems in `src` (mostly unused vars; a few real hook issues) |
| `python -m compileall app` | ✅ Exit 0 (no syntax errors) |
| `pip install groq passlib bcrypt python-jose` | ✅ Installed missing runtime deps into venv |
| `uvicorn app.main:app` | ✅ Boots, migrations run, all routers served |
| ~20 live API calls (curl) | ✅ See API Findings |
| `python test_language_matching.py` | ✅ Runs (print-based, graceful fallback) |
| `npm audit --omit=dev` | ⚠️ 6 vulns (1 critical, 3 high, 2 moderate) |

---

## Build Results

- **Frontend:** ✅ Production build succeeds.
  - Main JS chunk **1,859 kB** (536 kB gzip) — exceeds Vite's 500 kB warning. No code-splitting/lazy-loading.
  - Also bundles `html2canvas` (200 kB) and `jspdf` (`index.es` 151 kB) — large PDF/export libs loaded eagerly.
- **Backend:** ✅ Byte-compiles cleanly; imports resolve after installing missing packages.

---

## Test Results

- **Existing tests:** Only `backend/test_language_matching.py` exists. It is a **print-based script with no assertions**, so it cannot pass or fail — it demonstrates behavior only. It ran successfully and confirmed language detection + graceful AI fallback.
- **No automated test suite** (no pytest/vitest/jest config, no CI test job).
- **Manual API tests:** executed against a local instance on a scratch SQLite DB with all external keys blanked (no email/LLM side effects). Results in API Findings.

---

## Frontend Findings

| ID | Severity | Area | File | Problem |
|---|---|---|---|---|
| FE-1 | HIGH | Perf/UX | `frontend/src/App.jsx:298` | Session-expiry alert is hard-coded in Hindi only (`"आपका session ... expire हो गया है"`), inconsistent with the otherwise English UI. |
| FE-2 | MEDIUM | Correctness | `frontend/src/App.jsx:317-345` | `beforeunload` clears the whole session on tab close using a `sessionStorage` "isRefreshing" flag heuristic; this is fragile and can log users out unexpectedly on navigation. |
| FE-3 | MEDIUM | Perf | build output | 1.86 MB main bundle, no route-level code splitting or lazy import of heavy libs (three.js, jspdf, html2canvas). |
| FE-4 | LOW | Code quality | many components | `motion` imported but unused across ~10 components; several unused vars/imports (`useMemo`, `getAllComplaints`, `data`, `err`). |
| FE-5 | LOW | React | `Login.jsx`, `Signup.jsx`, `OTPModal.jsx`, `CustomCursor.jsx`, `CookieConsent.jsx` | `setState` called synchronously inside `useEffect` (React Hooks lint), risking cascading renders. |
| FE-6 | LOW | React | `Landing.jsx:645` | Component defined during render (`react-hooks/static-components`) — can remount subtree each render. |

No hardcoded `localhost`/backend URLs found in `src` (uses `VITE_API_URL`) — good.

---

## UI/UX Findings

- Static review only (no browser automation available in this environment). Component structure is consistent: shared CSS per component under `src/styles`, a theme toggle, cookie consent, notification center, and reusable cards/forms.
- **SUGGESTION:** The mixed-language user-facing string (FE-1) hurts UX consistency; standardize copy.
- **SUGGESTION:** Verify destructive actions (delete complaint, bulk delete, delete login history) show a confirmation dialog — the API supports them and they are irreversible.

---

## Responsive Findings

- **Not tested at runtime** (no headless browser / device emulation available here). The frontend uses per-component CSS and an `isMobile`-style detection in places. Recommend a manual pass at 360×800, 390×844, 768×1024, 1366×768, 1920×1080, and an axe-core run — none of these were performed and must not be marked as passing.

---

## Accessibility Findings

- **Not tested at runtime** (no axe-core run possible without a live browser here). Recommend adding `@axe-core/playwright` and testing keyboard nav, focus management on modals (OTPModal, SignInPromptModal, Feedback), form label associations, and color contrast. Unverified — do not assume compliant.

---

## Backend Findings

| ID | Severity | Area | File:line | Problem | Status |
|---|---|---|---|---|---|
| BE-1 | HIGH | Error handling | `app/main.py:27` (orig) | Validation handler called `await request.body()` a second time → `ClientDisconnect` → handler crashed → **every 422 became a dropped connection** (curl `HTTP 000`). | ✅ FIXED |
| BE-2 | HIGH | Error handling | `app/api/routes.py` (review/status/delete/resolution-feedback) | Broad `except Exception` caught the route's own `HTTPException(404)` and re-raised as **500 with empty detail**. | ✅ FIXED |
| BE-3 | MEDIUM | Dead code | `app/routes/agent_routes.py`, `app/routes/admin_login_history.py` | Never imported/mounted; a stale parallel implementation of the agent module. Confusing and unmaintained. | Documented |
| BE-4 | LOW | Logic | `app/routes/auth.py:189` | `request_otp` returns `is_new_user = user.id is None`, but `db.flush()` has already populated `user.id`, so this is **always `False`**. | Documented |
| BE-5 | LOW | Config | `app/main.py:40` | CORS entry `"https://*.vercel.app"` is a literal string; Starlette does not expand wildcard subdomains without `allow_origin_regex`, so it never matches. | Documented |
| BE-6 | LOW | Reliability | `backend/requirements.txt` vs venv | `groq`, `passlib`, `bcrypt`, `python-jose` (and others) were **not installed** in the committed venv; the server failed to boot until installed. Requirements/venv drift. | Mitigated (installed) |
| BE-7 | LOW | Portability | multiple `print("… emoji …")` | Emoji in `print()` crash on Windows `cp1252` consoles (`UnicodeEncodeError`) unless `PYTHONIOENCODING=utf-8` is set — this blocked the first boot attempt. | Documented |

---

## API Findings

Tested locally (port 8001/8002, scratch DB, keys blanked). "After fix" reflects the current code.

| Endpoint | Case | Result |
|---|---|---|
| `GET /` | liveness | ✅ 200 `{"status":"Quickfix Backend Running"}` |
| `POST /auth/register` | valid | ✅ 200, user created, password hashed |
| `POST /auth/register` | duplicate email | ✅ 400 |
| `POST /auth/register` | missing email | ❌ before: connection reset → ✅ after: **422 with detail** |
| `POST /auth/login-password` | correct | ✅ 200 + JWT |
| `POST /auth/login-password` | wrong password | ✅ 401 |
| `POST /auth/login-password` | unknown user | ✅ 404 |
| `GET /agent/complaints/queue` | missing `agent_email` | ✅ 422 |
| `GET /agent/complaints/queue` | non-agent user | ✅ 403 (server-side role check) |
| `GET /agent/complaints/queue` | unknown user | ✅ 404 |
| `DELETE /complaint/{id}` | missing ticket | ❌ before: **500** → ✅ after: **404** |
| `PATCH /complaint/{id}/status` | missing ticket | ❌ before: **500** → ✅ after: **404** |
| `POST /complaint/{id}/review` | missing ticket | ❌ before: **500** → ✅ after: **404** |
| `POST /complaint/{id}/resolution-feedback` | missing ticket | ❌ before: **500** → ✅ after: **404** |
| `POST /agent/chat` | no LLM keys | ✅ 200, graceful fallback response |
| `POST /auth/forgot-password` | unknown email | ✅ Non-enumerating generic message |
| `GET /auth/admin/login-history` | **no credentials** | ⚠️ **200 — returns all users' PII** (see SEC-1) |
| `GET /auth/admin/login-stats` | **no credentials** | ⚠️ **200 — returns login stats/failures** (see SEC-1) |

---

## Database Findings

- Schema is coherent (SQLAlchemy models with FKs, indexes on hot columns, timestamps). Deletes manually clean up child rows (`AgentResolution`, `ModelValidation`) to satisfy FK constraints.
- **DB-1 (MEDIUM):** `run_migrations()` performs schema changes via raw `ALTER TABLE` in bare `try/except: pass` blocks. Column names are hardcoded (no injection risk), but silent failures hide migration problems. Consider Alembic.
- **DB-2 (LOW):** `get_ist_time()` uses `datetime.utcnow() + 5:30` for IST rather than timezone-aware datetimes; fine functionally but not TZ-safe.
- **DB-3 (see SEC-4):** Three `.db` files are committed to git; one (`backend/complaints.db`) contains a real complaint row with populated `name` and `email` columns.

---

## Security Findings

| ID | Severity | Area | File:line | Problem |
|---|---|---|---|---|
| **SEC-1** | **CRITICAL** | Broken access control | `app/routes/auth.py:436,480,519`; `app/routes/agent_module.py:27`; `app/api/routes.py:129` | **No route verifies the JWT.** The frontend axios client never sends the token, and the backend authorizes solely by a client-supplied `email`/`agent_email` query param. `/auth/admin/login-history`, `/auth/admin/login-stats`, and `DELETE /auth/admin/login-history/{id}` have **no auth check at all** and expose/delete every user's email, phone, IP, and location — confirmed reachable with zero credentials. Agent/admin data endpoints are accessible to anyone who knows a privileged email. |
| SEC-2 | HIGH | Secrets | `app/routes/auth.py:99` | `JWT_SECRET_KEY` falls back to hardcoded `"your-secret-key-keep-it-safe"` if the env var is missing — forgeable tokens in any misconfigured deploy. Should fail fast if unset. |
| SEC-3 | HIGH | Auth (Google) | `app/routes/auth.py:242-249` | Google sign-in does **not verify the Google ID token** (`email = data.token`); the client asserts its own email. Combined with OTP this is partly mitigated, but the token must be verified server-side. |
| SEC-4 | HIGH | Data exposure | `backend/complaints.db`, `backend/customer_complaint.db`, `complaints.db` (git-tracked) | SQLite DBs are committed to the repo; `backend/complaints.db` holds a real complaint row with `name`/`email` PII. Remove from tracking and purge history. |
| SEC-5 | HIGH | Dependencies | `frontend/package.json` | `npm audit`: 6 vulns (1 critical, 3 high, 2 moderate) — `jspdf` (PDF/JS injection, DoS) and `lodash` (prototype pollution, code injection via `_.template`). |
| SEC-6 | MEDIUM | CORS | `app/main.py:33-50` | `allow_credentials=True` with `os.getenv("FRONTEND_URL", "*")` can yield `"*"` + credentials in non-prod; wildcard subdomain entry is non-functional (BE-5). |
| SEC-7 | LOW | Info leak | `app/api/routes.py` (500 handlers) | Remaining `except Exception` handlers return `str(e)` to the client, which can leak internal error details. |

**Positives:** Passwords bcrypt-hashed with SHA-256 pre-hash (72-char safe); SQLAlchemy ORM parameterizes queries (no SQL injection found); `forgot-password` does not enumerate users; `.env` is gitignored and not tracked; Redis/email/LLM failures degrade gracefully.

> SEC-1/SEC-3 are an **authentication redesign** and were intentionally **not auto-fixed** (outside safe-fix scope). See Recommended Tests / fix guidance below.

---

## Performance Findings

- **Frontend:** 1.86 MB main chunk, no code-splitting; heavy libs (three.js, jspdf, html2canvas) eagerly bundled. The custom `CursorTrail` canvas runs a continuous `requestAnimationFrame` particle system with global mousemove/touchmove listeners — measurable CPU/battery cost on low-end/mobile devices.
- **Backend:** AI orchestrator already parallelizes calls with `asyncio.gather` (good). `find_similar_complaints` / RAG re-index on startup (8 docs — fine at this scale). No pagination concerns at current scale; `GET /complaints` for an admin loads **all** complaints with no pagination (`Complaint).all()`) — will not scale.
- Connection pool configured (`pool_size=10, max_overflow=20, pool_pre_ping=True`).

---

## Fixes Applied

| ID | File | Change | Verification |
|---|---|---|---|
| BE-1 | `app/main.py` | Validation handler now uses `exc.body` instead of re-reading `await request.body()`; response wrapped in `jsonable_encoder`. Added `from fastapi.encoders import jsonable_encoder`. | Re-ran `POST /auth/register` with missing email → now returns **422** with a proper JSON detail/body (was a dropped connection). |
| BE-2 | `app/api/routes.py` | Added `except HTTPException: raise` before the generic `except Exception` in `review_complaint`, `delete_complaints`, `update_complaint_status`, `delete_complaint`, and `submit_resolution_feedback`. | Re-ran all four missing-ticket cases → now return **404 `{"detail":"Ticket not found"}`** (was 500 with empty detail). |

Both fixes are minimal, preserve existing behavior for the success path, and were re-verified against a live server after a restart. No architecture, schema, or UI changes were made.

---

## Remaining Issues

**Not fixed (require product/owner decision or are out of safe-fix scope):**

- **SEC-1 (CRITICAL):** Enforce real JWT verification on all protected routes; stop trusting client-supplied `email`. *Auth redesign — needs approval.*
- **SEC-3 (HIGH):** Verify Google ID tokens server-side.
- **SEC-2 (HIGH):** Remove the hardcoded `JWT_SECRET_KEY` default; fail fast if unset.
- **SEC-4 (HIGH):** Untrack the committed `.db` files (they contain PII) and purge from history.
- **SEC-5 (HIGH):** Run `npm audit fix` and re-test PDF export / anything using lodash.
- **BE-3 / BE-4 / BE-5 / BE-6 / BE-7, DB-1, FE-1..6:** documented above; low-risk cleanups.

---

## Recommended Tests

1. **Auth enforcement (highest priority):** once JWT is enforced, add API tests asserting that admin/agent endpoints return **401/403 without a valid token** — today they return data with none.
2. Backend: `pytest` + FastAPI `TestClient` for the CRUD/404/422 paths tested manually here (lock in the BE-1/BE-2 fixes as regression tests).
3. Frontend: Vitest + React Testing Library for `AuthContext`, login/OTP flow, and form validation.
4. E2E: Playwright for login → submit complaint → view in profile → logout.
5. Accessibility: `@axe-core/playwright` on Landing, Login, OTPModal, Feedback, Dashboard.
6. Responsive: manual/Playwright device-emulation pass at the five breakpoints (none performed yet).

---

## Final Verdict

### WORKING WITH CRITICAL ISSUES

The frontend builds and the backend runs; the two confirmed functional defects in error handling (BE-1, BE-2) have been **fixed and re-verified**. However, the application must **not** be treated as production-ready: authorization is not actually enforced (SEC-1), privileged endpoints leak user PII to unauthenticated callers, several high-severity dependency and secret-handling issues remain, and no accessibility/responsive/automated-test coverage exists. Resolve the CRITICAL/HIGH security items and add auth enforcement tests before shipping.
