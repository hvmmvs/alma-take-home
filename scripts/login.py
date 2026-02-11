#!/usr/bin/env python3
"""Log in and save the JWT token for use by other scripts."""

import getpass
import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = os.environ.get("ALMA_BASE_URL", "http://localhost:8000")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", ".token")


def main():
    print("=== Alma Login ===\n")

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    payload = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        print(f"Login failed ({e.code}): {body.get('detail', 'Unknown error')}")
        sys.exit(1)

    token = data["access_token"]
    with open(TOKEN_PATH, "w") as f:
        f.write(token)

    print("Login successful! Token saved.")
    print("You can now use the other scripts (list_leads, reach_out, etc.)")


if __name__ == "__main__":
    main()
