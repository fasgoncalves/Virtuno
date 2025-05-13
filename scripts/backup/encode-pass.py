import bcrypt

password = 'admin'  # or Any other password
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(hashed)
