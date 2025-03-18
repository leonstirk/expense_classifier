## Expense Classifier
# This script is a simple GUI tool to help classify expenses from a transaction file.

import pandas as pd
import json
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Canvas, Frame
from difflib import get_close_matches
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import numpy as np

# File paths
CLASSIFICATION_FILE = "expense_classifications.json"
EXPENSE_CATEGORIES_FILE = "expense_categories.json"
CONFIDENCE_THRESHOLD = 0.8  # Set threshold for high-confidence classification
FUZZY_MATCH_THRESHOLD = 0.7  # Threshold for fuzzy matching similar transactions

# Load or initialize expense categories
def load_expense_categories():
    if os.path.exists(EXPENSE_CATEGORIES_FILE):
        with open(EXPENSE_CATEGORIES_FILE, "r") as f:
            return json.load(f)
    return {}

EXPENSE_CATEGORIES = load_expense_categories()

# Load or initialize classification memory
def load_classifications():
    if os.path.exists(CLASSIFICATION_FILE):
        with open(CLASSIFICATION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_classifications(classifications):
    with open(CLASSIFICATION_FILE, "w") as f:
        json.dump(classifications, f, indent=4)

class ExpenseClassifierGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Classifier")
        self.root.geometry("800x700")
        
        self.classifications = load_classifications()
        self.df = None
        self.current_index = 0
        self.fuzzy_match_vars = []

        # Add scrollable frame
        self.canvas = Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
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

        self.transaction_info_label = tk.Label(self.scrollable_frame, text="Select a transaction file to begin", font=("Arial", 12))
        self.transaction_info_label.pack(pady=10)
        
        self.category_var = tk.StringVar()
        self.category_tree = ttk.Treeview(self.scrollable_frame)
        self.category_tree.pack(pady=10)
        
        self.populate_category_tree()
        
        self.prediction_label = tk.Label(self.scrollable_frame, text="", font=("Arial", 12))
        self.prediction_label.pack(pady=10)
        
        self.fuzzy_match_frame = tk.Frame(self.scrollable_frame)
        self.fuzzy_match_frame.pack(pady=10)

        self.confirm_btn = tk.Button(self.scrollable_frame, text="Confirm Classification", command=self.classify_current)
        self.confirm_btn.pack(pady=10)
        
        self.summary_btn = tk.Button(self.scrollable_frame, text="Show Summary", command=self.show_summary)
        self.summary_btn.pack(pady=10)

    def show_summary(self):
        if self.df is not None:
            summary = self.df.groupby("Category")["Amount"].sum().reset_index()
            print("\nExpense Summary:")
            print(summary)
            messagebox.showinfo("Summary", summary.to_string())

    def populate_category_tree(self):
        """ Populate the hierarchical category dropdown """
        self.category_tree.heading("#0", text="Select a Category", anchor=tk.W)
        for parent_category, subcategories in EXPENSE_CATEGORIES.items():
            parent_id = self.category_tree.insert("", "end", text=parent_category, open=False)
            for subcategory in subcategories:
                self.category_tree.insert(parent_id, "end", text=subcategory)
        
        self.category_tree.bind("<ButtonRelease-1>", self.on_category_select)
    
    def on_category_select(self, event):
        """ Set selected category """
        selected_item = self.category_tree.selection()
        if selected_item:
            self.category_var.set(self.category_tree.item(selected_item[0], "text"))

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if file_path:
            if file_path.endswith(".csv"):
                self.df = pd.read_csv(file_path)
            else:
                self.df = pd.read_excel(file_path)
            self.current_index = 0
            self.show_next_transaction()

    def show_next_transaction(self):
        if self.df is None or self.current_index >= len(self.df):
            messagebox.showinfo("Complete", "All transactions classified!")
            return
        row = self.df.iloc[self.current_index]
        identical_rows = self.df[self.df["Details"] == row["Details"]]
        fuzzy_matches = get_close_matches(row["Details"], self.df["Details"].unique(), n=5, cutoff=FUZZY_MATCH_THRESHOLD)
        
        transactions_text = "\n".join([f"Date: {r['Date']} | Amount: {r['Amount']} | Description: {r['Details']}" for _, r in identical_rows.iterrows()])
        
        self.transaction_info_label.config(text=f"Review transactions:\n{transactions_text}")
        
        # Clear previous fuzzy match checkboxes
        for widget in self.fuzzy_match_frame.winfo_children():
            widget.destroy()
        self.fuzzy_match_vars = []

        # Display fuzzy match checkboxes
        tk.Label(self.fuzzy_match_frame, text="Fuzzy Matches:", font=("Arial", 10)).pack()
        for match in fuzzy_matches:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.fuzzy_match_frame, text=match, variable=var)
            chk.pack(anchor='w')
            self.fuzzy_match_vars.append((match, var))
    
    def classify_current(self):
        category = self.category_var.get()
        if not category:
            messagebox.showerror("Error", "Please select a category.")
            return
        
        row = self.df.iloc[self.current_index]
        self.classifications[row["Details"]] = category
        save_classifications(self.classifications)
        
        identical_rows = self.df[self.df["Details"] == row["Details"]]
        self.df.loc[identical_rows.index, "Category"] = category
        
        for match, var in self.fuzzy_match_vars:
            if var.get():
                self.df.loc[self.df["Details"] == match, "Category"] = category
                self.classifications[match] = category
        
        save_classifications(self.classifications)
        self.current_index += len(identical_rows)
        self.show_next_transaction()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseClassifierGUI(root)
    root.mainloop()
