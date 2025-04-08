import os
import json
import pandas as pd
from matplotlib.figure import Figure
from config import CLASSIFICATION_FILE

CREDIT_CATEGORIES = {
    "TF Joint saving",
    "TF Bills",
    "TF Leon",
    "TF Kate"
}

def load_classified_data(filepath=CLASSIFICATION_FILE):
    if not os.path.exists(filepath):
        return pd.DataFrame()

    with open(filepath, "r") as f:
        data = json.load(f)

    records = [
        {
            "Date": entry.get("Date"),
            "Amount": float(entry["Amount"]),
            "Category": entry["Category"]
        }
        for entry in data.values()
        if "Date" in entry and "Amount" in entry and "Category" in entry
    ]

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["Date"])

def assign_custom_period(df, freq="M", start_date=None):
    if start_date is None:
        start_date = df["Date"].min()
    start_date = pd.to_datetime(start_date)

    if freq == "M":
        df["Period"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    elif freq == "W":
        df["Period"] = (((df["Date"] - start_date).dt.days // 7) * 7).apply(lambda x: start_date + pd.Timedelta(days=x))
    elif freq == "F":
        df["Period"] = (((df["Date"] - start_date).dt.days // 14) * 14).apply(lambda x: start_date + pd.Timedelta(days=x))
    else:
        raise ValueError("Invalid frequency. Use 'M', 'W', or 'F'.")

    return df

def create_spending_plot(df, freq="M", start_date=None):
    """
    Create a spending bar plot aggregated by custom-aligned periods.
    """
    df = assign_custom_period(df, freq, start_date)
    title = f"Total Spending Per {'Month' if freq == 'M' else 'Week' if freq == 'W' else 'Fortnight'}"
    width = 10 if freq == "M" else 5 if freq == "W" else 7

    grouped = df.groupby("Period")["Amount"].sum().reset_index()
    grouped["Period"] = pd.to_datetime(grouped["Period"])

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.bar(grouped["Period"], grouped["Amount"], width=width)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.grid(True, axis='y')

    return fig


def create_spending_vs_transfer_plot(df, freq="M", start_date=None):
    """
    Create a clustered bar plot showing spending vs income/transfers over time,
    with both categories shown as positive values for direct comparison.
    """
    df = assign_custom_period(df, freq, start_date)
    title = f"Spending vs Transfers/Income Per {'Month' if freq == 'M' else 'Week' if freq == 'W' else 'Fortnight'}"
    width = 10 if freq == "M" else 5 if freq == "W" else 7

    df["Type"] = df["Category"].apply(lambda x: "Credit" if x in CREDIT_CATEGORIES else "Spending")
    df["SignedAmount"] = df.apply(lambda row: row["Amount"] if row["Type"] == "Credit" else -row["Amount"], axis=1)

    grouped = df.groupby(["Period", "Type"])["SignedAmount"].sum().unstack(fill_value=0)

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot(111)
    periods = grouped.index
    offset = width / 3

    ax.bar(periods - pd.Timedelta(days=offset), grouped.get("Spending", 0), width=width / 2, label="Spending")
    ax.bar(periods + pd.Timedelta(days=offset), grouped.get("Credit", 0), width=width / 2, label="Credit")

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.legend()
    ax.grid(True, axis='y')

    return fig


def suggest_credit_categories(df, threshold=1000):
    """
    Suggest categories likely to be credit accounts based on significant positive transactions.
    """
    positive_agg = df[df["Amount"] > 0].groupby("Category")["Amount"].sum()
    frequent_positives = positive_agg[positive_agg > threshold].sort_values(ascending=False)
    return frequent_positives
