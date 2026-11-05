"""Voter identification with a browser cookie (no login)."""
import secrets
import string

COOKIE_NAME = "voter_token"
COOKIE_MAX_AGE_SECONDS = 365 * 24 * 60 * 60
TOKEN_LENGTH = 32
_TOKEN_CHARS = string.ascii_letters + string.digits


def get_voter_token(cookies):
    """Return the voter token from the request cookies, or None when it is missing or malformed."""
    value = cookies.get(COOKIE_NAME)
    if value is None or len(value) != TOKEN_LENGTH:
        return None
    if not all(ch in _TOKEN_CHARS for ch in value):
        return None
    return value


def issue_voter_token():
    """Return a new random token of TOKEN_LENGTH letters and digits."""
    return "".join(secrets.choice(_TOKEN_CHARS) for _ in range(TOKEN_LENGTH))
