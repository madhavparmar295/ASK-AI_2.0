"""Hook for the classifier (Stage 3, task T10).

Stage 2 calls detect_flags() when a ticket is created. Stage 3 replaces the body
with the keyword rules. The system may RAISE confidential/urgent, never lower it.
"""


def detect_flags(text: str) -> dict:
    return {"confidential": False, "urgent": False}
