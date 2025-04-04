## Expense Classifier

import logging
import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from config import CLASSIFICATION_FILE  # Import global settings
from utils import clean_description  # Import the clean_description function

class ExpenseClassifier:
    def __init__(self, classification_file=CLASSIFICATION_FILE):
        self.classification_file = classification_file
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.classifier = MultinomialNB()
        self.label_encoder = LabelEncoder()
        self._load_classifications()
        self._train_model()

    def _train_model(self):
        """Train the classifier using only manually classified transactions."""
        if not self.classifications:
            logging.warning("No classifications available. Skipping training.")
            self.is_trained = False
            return

        descriptions = []
        categories = []

        for entry in self.classifications.values():
            if entry.get("Source") != "manual":
                continue  # ✅ Skip auto-classified data

            # descriptions.append(entry["Description"])
            descriptions.append(clean_description(entry["Description"]))
            categories.append(entry["Category"])

        if not descriptions:
            logging.warning("No manual classifications found. Skipping training.")
            self.is_trained = False
            return

        self.label_encoder.fit(categories)
        y_train = self.label_encoder.transform(categories)
        X_train = self.vectorizer.fit_transform(descriptions)
        self.classifier.fit(X_train, y_train)

        self.is_trained = True
        logging.info(f"Model trained on {len(descriptions)} manually classified transactions.")


    def _load_classifications(self):
        with open(self.classification_file, "r") as f:
            self.classifications = json.load(f)

    # def _load_classifications(self):
    #     with open(self.classification_file, "r") as f:
    #         self.classifications = json.load(f)

    # def reload_and_retrain(self):
    #     """Reloads the classification file and retrains the model."""
    #     self._load_classifications()
    #     self._train_model()

    def save_classifications(self):
        """Save the current classifications to file and retrain the model."""
        with open(self.classification_file, "w") as f:
            json.dump(self.classifications, f, indent=4)
        self._train_model()
        logging.info("Classifications saved and model retrained.")

    # def save_classifications(self):
    #     with open(self.classification_file, "w") as f:
    #         json.dump(self.classifications, f, indent=4)
    #     self._train_model()

    # def predict_category(self, transaction_detail, top_n=2):
    #     """Predicts the expense category for a transaction."""
    #     X_test = self.vectorizer.transform([transaction_detail])
    #     probabilities = self.classifier.predict_proba(X_test)[0]
    #     category_indices = np.argsort(probabilities)[::-1][:top_n]

    #     return [(self.label_encoder.inverse_transform([idx])[0], probabilities[idx]) for idx in category_indices]

    def predict_category(self, transaction_detail, top_n=3):
        """Predicts the expense category for a transaction."""
        if not getattr(self, "is_trained", False):
            logging.warning("Prediction attempted before training. Returning empty prediction.")
            return []

        # X_test = self.vectorizer.transform([transaction_detail])
        X_test = self.vectorizer.transform([clean_description(transaction_detail)])
        probabilities = self.classifier.predict_proba(X_test)[0]
        category_indices = np.argsort(probabilities)[::-1][:top_n]

        return [(self.label_encoder.inverse_transform([idx])[0], probabilities[idx]) for idx in category_indices]
