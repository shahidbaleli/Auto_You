"""
ONE-TIME SETUP SCRIPT — Get YouTube OAuth refresh token.
Run this ONCE on your local computer. It opens a browser to sign in.
Total download: ~5 MB of Python packages.
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    print("=" * 55)
    print("YouTube OAuth Token Setup")
    print("=" * 55)
    print("\nEnter your Google Cloud Client ID:")
    client_id = input().strip()
    print("\nEnter your Google Cloud Client Secret:")
    client_secret = input().strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    print("\nOpening browser for Google sign-in...")
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 55)
    print("SUCCESS! Add these 3 values to GitHub Secrets:")
    print("=" * 55)
    print(f"\nYT_REFRESH_TOKEN: {creds.refresh_token}")
    print(f"\nYT_CLIENT_ID: {client_id}")
    print(f"\nYT_CLIENT_SECRET: {client_secret}")
    print("\n" + "=" * 55)
    print("These tokens NEVER expire (unless manually revoked).")
    print("=" * 55)


if __name__ == "__main__":
    main()
