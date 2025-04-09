import os
import json
import pandas as pd
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from config import CLASSIFICATION_FILE

CREDIT_CATEGORIES = {
    "TF Revolving",
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

def assign_custom_period(df, freq=7, start_date=None):
    """
    Assigns custom periods starting from a given base date, using a fixed-day cycle (e.g., 7, 14, 30).
    """
    if start_date is None:
        start_date = df["Date"].min()
    start_date = pd.to_datetime(start_date)

    if not isinstance(freq, int) or freq <= 0:
        raise ValueError("Frequency must be a positive integer representing number of days.")

    df["Period"] = (((df["Date"] - start_date).dt.days // freq) * freq).apply(
        lambda x: start_date + pd.Timedelta(days=x)
    )

    return df

def create_spending_vs_transfer_plot(df, freq=7, start_date=None, show_credit=True):
    """
    Create a clustered bar plot showing spending vs income/transfers over time,
    with both categories shown as positive values for direct comparison.
    """
    df = assign_custom_period(df, freq, start_date)
    title = f"Spending vs Transfers/Income Per {'Month' if freq == 30 else 'Week' if freq == 7 else 'Fortnight'}"
    width = 10 if freq == 30 else 5 if freq == 7 else 7

    df["Type"] = df["Category"].apply(lambda x: "Credit" if x in CREDIT_CATEGORIES else "Spending")
    df["SignedAmount"] = df.apply(lambda row: row["Amount"] if row["Type"] == "Credit" else -row["Amount"], axis=1)

    grouped = df.groupby(["Period", "Type"])["SignedAmount"].sum().unstack(fill_value=0)

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot(111)
    periods = grouped.index
    offset = width / 3

    ax.bar(periods - pd.Timedelta(days=offset), grouped.get("Spending", 0), width=width / 2, label="Spending")
    if show_credit:
        ax.bar(
            periods + pd.Timedelta(days=offset),
            grouped.get("Credit", 0),
            width=width / 2,
            label="Credit"
        )

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.legend()
    ax.grid(True)

     # Custom tick alignment based on start_date and rolling window
    base = pd.to_datetime(start_date or df["Date"].min())
    interval = freq

    # locator = mdates.DayLocator(interval=interval)
    # locator.set_params(bymonthday=None)  # reset month day anchors
    # locator.set_params(base=interval)    # enforce regular spacing
    # ax.xaxis.set_major_locator(locator)

    locator = mdates.DayLocator(interval=interval)
    ax.xaxis.set_major_locator(locator)
    ax.set_xlim(left=base)
    # Manually set tick locations if needed:
    ticks = pd.date_range(start=base, end=df["Date"].max(), freq=f"{interval}D")
    ax.set_xticks(ticks)


    # ax.set_xlim(left=base)
    # ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    fig.autofmt_xdate()

    return fig


def create_rolling_average_plot(df, window=7, start_date=None):
    """
    Plot a daily spending chart with a rolling average line.
    """
    df = df.copy()
    df = df.sort_values("Date")

    # Only include spending (exclude credits)
    df["Type"] = df["Category"].apply(lambda x: "Credit" if x in CREDIT_CATEGORIES else "Spending")
    spending = df[df["Type"] == "Spending"]

    # Group by date
    daily_totals = spending.groupby("Date")["Amount"].sum().reset_index()
    daily_totals["Rolling"] = daily_totals["Amount"].rolling(window=window).mean()

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(daily_totals["Date"], -daily_totals["Amount"], label="Daily Spend", alpha=0.4)
    ax.plot(daily_totals["Date"], -daily_totals["Rolling"], label=f"{window}-Day Avg", linewidth=2)

    ax.set_title(f"Daily Spending with {window}-Day Rolling Average")
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount")
    ax.grid(True)
    ax.legend()

    # Custom tick alignment based on start_date and rolling window
    base = pd.to_datetime(start_date or daily_totals["Date"].min())
    interval = window

    # locator = mdates.DayLocator(interval=interval)
    # locator.set_params(bymonthday=None)  # reset month day anchors
    # locator.set_params(base=interval)    # enforce regular spacing
    # ax.xaxis.set_major_locator(locator)

    locator = mdates.DayLocator(interval=interval)
    ax.xaxis.set_major_locator(locator)
    ax.set_xlim(left=base)
    # Manually set tick locations if needed:
    ticks = pd.date_range(start=base, end=daily_totals["Date"].max(), freq=f"{interval}D")
    ax.set_xticks(ticks)


    # ax.set_xlim(left=base)
    # ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    fig.autofmt_xdate()

    return fig

def suggest_credit_categories(df, threshold=1000):
    """
    Suggest categories likely to be credit accounts based on significant positive transactions.
    """
    positive_agg = df[df["Amount"] > 0].groupby("Category")["Amount"].sum()
    frequent_positives = positive_agg[positive_agg > threshold].sort_values(ascending=False)
    return frequent_positives
