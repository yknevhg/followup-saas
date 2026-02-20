# crypto.py
import os
from cryptography.fernet import Fernet

fernet = Fernet(os.environ["SMTP_ENCRYPTION_KEY"].encode())

def encrypt(text: str) -> bytes:
    return fernet.encrypt(text.encode())

def decrypt(token: bytes) -> str:
    return fernet.decrypt(token).decode()