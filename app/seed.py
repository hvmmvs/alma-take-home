"""Generate a bcrypt password hash for the internal user.

Usage: python -m app.seed <password>
"""

import sys

from app.core.security import hash_password


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.seed <password>")
        sys.exit(1)
    password = sys.argv[1]
    hashed = hash_password(password)
    print(f"INTERNAL_USER_PASSWORD_HASH={hashed}")


if __name__ == "__main__":
    main()
