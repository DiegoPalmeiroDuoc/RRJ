"""Password storage: PBKDF2-HMAC SHA256, individual salt + constant-time verify."""
import base64
import hashlib
import hmac
import secrets

ITERATIONS = 390_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, target = encoded.split('$', 3)
        if algorithm != 'pbkdf2_sha256' or int(iterations) > 2_000_000:
            return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                     base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(digest, base64.b64decode(target))
    except (ValueError, AttributeError):
        return False
