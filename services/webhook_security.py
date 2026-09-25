"""
Security helpers for Google Pub/Sub push webhooks.

Pub/Sub push requests carry an OIDC bearer token in the Authorization
header. We verify that token before processing the notification.
"""

import os

from fastapi import HTTPException, Request
from google.auth.transport import requests
from google.oauth2 import id_token


def verify_pubsub_oidc_token(request: Request) -> None:
    """
    Verify the Google-issued OIDC token attached to a Pub/Sub push.

    The expected audience is configured through
    GMAIL_PUBSUB_AUDIENCE.
    """

    authorization = request.headers.get("authorization", "")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing Pub/Sub OIDC bearer token.",
        )

    token = authorization.split(" ", 1)[1].strip()

    audience = os.getenv("GMAIL_PUBSUB_AUDIENCE")

    if not audience:
        raise HTTPException(
            status_code=500,
            detail="GMAIL_PUBSUB_AUDIENCE is not configured.",
        )

    try:
        claims = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=audience,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid Pub/Sub OIDC token.",
        ) from exc

    issuer = claims.get("iss")

    if issuer not in {
        "https://accounts.google.com",
        "accounts.google.com",
    }:
        raise HTTPException(
            status_code=401,
            detail="Invalid OIDC token issuer.",
        )