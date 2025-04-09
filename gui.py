# Description: GUI for the expense classifier application.

import logging
import os
import json
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox #, Canvas, Frame
from app_controller import AppController
from utils import generate_transaction_id
from config import AUTO_CLASSIFY_THRESHOLD, CLASSIFICATION_FILE
from scrollable_frame import ScrollableFrame  # if you saved it separately
# from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from analytics import load_classified_data, create_spending_vs_transfer_plot, create_rolling_average_plot, create_category_breakdown_plot

BARPLOT_OPTIONS = {
    "Monthly": 30,
    "Fortnightly": 14,
    "Weekly": 7,
}   

ROLLING_OPTIONS = {
    "7D Rolling": 7,
    "14D Rolling": 14,
    "30D Rolling": 30,
}

class AppGUI:

    def __init__(self, master, controller):
        # Set style 
        #style = ttk.Style()
        #style.theme_use("clam")

        self.master = master  # ✅ Store root window
        self.controller = controller  # ✅ Store controller instance

        self.master.title("Expense Classifier")
        self.master.geometry("1400x800")

        self.df = None
        self.current_index = 0

        self.controller = AppController()


        ## --- Notebook setup ---
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True)


        # --- Classification Tab ---
        self.classify_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.classify_tab, text="Classify")

        # Classification sidebar
        self.classification_sidebar = ttk.Frame(self.classify_tab)
        self.classification_sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Sidebar buttons
        self.file_btn = tk.Button(self.classification_sidebar, text="Load Transactions", command=self.load_file)
        self.file_btn.pack(pady=10)

        # Progress label
        self.progress_label = ttk.Label(self.classification_sidebar, text="")
        self.progress_label.pack(anchor="e", padx=10, pady=(0, 10))

        # Cards inside scrollable frame
        self.card_scrollable = ScrollableFrame(self.classify_tab, height=450)
        self.card_scrollable.pack(fill="both", expand=True)
        self.card_frame = self.card_scrollable.inner_frame
        
        
        # --- Summary tab ---
        # Add summary tab to notebook
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Summary")

        # Frame for the summary tab
        self.summary_frame = ttk.Frame(self.summary_tab)
        self.summary_frame.pack(fill="both", expand=True)

        # Summary sidebar
        self.summary_sidebar = ttk.Frame(self.summary_frame)
        self.summary_sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Summary working output
        self.summary_main = ttk.Frame(self.summary_frame)
        self.summary_main.pack(side="right", fill="both", expand=True)

        # Summary button
        self.summary_btn = tk.Button(self.summary_sidebar, text="Show Summary", command=self.show_summary)
        self.summary_btn.pack(pady=10)


        # --- Analytics tab ---
        # Add analytics tab to notebook
        self.analytics_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_tab, text="Analytics")

        # Frame for the analytics tab
        self.analytics_frame = ttk.Frame(self.analytics_tab)
        self.analytics_frame.pack(fill="both", expand=True)

        # Analytics sidebar
        self.analytics_sidebar = ttk.Frame(self.analytics_frame)
        self.analytics_sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Analytics working output
        self.analytics_main = ttk.Frame(self.analytics_frame)
        self.analytics_main.pack(side="right", fill="both", expand=True)

        # View mode dropdown
        ttk.Label(self.analytics_sidebar, text="View by:").pack(padx=(10, 2))
        # Set default view mode
        self.analytics_view_mode = tk.StringVar(value="7D Rolling")
        # Create dropdown for view mode
        view_dropdown = ttk.Combobox(
            self.analytics_sidebar,
            textvariable=self.analytics_view_mode,
            values=["Monthly", "Fortnightly", "Weekly", "7D Rolling", "14D Rolling", "30D Rolling"],
            state="readonly",
            width=10
        )
        view_dropdown.pack(padx=(0, 10))
        view_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_analytics_main())

        # Date selector
        self.analytics_start_date = tk.StringVar()
        ttk.Label(self.analytics_sidebar, text="Start date (yyyy-mm-dd):").pack(pady=(10, 2))

        date_entry = ttk.Entry(
            self.analytics_sidebar,
            textvariable=self.analytics_start_date,
            width=15
        )
        date_entry.pack(pady=(0, 10))

        # Category breakdown vs total spend
        self.analytics_mode = tk.StringVar(value="Total Spend")

        ttk.Label(self.analytics_sidebar, text="View mode:").pack(pady=(10, 2), anchor="w")

        ttk.Radiobutton(
            self.analytics_sidebar,
            text="Total Spend",
            variable=self.analytics_mode,
            value="Total Spend",
            command=self.update_analytics_main
        ).pack(anchor="w")

        ttk.Radiobutton(
            self.analytics_sidebar,
            text="Category Breakdown",
            variable=self.analytics_mode,
            value="Category Breakdown",
            command=self.update_analytics_main
        ).pack(anchor="w")

        # Refresh chart button
        refresh_button = ttk.Button(
            self.analytics_sidebar,
            text="Refresh Chart",
            command=self.update_analytics_main
        )
        refresh_button.pack(pady=(10, 0))

        # Toggle credit-expenditure vs expenditure only view
        self.analytics_show_credit = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.analytics_sidebar,
            text="Show credit categories",
            variable=self.analytics_show_credit,
            command=self.update_analytics_main  # or .tab if that’s your trigger
        ).pack(pady=(5, 10), anchor="w")

        self.update_analytics_main()


    def show_summary(self):
        if self.df is None:
            messagebox.showinfo("No data", "Please load a transaction file first.")
            return

        # Add UID and Category columns
        self.df["UID"] = self.df.apply(generate_transaction_id, axis=1)
        classifications = self.controller.classifier.classifications
        self.df["Category"] = self.df["UID"].map(
            lambda uid: classifications.get(uid, {}).get("Category", "Unclassified")
        )

        # Group and summarize
        summary_df = self.df.groupby("Category").agg(
            TotalAmount=("Amount", "sum"),
            Count=("Amount", "count")
        ).reset_index().sort_values(by="TotalAmount", ascending=False)

        # Clear previous summary display
        for widget in self.summary_main.winfo_children():
            widget.destroy()

        # Create Treeview table
        tree = ttk.Treeview(self.summary_main, columns=("Category", "Amount", "Count"), show="headings", height = 15)
        tree.heading("Category", text="Category")
        tree.heading("Amount", text="Total Amount")
        tree.heading("Count", text="Transactions")

        tree.column("Category", anchor="w", width=200)
        tree.column("Amount", anchor="e", width=120)
        tree.column("Count", anchor="center", width=100)

        # Insert rows
        for _, row in summary_df.iterrows():
            tree.insert("", "end", values=(
                row["Category"],
                f"${row['TotalAmount']:.2f}",
                row["Count"]
            ))

        tree.pack(fill="x", padx=10)


    def update_progress_label(self):
        if self.df is None:
            self.progress_label.config(text="No data loaded.")
            return

        total = len(self.df)

        # Generate all UIDs from current file
        file_uids = set(self.df.apply(generate_transaction_id, axis=1))

        # Count how many of those have been classified
        classified_uids = set(self.controller.classifier.classifications.keys())
        classified = len(file_uids & classified_uids)  # intersection

        percent = int(100 * classified / total) if total else 0
        self.progress_label.config(text=f"Classified {classified} of {total} transactions ({percent}%)")


    def load_file(self):
        logging.debug("Loading transaction file...")    
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if file_path:
            if file_path.endswith(".csv"):
                self.df = pd.read_csv(file_path)
            else:
                self.df = pd.read_excel(file_path)
            # Pass the loaded DataFrame to the controller
            self.controller.set_transactions_df(self.df)
            self.current_index = 0
            self.show_next_transaction()

            # self.controller.show_common_tokens()


    def auto_classify_row(self, transaction):
        uid = generate_transaction_id(transaction)

        if uid in self.controller.classifier.classifications:
            return False  # Already classified

        predictions = self.controller.get_prediction(transaction["Details"])
        if not predictions:
            return False  # No model trained or no prediction available

        top_category, top_conf = predictions[0]
        if top_conf >= AUTO_CLASSIFY_THRESHOLD:
            self.controller.classifier.classifications[uid] = {
                "Description": transaction["Details"],
                "Category": top_category,
                "Source": "auto",
                "Date": transaction["Date"],
                "Amount": transaction["Amount"]
            }
            return True

        return False


    ## Frame based cards layout rendering function 
    def display_transaction_cards(self, merged_rows):
        # Clear old cards
        for widget in self.card_frame.winfo_children():
            widget.destroy()

        for _, r in merged_rows.iterrows():
            uid = generate_transaction_id(r)
            if uid in self.controller.classifier.classifications:
                continue

            predictions = self.controller.get_prediction(r["Details"])[:2]

            card = ttk.Frame(self.card_frame, padding=10, relief="raised", borderwidth=1)
            card.pack(fill="x", padx=10, pady=5)

            # --- Layout rows using .grid() ---
            ttk.Label(card, text=f"{r['Date']}").grid(row=0, column=0, sticky="w", padx=(0, 10))
            ttk.Label(card, text=f"{r['Details']}").grid(row=0, column=1, sticky="w", padx=(0, 10))
            ttk.Label(card, text=f"${r['Amount']}").grid(row=0, column=2, sticky="w", padx=(0, 20))

            # Prediction buttons
            pred_frame = ttk.Frame(card)
            pred_frame.grid(row=0, column=3, sticky="w")

            for i, (category, confidence) in enumerate(predictions):
                ttk.Button(
                    pred_frame,
                    text=f"{category} ({confidence:.2f})",
                    command=lambda c=category, row=r: self.confirm_classification(row, c)
                ).grid(row=0, column=i, padx=(0, 5))

            # Manual classification
            manual_frame = ttk.Frame(card)
            manual_frame.grid(row=0, column=4, sticky="w", padx=(20, 0))

            ttk.Label(manual_frame, text="Manual:").grid(row=0, column=0)

            existing_categories = sorted(set(
                entry["Category"]
                for entry in self.controller.classifier.classifications.values()
            ))

            category_box = ttk.Combobox(manual_frame, values=existing_categories, state="normal", width=18)
            category_box.set("Select a category")
            category_box.grid(row=0, column=1, padx=5)

            ttk.Button(
                manual_frame,
                text="Confirm",
                command=lambda row=r, box=category_box: self.confirm_classification(row, box.get())
            ).grid(row=0, column=2, padx=(5, 0))


    def show_next_transaction(self):
        # STEP 1: Get rows from current file
        if self.df is None:
            return

        # STEP 2: Generate UIDs from the current file
        file_uids = self.df.apply(generate_transaction_id, axis=1)
        classified_uids = set(self.controller.classifier.classifications.keys())

        # STEP 3: Filter to only unclassified rows
        unclassified_df = self.df[~file_uids.isin(classified_uids)]

        # STEP 4: Auto-classify those that qualify
        auto_classified = []
        for _, row in unclassified_df.iterrows():
            if self.auto_classify_row(row):
                auto_classified.append(generate_transaction_id(row))

        # STEP 5: Save new auto classifications (if any)
        if auto_classified:
            self.controller.save_classifications()
            self.update_progress_label()

            # Refresh classification after saving
            classified_uids = set(self.controller.classifier.classifications.keys())
            file_uids = self.df.apply(generate_transaction_id, axis=1)
            unclassified_df = self.df[~file_uids.isin(classified_uids)]

        # STEP 6: Handle completion or show next group
        if unclassified_df.empty:
            messagebox.showinfo("Complete", "All transactions classified!")
            return

        row = unclassified_df.iloc[0]
        merged_rows = self.controller.get_grouped_transactions(row)
        self.current_group = merged_rows
        self.display_transaction_cards(merged_rows)


    def confirm_classification(self, transaction, selected_category):
        if not selected_category.strip():
            messagebox.showwarning("Invalid", "Please enter or select a category.")
            return

        uid = generate_transaction_id(transaction)
        self.controller.classifier.classifications[uid] = {
            "Description": transaction["Details"],
            "Category": selected_category.strip(),
            "Source": "manual",
            "Date": transaction["Date"],
            "Amount": transaction["Amount"]
        }

        self.controller.save_classifications()
        self.update_progress_label()
        # messagebox.showinfo("Confirmed", f"Transaction classified as '{selected_category}'.")

        # ✅ Check if all transactions in the current group are now classified

        all_classified = all(
            generate_transaction_id(row) in self.controller.classifier.classifications
            for _, row in self.current_group.iterrows()
        )

        if all_classified:
            self.current_index += 1  # Advance target index only when group is done
            self.show_next_transaction()
        else:
            # Just re-render the current card group to hide confirmed rows
            self.display_transaction_cards(self.current_group)

    def update_analytics_main(self):
        for widget in self.analytics_main.winfo_children():
            widget.destroy()

        # Heading and controls
        heading = ttk.Label(self.analytics_main, text="Spending Overview", font=("Segoe UI", 14, "bold"))
        heading.pack(pady=(10, 5))

        # Load data and plot
        df = load_classified_data()
        if df.empty:
            ttk.Label(self.analytics_main, text="No data available for analytics.").pack(pady=20)
            return

        # Get start date from entry
        start_date_str = self.analytics_start_date.get().strip() or None

        # Optional validation
        try:
            start_date = pd.to_datetime(start_date_str) if start_date_str else None
        except ValueError:
            messagebox.showwarning("Invalid date", "Please enter a valid start date (yyyy-mm-dd)")
            return

        mode = self.analytics_view_mode.get()

        # if mode in ROLLING_OPTIONS:
        #     fig = create_rolling_average_plot(df, window=ROLLING_OPTIONS[mode], start_date=start_date)
        # else:
        #     fig = create_spending_vs_transfer_plot(
        #         df,
        #         freq=BARPLOT_OPTIONS[mode],
        #         start_date=start_date,
        #         show_credit=self.analytics_show_credit.get()
        #     )

        if self.analytics_mode.get() == "Category Breakdown" and mode in ROLLING_OPTIONS:
            fig = create_category_breakdown_plot(df, window=ROLLING_OPTIONS[mode], top_n=5, start_date=start_date)
        elif mode in ROLLING_OPTIONS:
            fig = create_rolling_average_plot(df, window=ROLLING_OPTIONS[mode], start_date=start_date)
        else:
            fig = create_spending_vs_transfer_plot(
                df,
                freq=BARPLOT_OPTIONS[mode],
                start_date=start_date,
                show_credit=self.analytics_show_credit.get()
            )


        canvas = FigureCanvasTkAgg(fig, master=self.analytics_main)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    master = tk.Tk()
    controller = AppController()  # ✅ Create the controller first
    app = AppGUI(master, controller)  # ✅ Pass controller to AppGUI
    master.mainloop()



