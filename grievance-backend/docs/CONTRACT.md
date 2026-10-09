# Shared contract (all stages build against this)

Change this file first, tell everyone, then change code. **One person approves changes.**

## Roles
`student` · `staff` (handlers, heads) · `officer` (confidential tickets) · `admin`.
"Head" is not a role: a user is a head if they hold level 1 or 2 in any routing row (`GET /me` returns `is_head`).

## Statuses and legal transitions (`app/constants.py`)
```
ASSIGNED    -> IN_PROGRESS | ESCALATED | NEEDS_INFO | RESOLVED | CANCELLED
IN_PROGRESS -> ESCALATED | NEEDS_INFO | RESOLVED | CANCELLED
ESCALATED   -> ESCALATED (next level) | IN_PROGRESS | NEEDS_INFO | RESOLVED | CANCELLED
NEEDS_INFO  -> IN_PROGRESS (student replied) | CLOSED (no reply 7 days) | CANCELLED
RESOLVED    -> CLOSED (student confirms / 3 days) | ASSIGNED (student: "not fixed")
CLOSED, CANCELLED: final
```
The deadline clock runs in ASSIGNED, IN_PROGRESS and ESCALATED (`Status.CLOCK_RUNNING`) and is paused in NEEDS_INFO.
The escalation job (Stage 3) moves tickets in those states past `due_at` to the next level.

## Tables (`app/models.py`)
users, categories, units, routing, tickets, attachments, events, feedback, notifications, audit_log.
Ticket fields that matter across stages: `status`, `assignee_id`, `route_id`, `escalation_level`, `due_at`, `paused_at`, `confidential`, `urgent`.

## Visibility (`app/permissions.py`) - the only place that decides access
* View normal ticket: reporter, assignee, routing-chain member, admin.
* View confidential ticket: reporter, officers who are assignee or in the chain. Nobody else (admin sees counts only).
* Handle (start, request info, resolve): assignee or chain member; officer only if confidential; never the reporter.
* Escalate / reassign: head (level 1-2) or admin for normal tickets; officer in the chain for confidential.
* Unauthorised access returns **404**. Lists use `ticket_visibility_filter(user)`.
* Errors: **404** cannot see it · **403** can see it but not allowed to do this · **409** wrong state or duplicate · **422** invalid input · **429** daily limit or login rate limit · **413/415** file too big / wrong type · **503** routing not configured.
* Reporters see only events with `visible_to_student = true`.

## Rules for every endpoint
* Under `/api/grievance`, JSON, cookie session. State-changing requests send `X-CSRF-Token` (value of the `grievance_csrf` cookie, also returned by login and `/me`).
* The server sets `status`, `assignee_id`, `confidential`, `urgent`. Ignore client-sent values.
* Depend on `get_current_user` or `require_role(...)`. Never trust the front end for permissions.

## API list
| Stage | Method + path | Who |
|---|---|---|
| 1 | `POST /auth/google` `{credential}` | public |
| 1 | `POST /auth/dev-login` `{email}`, `GET /auth/dev-users` (dev only) | public |
| 1 | `POST /auth/logout`, `GET /me`, `GET /health` | any / public |
| 2 | `POST /issues`, `GET /issues/mine?status=&limit=&offset=`, `GET /issues/{id}` | any signed-in user / viewer |
| 2 | `POST /issues/{id}/attachments` (multipart, field `file`), `GET /attachments/{id}` | reporter, handlers |
| 2 | `POST /issues/{id}/reply` `{text}`, `/cancel` `{reason?}`, `/confirm`, `/reopen` `{reason}`, `/feedback` `{rating, comment?}` | reporter |
| 2 | `GET /staff/issues?scope=mine\|team&status=&overdue=`, `GET /staff/overdue` | staff, officer (others get 404) |
| 2 | `POST /issues/{id}/start`, `/request-info` `{text}`, `/resolve` `{note}` | `can_handle` |
| 2 | `POST /issues/{id}/escalate` `{reason}`, `/reassign` `{assignee_id, reason}` | `can_escalate` |
| 3 | `POST /classify`, `GET /notifications`, `POST /notifications/{id}/read` | student / any |
| 3 | `/admin/categories`, `/admin/units`, `/admin/routing` (+ `POST /admin/routing/import`), `/admin/users` (+ import) | admin |
| 3 | `GET /admin/stats`, `/admin/issues`, `/admin/health` | admin |

Example: `GET /me`
```json
{"id": "uuid", "name": "Ravi Kumar", "email": "ravi@college.edu", "role": "student",
 "department": "CSE", "hostel": "Hostel A", "room": "A-101", "is_head": false,
 "csrf_token": "..."}
```
Example: `POST /issues` (Stage 2). Files are added **after** the ticket exists, one `POST /issues/{id}/attachments` per file.
```json
{"description": "AC not working in my room", "category_id": "uuid", "unit_id": "uuid",
 "location_text": "A-101", "confidential": false}
```
`GET /issues/{id}` returns the ticket, its attachments, the timeline (students see only student-visible events) and
`actions`: the list of things the signed-in user may do now (`reply, cancel, upload, confirm, reopen, feedback, start,
request_info, resolve, escalate, reassign`). **The UI draws its buttons from `actions`; it never decides on its own.**

## Hooks for Stage 3
| Where | What Stage 3 does |
|---|---|
| `app/services/flags.py` `detect_flags(text)` | Replace with the keyword classifier. Return `{"confidential": bool, "urgent": bool}` |
| `app/services/notify.py` `notify(db, kind, ticket, actor=, previous_assignee_id=)` | Create notifications, send email; recipients per kind are listed in that file |
| `services/tickets.escalate_ticket(db, ticket, None, reason)` | The scheduler calls this for overdue tickets (conditional on current level) |
| `services/tickets.overdue_clause(now)` | WHERE-clause for overdue tickets |
| `services/tickets.auto_close(db)` | Call from the scheduler every run |
