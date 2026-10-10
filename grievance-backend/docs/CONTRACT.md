# Shared contract (all stages build against this)

Change this file first, tell everyone, then change code. **One person approves changes.**

## Roles
`student` · `staff` (handlers, heads) · `officer` (confidential tickets) · `admin`.
"Head" is not a role: a user is a head if they hold level 1 or 2 in any routing row (`GET /me` returns `is_head`).

## Statuses and legal transitions (`app/constants.py`)
```
ASSIGNED    -> IN_PROGRESS | ESCALATED | NEEDS_INFO | RESOLVED | CANCELLED
IN_PROGRESS -> ESCALATED | NEEDS_INFO | RESOLVED | CANCELLED
ESCALATED   -> IN_PROGRESS | NEEDS_INFO | RESOLVED | CANCELLED
NEEDS_INFO  -> IN_PROGRESS (student replied) | CLOSED (no reply 7 days) | CANCELLED
RESOLVED    -> CLOSED (student confirms / 3 days) | ASSIGNED (student: "not fixed")
CLOSED, CANCELLED: final
```
Only the escalation job moves ASSIGNED / IN_PROGRESS tickets past `due_at` to ESCALATED.

## Tables (`app/models.py`)
users, categories, units, routing, tickets, attachments, events, feedback, notifications, audit_log.
Ticket fields that matter across stages: `status`, `assignee_id`, `route_id`, `escalation_level`, `due_at`, `paused_at`, `confidential`, `urgent`.

## Visibility (`app/permissions.py`) - the only place that decides access
* View normal ticket: reporter, assignee, routing-chain member, admin.
* View confidential ticket: reporter, officers who are assignee or in the chain. Nobody else (admin sees counts only).
* Handle (start, request info, resolve): assignee or chain member; officer only if confidential; never the reporter.
* Escalate / reassign: head (level 1-2) or admin for normal tickets; officer in the chain for confidential.
* Unauthorised access returns **404**. Lists use `ticket_visibility_filter(user)`.
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
| 2 | `POST /issues`, `GET /issues/mine`, `GET /issues/{id}` | student / viewer |
| 2 | `POST /issues/{id}/attachments`, `GET /attachments/{id}` | reporter, handlers |
| 2 | `POST /issues/{id}/reply`, `/cancel`, `/confirm`, `/reopen`, `/feedback` | reporter |
| 2 | `GET /staff/issues`, `GET /staff/overdue` | staff, officer |
| 2 | `POST /issues/{id}/start`, `/request-info`, `/resolve` | `can_handle` |
| 2 | `POST /issues/{id}/escalate`, `/reassign` | `can_escalate` |
| 3 | `POST /classify`, `GET /notifications`, `POST /notifications/{id}/read` | student / any |
| 3 | `/admin/categories`, `/admin/units`, `/admin/routing` (+ `POST /admin/routing/import`), `/admin/users` (+ import) | admin |
| 3 | `GET /admin/stats`, `/admin/issues`, `/admin/health` | admin |

Example: `GET /me`
```json
{"id": "uuid", "name": "Ravi Kumar", "email": "ravi@college.edu", "role": "student",
 "department": "CSE", "hostel": "Hostel A", "room": "A-101", "is_head": false,
 "csrf_token": "..."}
```
Example: `POST /issues` (Stage 2)
```json
{"description": "AC not working in my room", "category_id": "uuid", "unit_id": "uuid",
 "location_text": "A-101", "confidential": false, "attachment_ids": []}
```
