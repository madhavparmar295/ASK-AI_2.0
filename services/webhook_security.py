import os

from google.auth.transport import requests
from google.oauth2 import id_token


PUBSUB_OIDC_AUDIENCE = os.getenv("PUBSUB_OIDC_AUDIENCE")
PUBSUB_OIDC_SERVICE_ACCOUNT = os.getenv("PUBSUB_OIDC_SERVICE_ACCOUNT")


def verify_pubsub_oidc_token(authorization: str | None) -> dict:
    """
    Verify the OIDC JWT sent by Google Pub/Sub.

    The token must:
    - be sent as: Authorization: Bearer <JWT>
    - have the expected audience
    - be issued by Google
    - have a verified email
    - come from the configured Pub/Sub push service account
    """

    if not authorization:
        raise ValueError("Missing Authorization header")

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid Authorization header")

    token = parts[1]

    if not PUBSUB_OIDC_AUDIENCE:
        raise RuntimeError(
            "PUBSUB_OIDC_AUDIENCE is not configured"
        )

    if not PUBSUB_OIDC_SERVICE_ACCOUNT:
        raise RuntimeError(
            "PUBSUB_OIDC_SERVICE_ACCOUNT is not configured"
        )

    # Verify Google's signed OIDC token and its audience.
    claims = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        audience=PUBSUB_OIDC_AUDIENCE,
    )

    # Verify token issuer.
    issuer = claims.get("iss")

    if issuer not in (
        "https://accounts.google.com",
        "accounts.google.com",
    ):
        raise ValueError("Invalid OIDC token issuer")

    # Verify that Google's email claim is verified.
    if claims.get("email_verified") is not True:
        raise ValueError("OIDC email is not verified")

    # Verify that the token was issued for the exact
    # Pub/Sub push service account configured in GCP.
    token_email = claims.get("email")

    if token_email != PUBSUB_OIDC_SERVICE_ACCOUNT:
        raise ValueError(
            "Unexpected Pub/Sub service account"
        )

    return claims