#!/usr/bin/env python3
"""Interactive .env setup — generates password hash and writes .env file."""

import getpass
import os
import secrets
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.core.security import hash_password

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")


def main():
    print("=== Alma .env Setup ===\n")

    if os.path.exists(ENV_PATH):
        resp = input(".env already exists. Overwrite? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            return

    username = input("Internal username [admin]: ").strip() or "admin"
    password = getpass.getpass("Internal password: ")
    if not password:
        print("Error: password cannot be empty.")
        return
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: passwords do not match.")
        return

    jwt_secret = secrets.token_urlsafe(32)
    password_hash = hash_password(password)

    contents = f"""\
DATABASE_URL=sqlite+aiosqlite:///./alma.db
UPLOAD_DIR=uploads

JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

INTERNAL_USER_USERNAME={username}
INTERNAL_USER_PASSWORD_HASH='{password_hash}'
"""

    with open(ENV_PATH, "w") as f:
        f.write(contents)

    print(f"\n.env written to {os.path.abspath(ENV_PATH)}")
    print(f"  Username: {username}")
    print("  Password: (hidden)")
    print("\n** If the server is already running, you MUST restart it. **")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
