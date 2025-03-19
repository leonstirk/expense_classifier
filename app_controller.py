import os
import json
from expense_classifier import ExpenseClassifier
from config import CLASSIFICATION_FILE  # Import global settings

class AppController:
    def __init__(self):
        with open("data/expense_classifications.json", "r") as f:
            expense_classifications = json.load(f)
        self.classifier = ExpenseClassifier(expense_classifications)

    def predict_expense(self, transaction_detail):
        """Predict the expense category for a given transaction."""
        return self.classifier.predict_category(transaction_detail, top_n=3)

    # The below funcitons might need to be moved to somewhere more appropriate if they are needed at all
    # Load or initialize classification memory
    def load_classifications():
        if os.path.exists(CLASSIFICATION_FILE):
            with open(CLASSIFICATION_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_classifications(classifications):
        with open(CLASSIFICATION_FILE, "w") as f:
            json.dump(classifications, f, indent=4)
