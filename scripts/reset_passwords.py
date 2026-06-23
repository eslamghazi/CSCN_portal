"""One-off utility: reset EVERY user account's password to a strong random value
and write the new credentials to a text file.

Run:  python scripts/reset_passwords.py

- Generates a fresh random password per user (secrets.token_urlsafe).
- Updates the password hash in the database (bcrypt, rounds=12).
- Writes username / full name / role / new password to C:\\CSCN\\credentials.txt
  (UTF-8, with a clear "keep secret / delete after distributing" header).

This does NOT touch the seeding logic; new installs are hardened separately in
main.py / .env.
"""
import sys
from pathlib import Path

# Make the project root importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import secrets

from loguru import logger

from config.settings import DATA_DIR
from database.base import Base
from database.engine import engine
import domain.entities  # noqa: F401  -- registers all models on Base.metadata
from domain.entities.user import User
from database.session import db_session as scoped_db_session
from infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from application.services.auth_service import AuthService


CREDENTIALS_FILE = DATA_DIR / "credentials.txt"
PASSWORD_NBYTES = 12  # secrets.token_urlsafe(12) -> ~16 char URL-safe password


def reset_all_passwords() -> list:
    """Reset every user's password to a random value. Returns a list of
    (username, full_name, role, new_password) tuples."""
    Base.metadata.create_all(engine)
    db = scoped_db_session()
    auth = AuthService(UserRepositoryImpl(db))

    users = db.query(User).order_by(User.id).all()
    if not users:
        logger.warning("No users found in the database; nothing to reset.")
        return []

    results = []
    for user in users:
        new_password = secrets.token_urlsafe(PASSWORD_NBYTES)
        user.password_hash = auth.hash_password(new_password)
        role = user.role.name if user.role else "-"
        results.append((user.username, user.full_name or "-", role, new_password))
    db.commit()
    return results


def write_credentials_file(results: list) -> Path:
    lines = [
        "=" * 64,
        "  CSCN_portal — بيانات الدخول (تم إعادة تعيينها)",
        "  ACCOUNT CREDENTIALS — RESET TO RANDOM PASSWORDS",
        "=" * 64,
        "",
        "  هام: هذا الملف يحتوي على كلمات مرور سرية.",
        "  وزّع كل حساب على صاحبه ثم احذف هذا الملف.",
        "  IMPORTANT: keep secret. Distribute, then DELETE this file.",
        "",
        "-" * 64,
        "",
    ]
    for username, full_name, role, password in results:
        lines.append(f"  المستخدم / Username : {username}")
        lines.append(f"  الاسم    / Name     : {full_name}")
        lines.append(f"  الصلاحية / Role     : {role}")
        lines.append(f"  كلمة المرور / Pass  : {password}")
        lines.append("  " + "-" * 60)
    lines.append("")

    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text("\n".join(lines), encoding="utf-8")
    return CREDENTIALS_FILE


def main():
    results = reset_all_passwords()
    if not results:
        print("No users to reset.")
        return
    path = write_credentials_file(results)
    print(f"Reset {len(results)} account(s). Credentials written to: {path}\n")
    for username, _full, role, password in results:
        print(f"  {username:<14} [{role:<10}]  {password}")


if __name__ == "__main__":
    main()
