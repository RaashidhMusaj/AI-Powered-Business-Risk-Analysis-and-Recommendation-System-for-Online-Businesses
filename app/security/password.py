import bcrypt


def hash_password(password: str) -> str:
    """
    Hashes password using bcrypt directly, avoiding passlib compatibility issues with bcrypt 4+.
    Safely truncates inputs to 72 bytes as required by bcrypt specification.
    """
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies plain text password against stored bcrypt hash.
    """
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False
