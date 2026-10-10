# College Grievance System: Backend (Stage 1: Foundation)

FastAPI + PostgreSQL. Stage 1 delivers: database schema and seed data (T3), Google login and sessions (T1),
visibility and permission rules (T5). No ticket endpoints yet; those are Stage 2.

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
