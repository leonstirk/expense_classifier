# utils.py
import hashlib
import re
import os
import json
import pandas as pd
from config import IGNORED_TERMS, CLASSIFICATION_FILE


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

def load_classified_data(filepath=CLASSIFICATION_FILE):
    if not os.path.exists(filepath):
        return pd.DataFrame()

    with open(filepath, "r") as f:
        data = json.load(f)

    rows = []
    for uid, entry in data.items():
        row = {
            "UID": uid,
            "Date": entry.get("Date"),
            "Details": entry.get("Description"),
            "Amount": entry.get("Amount"),
            "Category": entry.get("Category"),
            "Source": entry.get("Source"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    # df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    return df.dropna(subset=["Date"])
