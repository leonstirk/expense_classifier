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
from analytics import load_classified_data, create_spending_plot, create_spending_vs_transfer_plot
from tkcalendar import DateEntry

class AppGUI:
    def __init__(self, master, controller):
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
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Summary")

        # Summary sidebar
        self.summary_sidebar = ttk.Frame(self.summary_tab)
        self.summary_sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.summary_btn = tk.Button(self.summary_sidebar, text="Show Summary", command=self.show_summary)
        self.summary_btn.pack(pady=10)


        # --- Analytics tab ---
        self.analytics_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_tab, text="Analytics")

        # Analyics sidebar
        self.analytics_sidebar = ttk.Frame(self.analytics_tab)
        self.analytics_sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.analytics_view_mode = tk.StringVar(value="M")

        # # Create a frame for options
        # option_frame = ttk.Frame(self.analytics_tab)
        # option_frame.pack(pady=(0, 10))

        # View mode dropdown
        ttk.Label(self.analytics_sidebar, text="View by:").pack(side="left", padx=(0, 5))
        view_dropdown = ttk.Combobox(
            self.analytics_sidebar,
            textvariable=self.analytics_view_mode,
            values=["M", "F", "W"],
            state="readonly",
            width=10
        )
        view_dropdown.pack(side="left", padx=(0, 10))
        view_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_analytics_tab())

        # Date selector
        ttk.Label(self.analytics_sidebar, text="Start date:").pack(side="left", padx=(10, 5))
        self.analytics_start_date = tk.StringVar()
        date_entry = DateEntry(self.analytics_sidebar, textvariable=self.analytics_start_date, width=12, date_pattern="yyyy-mm-dd")
        date_entry.pack(side="left")

        self.update_analytics_tab()


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
        for widget in self.summary_tab.winfo_children():
            widget.destroy()

        # Create Treeview table
        tree = ttk.Treeview(self.summary_tab, columns=("Category", "Amount", "Count"), show="headings", height = 15)
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

    def update_analytics_tab(self):
        for widget in self.analytics_tab.winfo_children():
            widget.destroy()

        # Heading and controls
        heading = ttk.Label(self.analytics_tab, text="Spending Overview", font=("Segoe UI", 14, "bold"))
        heading.pack(pady=(10, 5))

        # # Dropdown to select view mode (Monthly or Weekly)
        # mode_frame = ttk.Frame(self.analytics_tab)
        # mode_frame.pack(pady=(0, 10))

        # ttk.Label(mode_frame, text="View by:").pack(side="left", padx=(0, 5))

        # view_dropdown = ttk.Combobox(
        #     mode_frame,
        #     textvariable=self.analytics_view_mode,
        #     values=["M", "F", "W"],
        #     state="readonly",
        #     width=10
        # )
        # view_dropdown.pack(side="left")
        # view_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_analytics_tab())

        # Load data and plot
        df = load_classified_data()
        if df.empty:
            ttk.Label(self.analytics_tab, text="No data available for analytics.").pack(pady=20)
            return

        # fig = create_spending_vs_transfer_plot(df, freq=self.analytics_view_mode.get())
        start_date = self.analytics_start_date.get() or None
        fig = create_spending_vs_transfer_plot(df, freq=self.analytics_view_mode.get(), start_date=start_date)

        canvas = FigureCanvasTkAgg(fig, master=self.analytics_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Optional refresh button (if needed)
        ttk.Button(self.analytics_tab, text="Refresh Chart", command=self.update_analytics_tab).pack(pady=10)



if __name__ == "__main__":
    master = tk.Tk()
    controller = AppController()  # ✅ Create the controller first
    app = AppGUI(master, controller)  # ✅ Pass controller to AppGUI
    master.mainloop()



