# fuzzy_utils.py

import re
import logging
import pandas as pd
from rapidfuzz import process, fuzz
from config import FUZZY_MATCH_THRESHOLD

def normalize_text(text):
    """Return a lowercase, punctuation-free version of the input text."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def group_similar_transactions(df, target_row, threshold=FUZZY_MATCH_THRESHOLD, limit=5):
    """
    Group transactions with similar 'Details' in a DataFrame using fuzzy matching.
    Returns unique rows matching on identical or fuzzy 'Details', including the target row.
    """

    # Normalize the target description
    target = normalize_text(target_row["Details"])

    # Get all unique descriptions and normalize them
    unique_details = df["Details"].unique()
    normalized_details = [normalize_text(detail) for detail in unique_details]

    # Use RapidFuzz to extract matches
    matches = process.extract(
        target,
        normalized_details,
        scorer=fuzz.token_sort_ratio,
        limit=limit,
        score_cutoff=threshold
    )
    fuzzy_matched_details = [unique_details[match[2]] for match in matches]

    # Collect all matching rows:
    matching_rows = pd.concat([
        df[df["Details"] == target_row["Details"]],
        df[df["Details"].isin(fuzzy_matched_details)]
    ])

    # Ensure the target row itself is included
    matching_rows = pd.concat([matching_rows, target_row.to_frame().T])

    # Remove full duplicates based on core transaction fields
    merged_rows = matching_rows.drop_duplicates(subset=["Date", "Details", "Amount", "Balance"])

    return merged_rows
