# College Grievance System: Backend (Stages 1 and 2)

FastAPI + PostgreSQL.

* **Stage 1:** database schema and seed data (T3), Google login and sessions (T1), visibility and permission rules (T5).
* **Stage 2:** ticket API (T4), staff actions (T6), routing and deadlines (T7), attachments (T11).

Requires Python 3.10+.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # edit SECRET_KEY etc.
docker compose up -d                                    # PostgreSQL (or use your own)
alembic upgrade head                                    # create tables
python -m app.seed                                      # example data
uvicorn app.main:app --reload --port 8000
```

* API docs (development only): http://localhost:8000/docs
* Try login: `POST /api/grievance/auth/dev-login {"email": "ravi@college.edu"}` then `GET /api/grievance/me`
* Seeded logins (dev): `admin@`, `cell@`, `officer1@`, `warden@`, `caretaker_a@`, `ravi@`, `priya@` ... `@college.edu`
  (change `ALLOWED_EMAIL_DOMAIN` in `.env` to match the college).

## Tests

```bash
pytest -q          # uses an in-memory SQLite database; no PostgreSQL needed
```

All must pass before Stage 2 starts, and keep passing after every later stage.

## Front end (the chatbot's Vite app)

Proxy the API through the dev server so cookies work on one origin. In `vite.config.js`:

```js
server: { proxy: { '/api/grievance': 'http://localhost:8000' } }
```

Call the API with `credentials: 'include'`. For POST/PUT/PATCH/DELETE send header
`X-CSRF-Token` = the `csrf_token` returned by login or `GET /me`.

## Google sign-in setup

1. Workspace admin creates an OAuth client (type: Web) and sets the app to **Internal**.
2. Add the dev and production origins and set `GOOGLE_CLIENT_ID` in `.env`.
3. The front end gets a Google ID token (Google Identity Services) and posts it to `POST /api/grievance/auth/google {"credential": "..."}`.
4. The backend verifies it (signature, expiry, audience, verified email, college domain, Workspace `hd`).

Users must exist first (admin loads the student CSV and adds staff). `UNKNOWN_EMAIL_POLICY=student` would let
any college account in as a student instead.

## Production checklist

The app **refuses to start** in production unless: `DEV_LOGIN_ENABLED=false`, `SECRET_KEY` is 32+ random characters,
`COOKIE_SECURE=true`, `GOOGLE_CLIENT_ID` is set. Run uvicorn with `--proxy-headers` behind the reverse proxy.
The login rate limiter is in-memory per process.

## For the Stage 2 owner: what to import

| Need | Use |
|---|---|
| DB session | `from app.db import get_db` |
| Logged-in user | `Depends(get_current_user)` from `app.security.deps` |
| Role gate | `Depends(require_role(Role.ADMIN, ...))` (wrong role gives 404) |
| Open one ticket | `get_ticket_or_404(db, user, id)` or with `check=can_handle` / `can_escalate` |
| List tickets | `select(Ticket).where(ticket_visibility_filter(user))` |
| Timeline for a user | `visible_events(user, ticket, events)` |
| Statuses and legal moves | `from app.constants import Status, TRANSITIONS, can_transition` |
| Register routes | include your router in `app/main.py` inside the `api` router (CSRF is applied automatically) |

Shared definitions are in `docs/CONTRACT.md`. Schema changes: edit `app/models.py`, then
`alembic revision --autogenerate -m "describe change"` and commit the new file in `alembic/versions/`.

## Stage 2: tickets, staff actions, routing, attachments

New settings (all in `.env.example`): `MAX_TICKETS_PER_DAY`, `MAX_ATTACHMENTS_PER_USER_PER_TICKET`, `MAX_UPLOAD_MB`,
`UPLOAD_DIR`, `CLAMAV_ENABLED`, `AUTO_CLOSE_RESOLVED_DAYS`, `AUTO_CLOSE_NEEDS_INFO_DAYS`.

**Uploads:** set `UPLOAD_DIR` to a folder **outside** anything the web server serves, writable only by the app user,
and include it in the daily backup. Files are checked by content (JPG, PNG, PDF only), stored under random names,
never modified, and downloaded only through `GET /api/grievance/attachments/{id}` after a permission check.
If `CLAMAV_ENABLED=false` nothing is virus-scanned: tell the admin block (see known limitations).

**Try it** (after seeding; `ravi` reports, `caretaker_a` handles). Replace the ids using `GET /api/grievance/auth/dev-users`
and the `/docs` page, which lists every endpoint:

```bash
curl -c jar -H 'content-type: application/json' -d '{"email":"ravi@college.edu"}' localhost:8000/api/grievance/auth/dev-login
# use the csrf_token from the response in X-CSRF-Token for every POST
```

**Rules implemented here:** routing (exact -> category default -> "Other" -> error), inactive staff are skipped,
confidential tickets always go to the confidential category's officers, the deadline pauses in NEEDS_INFO and resumes
with the paused time added, one open ticket per student/category/unit, 10 new tickets per student per day,
a person can never handle or escalate a ticket they reported themselves.

**Not here (Stage 3):** the scheduler that escalates overdue tickets and auto-closes, notifications and email, the
keyword classifier, the admin endpoints. Their hooks are marked in `docs/CONTRACT.md`.

**Stage 3 owner, import these:** `app.services.tickets` (`escalate_ticket`, `auto_close`, `overdue_clause`),
`app.services.notify.notify`, `app.services.flags.detect_flags`, `app.services.routing`.
