#!/usr/bin/env python3
"""Submit a new lead (public — no auth required)."""

import json
import mimetypes
import os
import sys
import uuid
import urllib.request
import urllib.error

BASE_URL = os.environ.get("ALMA_BASE_URL", "http://localhost:8000")


def build_multipart(fields: dict[str, str], file_path: str | None = None):
    """Build a multipart/form-data body using stdlib only."""
    boundary = uuid.uuid4().hex
    lines = []

    for key, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b"")
        lines.append(value.encode())

    if file_path:
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            file_data = f.read()
        lines.append(f"--{boundary}".encode())
        lines.append(
            f'Content-Disposition: form-data; name="resume"; filename="{filename}"'.encode()
        )
        lines.append(f"Content-Type: {content_type}".encode())
        lines.append(b"")
        lines.append(file_data)

    lines.append(f"--{boundary}--".encode())
    body = b"\r\n".join(lines)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def main():
    print("=== Submit a New Lead ===\n")

    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    email = input("Email: ").strip()

    if not all([first_name, last_name, email]):
        print("Error: all fields are required.")
        sys.exit(1)

    resume_path = input("Resume file path (leave blank to skip): ").strip() or None
    if resume_path and not os.path.isfile(resume_path):
        print(f"Error: file not found: {resume_path}")
        sys.exit(1)

    fields = {"first_name": first_name, "last_name": last_name, "email": email}
    body, content_type = build_multipart(fields, resume_path)

    req = urllib.request.Request(
        f"{BASE_URL}/api/leads",
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read()).get("detail", "Unknown error")
        print(f"\nSubmission failed ({e.code}): {detail}")
        sys.exit(1)

    print(f"\nLead submitted successfully!")
    print(f"  ID:    {data['id']}")
    print(f"  Name:  {data['first_name']} {data['last_name']}")
    print(f"  Email: {data['email']}")
    print(f"  State: {data['state']}")
    if data.get("resume_path"):
        print(f"  Resume: {data['resume_path']}")


if __name__ == "__main__":
    main()
