import json
from expense_classifier import ExpenseClassifier

class AppController:
    def __init__(self):
        with open("data/expense_classifications.json", "r") as f:
            expense_classifications = json.load(f)
        self.classifier = ExpenseClassifier(expense_classifications)

    def predict_expense(self, transaction_detail):
        """Predict the expense category for a given transaction."""
        return self.classifier.predict_category(transaction_detail, top_n=3)



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
