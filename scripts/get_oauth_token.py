#!/usr/bin/env python3
"""
One-time helper: authenticate with your Google account and print a refresh token.

Run this locally once to get the three values you need for GitHub secrets:
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN

Prerequisites:
    1. Go to https://console.cloud.google.com
    2. Create a project (or reuse one) → enable "Google Drive API"
    3. Go to Credentials → Create Credentials → OAuth client ID
       - Application type: "Desktop app"
       - Download the JSON file and save it as  scripts/client_secret.json
    4. Go to OAuth consent screen → add your Google email as a test user

Usage:
    cd scripts
    pip install -r requirements.txt
    python get_oauth_token.py
"""

import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing dependency.  Run:  pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CLIENT_SECRET_FILE = Path(__file__).parent / "client_secret.json"


def main():
    if not CLIENT_SECRET_FILE.exists():
        print(f"Error: {CLIENT_SECRET_FILE} not found.")
        print("Download it from Google Cloud Console → Credentials → OAuth client ID → Download JSON")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE), scopes=SCOPES
    )
    creds = flow.run_local_server(port=8090)

    client_info = json.loads(CLIENT_SECRET_FILE.read_text())
    client_data = client_info.get("installed") or client_info.get("web")

    print("\n" + "=" * 60)
    print("Add these three values as GitHub repository secrets:")
    print("  Settings → Secrets and variables → Actions → New secret")
    print("=" * 60)
    print(f"\nGOOGLE_CLIENT_ID:\n  {client_data['client_id']}")
    print(f"\nGOOGLE_CLIENT_SECRET:\n  {client_data['client_secret']}")
    print(f"\nGOOGLE_REFRESH_TOKEN:\n  {creds.refresh_token}")
    print(f"\nAlso add your Drive folder ID:")
    print(f"DRIVE_ROOT_FOLDER_ID:\n  (the ID from the folder URL — after /folders/)")
    print("=" * 60)


if __name__ == "__main__":
    main()
