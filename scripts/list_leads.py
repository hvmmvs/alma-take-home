#!/usr/bin/env python3
"""List all leads (requires login)."""

import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = os.environ.get("ALMA_BASE_URL", "http://localhost:8000")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", ".token")


def load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        print("Error: not logged in. Run `python scripts/login.py` first.")
        sys.exit(1)
    with open(TOKEN_PATH) as f:
        return f.read().strip()


def main():
    token = load_token()

    req = urllib.request.Request(
        f"{BASE_URL}/api/leads",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            leads = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print("Error: token expired or invalid. Run `python scripts/login.py` again.")
        else:
            detail = json.loads(e.read()).get("detail", "Unknown error")
            print(f"Error ({e.code}): {detail}")
        sys.exit(1)

    if not leads:
        print("No leads found.")
        return

    print(f"{'#':<4} {'ID':<36}  {'Name':<25} {'Email':<30} {'State':<12}")
    print("-" * 110)
    for i, lead in enumerate(leads, 1):
        name = f"{lead['first_name']} {lead['last_name']}"
        print(f"{i:<4} {lead['id']:<36}  {name:<25} {lead['email']:<30} {lead['state']:<12}")

    print(f"\nTotal: {len(leads)} lead(s)")


if __name__ == "__main__":
    main()
