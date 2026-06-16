"""Small reusable input validators."""
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[0-9+\-\s()]{6,20}$")


def is_valid_email(value: str) -> bool:
    """True if value is a syntactically valid email address."""
    return bool(_EMAIL_RE.match((value or "").strip()))


def is_valid_phone(value: str) -> bool:
    """True if value looks like a phone number (digits, +, -, spaces, parens)."""
    return bool(_PHONE_RE.match((value or "").strip()))
