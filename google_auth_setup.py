"""
One-time Google OAuth token generator.
Run this ONCE per account to produce the token JSON for Horizon.

USAGE (in Termux or any Python environment):
  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

  For professional account:
    python3 google_auth_setup.py professional

  For personal account:
    python3 google_auth_setup.py personal

Then paste the OUTPUT into Horizon as:
  GOOGLE_PROFESSIONAL_TOKEN_JSON  or  GOOGLE_PERSONAL_TOKEN_JSON

BEFORE RUNNING:
  1. Create a file called 'credentials_professional.json' with the contents
     of your GOOGLE_PROFESSIONAL_CREDENTIALS_JSON env var value
  2. Create a file called 'credentials_personal.json' with the contents
     of your GOOGLE_PERSONAL_CREDENTIALS_JSON env var value
"""

import sys
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

ACCOUNT_EMAILS = {
    "professional": "adarsh.jaiswal.2112.aj@gmail.com",
    "personal": "aj.jin.japan.2006@gmail.com",
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("professional", "personal"):
        print("Usage: python3 google_auth_setup.py professional|personal")
        sys.exit(1)

    account = sys.argv[1]
    creds_file = f"credentials_{account}.json"

    if not os.path.exists(creds_file):
        print(f"\nERROR: '{creds_file}' not found.")
        print(f"Create it by copying the value of GOOGLE_{account.upper()}_CREDENTIALS_JSON")
        print("from Horizon into a file with that name in this same directory.\n")
        sys.exit(1)

    print(f"\n=== OAuth setup for '{account}' ({ACCOUNT_EMAILS[account]}) ===\n")
    print("A URL will appear below. Open it in your browser,")
    print(f"sign in as {ACCOUNT_EMAILS[account]}, and authorize.")
    print("Then paste the authorization code back here.\n")

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)

    # console mode: prints URL, waits for code paste — works headless/in Termux
    creds = flow.run_console()

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }

    token_json = json.dumps(token_data)

    print("\n" + "=" * 60)
    print(f"SUCCESS — paste this into Horizon as:")
    print(f"  GOOGLE_{account.upper()}_TOKEN_JSON")
    print("=" * 60)
    print(token_json)
    print("=" * 60 + "\n")

    # Also save locally as a backup
    out_file = f"token_{account}.json"
    with open(out_file, "w") as f:
        f.write(token_json)
    print(f"Also saved locally as: {out_file}")

if __name__ == "__main__":
    main()
