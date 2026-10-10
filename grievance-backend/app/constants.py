"""Shared definitions: roles, statuses and the legal status transitions.

These are part of the team contract. Later stages import them; do not
redefine them elsewhere.
"""


class Role:
    STUDENT = "student"
    STAFF = "staff"
    OFFICER = "officer"   # designated officer for confidential tickets
    ADMIN = "admin"
    ALL = (STUDENT, STAFF, OFFICER, ADMIN)


class Status:
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    NEEDS_INFO = "NEEDS_INFO"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

    ALL = (ASSIGNED, IN_PROGRESS, ESCALATED, NEEDS_INFO, RESOLVED, CLOSED, CANCELLED)
    # tickets the escalation job looks at
    CLOCK_RUNNING = (ASSIGNED, IN_PROGRESS)
    FINAL = (CLOSED, CANCELLED)


class UnitType:
    HOSTEL = "hostel"
    DEPARTMENT = "department"
    BUILDING = "building"
    MESS = "mess"
    CAMPUS = "campus"
    ALL = (HOSTEL, DEPARTMENT, BUILDING, MESS, CAMPUS)


# Legal status transitions (from the lifecycle diagram).
# ESCALATED -> NEEDS_INFO is added so an escalated handler can also ask the student.
TRANSITIONS = {
    Status.ASSIGNED: {Status.IN_PROGRESS, Status.ESCALATED, Status.NEEDS_INFO,
                      Status.RESOLVED, Status.CANCELLED},
    Status.IN_PROGRESS: {Status.ESCALATED, Status.NEEDS_INFO, Status.RESOLVED,
                         Status.CANCELLED},
    Status.ESCALATED: {Status.IN_PROGRESS, Status.NEEDS_INFO, Status.RESOLVED,
                       Status.CANCELLED},
    Status.NEEDS_INFO: {Status.IN_PROGRESS, Status.CLOSED, Status.CANCELLED},
    Status.RESOLVED: {Status.CLOSED, Status.ASSIGNED},   # ASSIGNED = student says "not fixed"
    Status.CLOSED: set(),
    Status.CANCELLED: set(),
}


def can_transition(current: str, new: str) -> bool:
    return new in TRANSITIONS.get(current, set())
