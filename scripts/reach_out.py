#!/usr/bin/env python3
"""Mark a lead as REACHED_OUT (requires login)."""

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


def fetch_leads(token: str) -> list[dict]:
    req = urllib.request.Request(
        f"{BASE_URL}/api/leads",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print("Error: token expired or invalid. Run `python scripts/login.py` again.")
        else:
            detail = json.loads(e.read()).get("detail", "Unknown error")
            print(f"Error ({e.code}): {detail}")
        sys.exit(1)


def main():
    token = load_token()
    leads = fetch_leads(token)

    pending = [l for l in leads if l["state"] == "PENDING"]
    if not pending:
        print("No pending leads to reach out to.")
        return

    print("Pending leads:\n")
    print(f"  {'#':<4} {'Name':<25} {'Email':<30}")
    print(f"  {'-'*60}")
    for i, lead in enumerate(pending, 1):
        name = f"{lead['first_name']} {lead['last_name']}"
        print(f"  {i:<4} {name:<25} {lead['email']:<30}")

    print()
    choice = input(f"Select a lead to mark as REACHED_OUT (1-{len(pending)}): ").strip()

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(pending):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        sys.exit(1)

    selected = pending[idx]
    lead_id = selected["id"]

    payload = json.dumps({"state": "REACHED_OUT"}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/leads/{lead_id}",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read()).get("detail", "Unknown error")
        print(f"\nFailed ({e.code}): {detail}")
        sys.exit(1)

    name = f"{data['first_name']} {data['last_name']}"
    print(f"\nDone! {name} marked as REACHED_OUT.")
    print(f"sent email to prospect: {data['email']}")
    print("sent email to attorney: attorney@example.com")


if __name__ == "__main__":
    main()
