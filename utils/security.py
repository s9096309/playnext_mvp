import bcrypt
import re

def hash_password(password: str) -> str:
    """Hashes the given password using bcrypt."""
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if the plain password matches the hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False


def sanitize_html(text: str) -> str:
    """
    Removes HTML tags and potentially dangerous scripts from user input.
    """
    if not text:
        return text
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

