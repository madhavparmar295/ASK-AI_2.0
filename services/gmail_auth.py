# services/gmail_auth.py

import json
import os
import re
import secrets

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


# Define the minimum required permission scope to read emails
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

# Read your environment configurations
CLIENT_SECRETS_FILE = os.getenv(
    "GMAIL_CLIENT_SECRETS_FILE",
    "client_secret.json",
)

TOKEN_STORE_PATH = os.getenv(
    "GMAIL_TOKEN_STORE",
    "tokens/{user_id}.json",
)


def _safe_user_id(user_id: str) -> str:
    """
    Sanitize user_id before using it in a filesystem path.
    Prevents path traversal through tokens/{user_id}.json.
    """
    return re.sub(r"[^a-zA-Z0-9._@-]", "_", user_id)


def build_auth_url(user_id: str, redirect_uri: str):
    """
    Sub-Step A: Generate the Google Consent Screen URL.

    Returns:
        auth_url, state

    The random state is used to protect the OAuth flow against CSRF.
    """
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    flow.autogenerate_code_verifier = False

    # Generate a random OAuth state instead of using user_id.
    state = secrets.token_urlsafe(32)

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
    )

    return auth_url, state


def exchange_code_for_tokens(
    code: str,
    redirect_uri: str,
    user_id: str,
) -> Credentials:
    """
    Sub-Step B: Exchange the temporary one-time auth code
    for long-lived tokens.
    """
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    flow.autogenerate_code_verifier = False

    flow.fetch_token(code=code)

    creds = flow.credentials

    _persist_credentials(user_id, creds)

    return creds


def get_valid_credentials(user_id: str) -> Credentials:
    """
    Sub-Step C: Retrieve working credentials for background processing.

    Automatically refreshes an expired access token using
    the stored refresh token.
    """
    path = TOKEN_STORE_PATH.format(
        user_id=_safe_user_id(user_id)
    )

    if not os.path.exists(path):
        raise ValueError(
            f"No stored credentials for user {user_id}; "
            "run OAuth flow first."
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    creds = Credentials.from_authorized_user_info(
        data,
        SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _persist_credentials(user_id, creds)

    return creds


def _persist_credentials(
    user_id: str,
    creds: Credentials,
) -> None:
    """
    Helper Function: Saves the tokens to the tokens folder.
    """
    path = TOKEN_STORE_PATH.format(
        user_id=_safe_user_id(user_id)
    )

    directory = os.path.dirname(path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())