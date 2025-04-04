# Description: GUI for the expense classifier application.

import logging
import os
import json
import platform
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Canvas, Frame
from difflib import get_close_matches
# from sklearn.pipeline import make_pipeline
from app_controller import AppController
from utils import generate_transaction_id
from config import AUTO_CLASSIFY_THRESHOLD
from scrollable_frame import ScrollableFrame  # if you saved it separately

class AppGUI:
    def __init__(self, master, controller):
        self.master = master  # ✅ Store root window
        self.controller = controller  # ✅ Store controller instance

        self.master.title("Expense Classifier")
        self.master.geometry("1400x800")

        self.df = None
        self.current_index = 0
        # self.fuzzy_match_vars = []

        self.progress_label = ttk.Label(self.master, text="")
        self.progress_label.pack(anchor="e", padx=10, pady=(0, 10))

        # Sidebar container (static frame, no scrolling)
        self.sidebar_frame = ttk.Frame(self.master)
        self.sidebar_frame.pack(side="left", fill="y", padx=10, pady=10)

        # Scrollable frame for transaction cards
        self.card_scrollable = ScrollableFrame(self.master, height=450)
        self.card_scrollable.pack(fill="both", expand=True)
        self.card_frame = self.card_scrollable.inner_frame

        # Summary output area (will hold the Treeview)
        self.summary_frame = ttk.Frame(self.master)
        self.summary_frame.pack(fill="x", padx=10, pady=(5, 15))

        # UI Components
        self.file_btn = tk.Button(self.sidebar_frame, text="Load Transactions", command=self.load_file)
        self.file_btn.pack(pady=10)

        # self.status_label = tk.Label(self.master, text="", fg="green")
        # self.status_label.pack()
        
        self.summary_btn = tk.Button(self.sidebar_frame, text="Show Summary", command=self.show_summary)
        self.summary_btn.pack(pady=10)

        self.controller = AppController()

    # def show_summary(self):
    #     if self.df is not None:
    #         summary = self.df.groupby("Category")["Amount"].sum().reset_index()
    #         print("\nExpense Summary:")
    #         print(summary)
    #         messagebox.showinfo("Summary", summary.to_string())


    # def show_summary(self):
    #     if self.df is None:
    #         messagebox.showinfo("No data", "Please load a transaction file first.")
    #         return

    #     # Step 1: Generate UIDs for current file
    #     self.df["UID"] = self.df.apply(generate_transaction_id, axis=1)

    #     # Step 2: Map each UID to a category (from manual + auto classifications)
    #     classifications = self.controller.classifier.classifications
    #     self.df["Category"] = self.df["UID"].map(
    #         lambda uid: classifications.get(uid, {}).get("Category", "Unclassified")
    #     )

    #     # Step 3: Group and summarize
    #     summary = self.df.groupby("Category")["Amount"].sum().reset_index()
    #     summary = summary.sort_values(by="Amount", ascending=False)
    #     summary["Amount"] = summary["Amount"].map(lambda x: f"${x:.2f}")
    #     summary = self.df.groupby("Category").agg(
    #         TotalAmount=("Amount", "sum"),
    #         Count=("Amount", "count")
    #     ).reset_index()

    #     # Step 4: Display
    #     print("\nExpense Summary:")
    #     print(summary)
    #     messagebox.showinfo("Summary", summary.to_string(index=False))

    def show_summary(self):
        if self.df is None:
            messagebox.showinfo("No data", "Please load a transaction file first.")
            return

        from utils import generate_transaction_id

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
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        # Create Treeview table
        tree = ttk.Treeview(self.summary_frame, columns=("Category", "Amount", "Count"), show="headings", height = 15)
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


    # # Load or initialize expense categories
    # def load_expense_categories(self):
    #     if os.path.exists(EXPENSE_CATEGORIES_FILE):
    #         with open(EXPENSE_CATEGORIES_FILE, "r") as f:
    #             return json.load(f)
    #     return {}

    # def update_progress_label(self):
    #     total = len(self.df)
    #     classified = len(self.controller.classifier.classifications)
    #     percent = int(100 * classified / total)
    #     self.progress_label.config(text=f"Classified {classified} of {total} transactions ({percent}%)")
    #     # self.progress_label.config(text=f"Classified {classified} of {total} transactions")

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

    def auto_classify_row(self, row):
        uid = generate_transaction_id(row)

        if uid in self.controller.classifier.classifications:
            return False  # Already classified

        predictions = self.controller.get_prediction(row["Details"])
        if not predictions:
            return False  # No model trained or no prediction available

        top_category, top_conf = predictions[0]
        if top_conf >= AUTO_CLASSIFY_THRESHOLD:
            self.controller.classifier.classifications[uid] = {
                "Description": row["Details"],
                "Category": top_category,
                "Source": "auto"
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

    
    # def show_next_transaction(self):
    #         if self.df is None or self.current_index >= len(self.df):
    #             messagebox.showinfo("Complete", "All transactions classified!")
    #             return

    #         unclassified_df = self.controller.get_unclassified_transactions()

    #         # Auto-classify any rows confidently
    #         auto_classified = []
    #         for _, row in unclassified_df.iterrows():
    #             if self.auto_classify_row(row):
    #                 auto_classified.append(row.name)

    #         # Save if anything was classified
    #         if auto_classified:
    #             self.controller.save_classifications()
    #             self.update_progress_label()
    #             # Re-filter since some rows are now classified
    #             unclassified_df = self.controller.get_unclassified_transactions()

    #         if unclassified_df.empty:
    #             # messagebox.showinfo("Complete", "All transactions classified!")
    #             return

    #         # Reset to show the first unclassified transaction
    #         row = unclassified_df.iloc[0]
    #         merged_rows = self.controller.get_grouped_transactions(row)
    #         self.current_group = merged_rows  # Store current group DataFrame
            
    #         self.update_progress_label()
    #         self.display_transaction_cards(merged_rows)

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
            "Source": "manual"
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


if __name__ == "__main__":
    master = tk.Tk()
    controller = AppController()  # ✅ Create the controller first
    app = AppGUI(master, controller)  # ✅ Pass controller to AppGUI
    master.mainloop()



