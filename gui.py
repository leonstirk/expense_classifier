# Description: GUI for the expense classifier application.

import logging
import os
import json
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Canvas, Frame
from difflib import get_close_matches
# from sklearn.pipeline import make_pipeline
from app_controller import AppController
from utils import generate_transaction_id
from config import EXPENSE_CATEGORIES_FILE, AUTO_CLASSIFY_THRESHOLD


class AppGUI:
    def __init__(self, master, controller):
        self.master = master  # ✅ Store root window
        self.controller = controller  # ✅ Store controller instance

        self.master.title("Expense Classifier")
        self.master.geometry("1400x700")
        
        #self.classifications = AppController.load_classifications()
        #logging.debug(f"Loaded classifications: {self.classifications}")

        self.df = None
        self.current_index = 0
        # self.fuzzy_match_vars = []

        self.progress_label = ttk.Label(self.master, text="")
        self.progress_label.pack(anchor="e", padx=10, pady=(0, 10))

        # Add scrollable frame
        self.canvas = Canvas(master)
        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # UI Components
        self.file_btn = tk.Button(self.scrollable_frame, text="Load Transactions", command=self.load_file)
        self.file_btn.pack(pady=10)

        ############################################
        ## Frame based cards layout
        self.card_canvas = tk.Canvas(self.master, height=500)
        self.card_frame = ttk.Frame(self.card_canvas)

        # Attach card_frame to a scrollbar
        scrollbar = ttk.Scrollbar(self.master, orient="vertical", command=self.card_canvas.yview)
        self.card_canvas.configure(yscrollcommand=scrollbar.set)

        # Create a window inside the canvas to hold the frame
        self.canvas_window = self.card_canvas.create_window((0, 0), window=self.card_frame, anchor="nw")

        # Scrollable layout
        self.card_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Update scroll region when the inner frame changes size
        self.card_frame.bind("<Configure>", lambda e: self.card_canvas.configure(scrollregion=self.card_canvas.bbox("all")))
        ############################################

        self.status_label = tk.Label(self.master, text="", fg="green")
        self.status_label.pack()
        
        self.summary_btn = tk.Button(self.scrollable_frame, text="Show Summary", command=self.show_summary)
        self.summary_btn.pack(pady=10)

        self.controller = AppController()

    def show_summary(self):
        if self.df is not None:
            summary = self.df.groupby("Category")["Amount"].sum().reset_index()
            print("\nExpense Summary:")
            print(summary)
            messagebox.showinfo("Summary", summary.to_string())

    # Load or initialize expense categories
    def load_expense_categories(self):
        if os.path.exists(EXPENSE_CATEGORIES_FILE):
            with open(EXPENSE_CATEGORIES_FILE, "r") as f:
                return json.load(f)
        return {}

    def update_progress_label(self):
        total = len(self.df)
        classified = len(self.controller.classifier.classifications)
        percent = int(100 * classified / total)
        self.progress_label.config(text=f"Classified {classified} of {total} transactions ({percent}%)")
        # self.progress_label.config(text=f"Classified {classified} of {total} transactions")

    # def populate_category_tree(self):
    #     """ Populate the hierarchical category dropdown """
    #     self.category_tree.heading("#0", text="Select a Category", anchor=tk.W)
    #     EXPENSE_CATEGORIES = self.load_expense_categories()
    #     if not EXPENSE_CATEGORIES:
    #         logging.warning("No categories found in expense_categories.json!")
    #     for parent_category, subcategories in EXPENSE_CATEGORIES.items():
    #         parent_id = self.category_tree.insert("", "end", text=parent_category, open=False)
    #         for subcategory in subcategories:
    #             self.category_tree.insert(parent_id, "end", text=subcategory)
        
    #     self.category_tree.bind("<ButtonRelease-1>", self.on_category_select)
    
    # def on_category_select(self, event):
    #     """ Set selected category """
    #     selected_item = self.category_tree.selection()
    #     if selected_item:
    #         self.category_var.set(self.category_tree.item(selected_item[0], "text"))


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

    # def auto_classify_row(self, row):
    #     index = row.name
    #     if str(index) in self.controller.classifier.classifications:
    #         return False  # Already classified

    #     predictions = self.controller.get_prediction(row["Details"])
    #     top_category, top_conf = predictions[0]

    #     if top_conf >= AUTO_CLASSIFY_THRESHOLD:
    #         self.controller.classifier.classifications[str(index)] = {
    #             "Description": row["Details"],
    #             "Category": top_category,
    #             "Source": "auto"
    #         }
    #         self.controller.save_classifications()
    #         self.update_progress_label()
    #         return True  # Auto-classified
    #     return False  # Not confident enough

    def auto_classify_row(self, row):
        index = row.name
        if str(index) in self.controller.classifier.classifications:
            return False  # Already classified

        predictions = self.controller.get_prediction(row["Details"])
        if not predictions:
            return False  # No model trained or no prediction available

        top_category, top_conf = predictions[0]
        if top_conf >= AUTO_CLASSIFY_THRESHOLD:
            self.controller.classifier.classifications[str(index)] = {
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
                continue  # ✅ Skip already-classified transactions
            
            predictions = self.controller.get_prediction(r["Details"])
            top_preds = predictions

            card = ttk.Frame(self.card_frame, padding=10, relief="raised", borderwidth=1)
            card.pack(fill="x", padx=10, pady=5)

            ttk.Label(card, text=f"Date: {r['Date']}").pack(anchor="w")
            ttk.Label(card, text=f"Description: {r['Details']}").pack(anchor="w")
            ttk.Label(card, text=f"Amount: ${r['Amount']}").pack(anchor="w")
            # ttk.Label(card, text="Predicted Categories:").pack(anchor="w")
            # ttk.Label(card, text=top_preds, justify="left", foreground="gray").pack(anchor="w")
            
            # Create a container for prediction buttons
            pred_frame = ttk.Frame(card)
            pred_frame.pack(anchor="w", pady=(5, 0))
            ttk.Label(pred_frame, text="Confirm predicted category:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 3))

            for pred in top_preds:
                category, confidence = pred
                # Create a button for each prediction.
                btn = ttk.Button(pred_frame, text=f"{category} ({confidence:.2f})",
                                 command=lambda c=category, row=r: self.confirm_classification(row, c))
                btn.pack(side="left", padx=5)

            # Manual classification section
            manual_frame = ttk.Frame(card)
            manual_frame.pack(anchor="w", pady=(10, 0))

            ttk.Label(manual_frame, text="Or manually select a category:").pack(anchor="w")

            # Build list of known categories (sorted, unique)
            existing_categories = sorted(set(
                entry["Category"]
                for entry in self.controller.classifier.classifications.values()
            ))

            # Rebuild list of known categories (sorted, unique)
            existing_categories = sorted(set(
                entry["Category"]
                for entry in self.controller.classifier.classifications.values()
            ))

            # Create Combobox
            # category_box = ttk.Combobox(manual_frame, values=existing_categories, state="readonly")
            category_box = ttk.Combobox(manual_frame, values=existing_categories, state="normal")  # ← allows typing
            category_box.set("Select a category")
            category_box.pack(anchor="w", pady=(2, 5))

            # Manual confirm button
            ttk.Button(
                manual_frame,
                text="Confirm Manual Classification",
                command=lambda row=r, box=category_box: self.confirm_classification(row, box.get())
            ).pack(anchor="w", pady=(2, 0))

    # def show_next_transaction(self):
    #         if self.df is None or self.current_index >= len(self.df):
    #             messagebox.showinfo("Complete", "All transactions classified!")
    #             return

    #         unclassified_df = self.controller.get_unclassified_transactions()

    #         if unclassified_df.empty:
    #             messagebox.showinfo("Complete", "All transactions classified!")
    #             return

    #         # Reset to show the first unclassified transaction
    #         row = unclassified_df.iloc[0]
    #         merged_rows = self.controller.get_grouped_transactions(row)
    #         self.current_group = merged_rows  # Store current group DataFrame
            
    #         self.update_progress_label()
    #         self.display_transaction_cards(merged_rows)


    def show_next_transaction(self):
            if self.df is None or self.current_index >= len(self.df):
                messagebox.showinfo("Complete", "All transactions classified!")
                return

            unclassified_df = self.controller.get_unclassified_transactions()

            # Auto-classify any rows confidently
            auto_classified = []
            for _, row in unclassified_df.iterrows():
                if self.auto_classify_row(row):
                    auto_classified.append(row.name)

            # Save if anything was classified
            if auto_classified:
                self.controller.save_classifications()
                self.update_progress_label()
                # Re-filter since some rows are now classified
                unclassified_df = self.controller.get_unclassified_transactions()

            if unclassified_df.empty:
                # messagebox.showinfo("Complete", "All transactions classified!")
                return

            # Reset to show the first unclassified transaction
            row = unclassified_df.iloc[0]
            merged_rows = self.controller.get_grouped_transactions(row)
            self.current_group = merged_rows  # Store current group DataFrame
            
            self.update_progress_label()
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



