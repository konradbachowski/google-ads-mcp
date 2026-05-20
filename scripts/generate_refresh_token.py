"""Generate and store Google Ads OAuth refresh token.

This script runs the installed-app OAuth flow and stores the resulting refresh
token into the project's .env file as GOOGLE_ADS_REFRESH_TOKEN.

It avoids printing the full token to stdout.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPE = "https://www.googleapis.com/auth/adwords"


def _mask(token: str) -> str:
    if len(token) <= 12:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def _upsert_env_var(env_text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    line = f"{key}={value}"
    if pattern.search(env_text):
        return pattern.sub(line, env_text)
    if env_text and not env_text.endswith("\n"):
        env_text += "\n"
    return env_text + line + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-file",
        default=str(Path(__file__).resolve().parents[1] / ".env"),
        help="Path to .env file to update",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the browser (prints URL in terminal)",
    )
    args = parser.parse_args()

    load_dotenv(args.env_file)

    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit(
            "Missing GOOGLE_ADS_CLIENT_ID or GOOGLE_ADS_CLIENT_SECRET in .env"
        )

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=[SCOPE])

    # run_local_server will print a URL if it can't open a browser.
    creds = flow.run_local_server(
        port=0,
        open_browser=not args.no_browser,
        authorization_prompt_message=(
            "Please visit this URL to authorize this application: {url}"
        ),
        success_message="Authorization complete. You may close this tab.",
    )

    refresh_token = getattr(creds, "refresh_token", None)
    if not refresh_token:
        raise SystemExit(
            "OAuth completed but refresh_token is missing. "
            "Try revoking access and re-running the script."
        )

    env_path = Path(args.env_file)
    existing = env_path.read_text() if env_path.exists() else ""
    updated = _upsert_env_var(existing, "GOOGLE_ADS_REFRESH_TOKEN", refresh_token)
    env_path.write_text(updated)

    print("OK: Stored GOOGLE_ADS_REFRESH_TOKEN in .env")
    print(f"Token (masked): {_mask(refresh_token)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
