"""Hook for notifications (Stage 3, task T9).

Stage 2 calls notify() after every important change. Stage 3 fills in the body:
create in-app notifications, send emails, and apply the content-free rule for
confidential tickets.

kind -> who should be told (decided in Stage 3):
  created        reporter ("received"), assignee ("assigned")
  reassigned     new assignee
  info_requested reporter
  replied        assignee
  escalated      new assignee, previous assignee, reporter
  resolved       reporter (confirm or reopen)
  closed         reporter (feedback link)
  cancelled      assignee
  reopened       new assignee
"""


def notify(db, kind: str, ticket, *, actor=None, previous_assignee_id=None) -> None:
    return None
