# utils.py
import hashlib

def generate_transaction_id(row):
    key = f"{row['Date']}|{row['Details']}|{row['Amount']}|{row.get('Balance', '')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()