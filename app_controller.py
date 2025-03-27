import os
import json
from expense_classifier import ExpenseClassifier

class AppController:
    def __init__(self):
        self.classifier = ExpenseClassifier()
        self.transactions = []
        self.classifications = self.classifier.classifications

    def get_prediction(self, transaction_detail):
        """Predict the expense category for a given transaction."""
        return self.classifier.predict_category(transaction_detail, top_n=3)

    # The below funcitons might need to be moved to somewhere more appropriate if they are needed at all
    # Load or initialize classification memory
    # def load_classifications():
    #     if os.path.exists(CLASSIFICATION_FILE):
    #         with open(CLASSIFICATION_FILE, "r") as f:
    #             return json.load(f)
    #     return {}

    def save_classifications(self):
        with open(self.classification_file, "w") as f:
            json.dump(self.classifications, f, indent=4)
    
        # Retrain model using updated data
        self.classifier.reload_and_retrain()