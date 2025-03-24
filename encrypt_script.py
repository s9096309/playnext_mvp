import secrets
import base64

secret_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
print(f"SECRET_KEY: {secret_key}")