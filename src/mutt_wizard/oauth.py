from __future__ import annotations

from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://mail.google.com/"]


def ensure_token(
    email: str,
    client_secret_path: Path,
    token_path: Path,
    open_browser: bool,
) -> Credentials:
    creds: Optional[Credentials] = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path), SCOPES
        )
        try:
            creds = flow.run_local_server(open_browser=open_browser, port=0)
        except Exception:
            creds = flow.run_console()

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def access_token(
    email: str,
    client_secret_path: Path,
    token_path: Path,
) -> str:
    creds = ensure_token(
        email=email,
        client_secret_path=client_secret_path,
        token_path=token_path,
        open_browser=False,
    )
    return creds.token
