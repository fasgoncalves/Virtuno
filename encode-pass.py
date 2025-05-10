import bcrypt

password = 'triAmd-25'  # or Any other password
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(hashed)
