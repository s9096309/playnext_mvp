import bcrypt

def hash_password(password: str) -> str:
    """Hashes the given password using bcrypt."""
    # Encode the password as bytes
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # Decode the hashed bytes back to a string for storage
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if the plain password matches the hashed password."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False  # Handle cases where the hash is invalid



print(verify_password("test1234", "$2b$12$m.KRJ6ykTIK4PsEzbigza.2hD/N6ullWHn7u.FsYYqAb/oEMU3avO"))

