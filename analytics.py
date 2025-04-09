import os
import json
import pandas as pd
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
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

    locator = mdates.DayLocator(interval=interval)
    ax.xaxis.set_major_locator(locator)
    ax.set_xlim(left=base)
    # Manually set tick locations if needed:
    ticks = pd.date_range(start=base, end=df["Date"].max(), freq=f"{interval}D")
    ax.set_xticks(ticks)

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


def create_category_breakdown_plot(df, window=10, top_n=5, start_date=None):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Type"] = df["Category"].apply(lambda x: "Credit" if x in CREDIT_CATEGORIES else "Spending")
    df["Amount"] = -df["Amount"]
    spending = df[df["Type"] == "Spending"]

    # Daily spend by category
    pivot = spending.pivot_table(index="Date", columns="Category", values="Amount", aggfunc="sum").fillna(0)

    # Filter top N categories
    total_per_cat = pivot.sum().sort_values(ascending=False)
    top_categories = total_per_cat.head(top_n).index
    pivot = pivot[top_categories]

    # Compute rolling averages
    rolling = pivot.rolling(window=window).mean()

    # Setup plot
    # fig = Figure(figsize=(8, 5), dpi=100)
    # ax = fig.add_subplot(111)


    # Create figure and axes
    fig = Figure(figsize=(8, 5), dpi=100)
    ax1 = fig.add_subplot(111)              # For bars (spending)
    ax2 = ax1.twinx()                        # For rolling average lines
    ax2.set_zorder(ax1.get_zorder() - 1)     # Push behind bars
    ax1.patch.set_visible(False)             # Hide the background of ax2


    color_map = cm.get_cmap("tab10", len(top_categories))
    colors = {cat: color_map(i) for i, cat in enumerate(top_categories)}

    # # Bars: stacked daily spend
    # bottom = np.zeros(len(pivot))
    # for cat in top_categories:
    #     ax.bar(pivot.index, pivot[cat], bottom=bottom, label=cat, alpha=0.6, color=colors[cat])
    #     bottom += pivot[cat].values

    # # Lines: rolling averages
    # for cat in top_categories:
    #     ax.plot(rolling.index, rolling[cat], label=f"{cat} ({window}d avg)", linewidth=2, color=colors[cat])


    # Plot stacked bars on ax1
    bottom = np.zeros(len(pivot))
    for cat in top_categories:
        ax1.bar(pivot.index, pivot[cat], bottom=bottom, label=cat, alpha=0.6, color=colors[cat])
        bottom += pivot[cat].values

    # Plot rolling averages on ax2
    for cat in top_categories:
        ax2.plot(rolling.index, rolling[cat], label=f"{cat} ({window}d avg)", linewidth=2, color=colors[cat])


    # ax.set_title(f"Daily Spend by Category with {window}-Day Rolling Averages")
    # ax.set_xlabel("Date")
    # ax.set_ylabel("Amount")
    # ax.grid(True, axis="y")
    # ax.legend(fontsize=8)


    # Labels and layout
    ax1.set_title(f"Daily Spend by Category with {window}-Day Rolling Averages")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Spending")
    ax2.set_ylabel("Rolling Average")
    ax1.grid(True, axis="y")

    # Custom tick alignment based on start_date and rolling window
    base = pd.to_datetime(start_date or df["Date"].min())
    interval = window

    locator = mdates.DayLocator(interval=interval)
    ax1.xaxis.set_major_locator(locator)
    ax1.set_xlim(left=base)
    # Manually set tick locations if needed:
    ticks = pd.date_range(start=base, end=df["Date"].max(), freq=f"{interval}D")
    ax1.set_xticks(ticks)

    # ax1.xaxis.set_major_formatter(mdates.DateFormatter("%a %d %b"))
    fig.autofmt_xdate()

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, fontsize=8, loc="upper left")

    return fig


def suggest_credit_categories(df, threshold=1000):
    """
    Suggest categories likely to be credit accounts based on significant positive transactions.
    """
    positive_agg = df[df["Amount"] > 0].groupby("Category")["Amount"].sum()
    frequent_positives = positive_agg[positive_agg > threshold].sort_values(ascending=False)
    return frequent_positives
