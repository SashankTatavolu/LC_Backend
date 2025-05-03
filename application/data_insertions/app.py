import hashlib
import os
import base64

def hash_password(password):
    # Lower memory cost to avoid memory errors
    n = 2**14  # Reduced from 32768
    r = 8
    p = 1

    salt = os.urandom(16)
    key = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=64
    )
    salt_hex = base64.b16encode(salt).decode('utf-8').lower()
    key_hex = base64.b16encode(key).decode('utf-8').lower()
    
    hashed = f"scrypt:{n}:{r}:{p}${salt_hex}${key_hex}"
    return hashed

# Example usage
if __name__ == "__main__":
    password = input("Enter your password: ")
    hashed_password = hash_password(password)
    print("Hashed password:")
    print(hashed_password)
