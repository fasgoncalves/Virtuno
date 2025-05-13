import bcrypt

password = 'pass-to-encrypt'  # or Any other password
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(hashed)
