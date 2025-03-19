import bcrypt

password = "your_test_password"  # Replace with your test password

salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

print(hashed_password.decode('utf-8'))