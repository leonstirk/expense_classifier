# utils.py
import hashlib
import re
from config import IGNORED_TERMS


def generate_transaction_id(row):
    key = f"{row['Date']}|{row['Details']}|{row['Amount']}|{row.get('Balance', '')}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def clean_description(text):
    # Lowercase
    text = text.lower()
    # Remove ignored terms as whole words
    pattern = r"\b(" + "|".join(re.escape(term) for term in IGNORED_TERMS) + r")\b"
    text = re.sub(pattern, "", text)
    # Remove extra whitespace
    return re.sub(r"\s+", " ", text).strip()

