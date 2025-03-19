## Expense Classifier

# import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder

class ExpenseClassifier:
    def __init__(self, expense_classifications):
        self.expense_classifications = expense_classifications
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.classifier = MultinomialNB()
        self.label_encoder = LabelEncoder()
        self._train_model()

    def _train_model(self):
        """Train the classifier with known expense categories."""
        descriptions = list(self.expense_classifications.keys())
        categories = list(self.expense_classifications.values())

        self.label_encoder.fit(categories)
        y_train = self.label_encoder.transform(categories)
        X_train = self.vectorizer.fit_transform(descriptions)

        self.classifier.fit(X_train, y_train)
        logging.info("Expense Classifier trained successfully.")

    def predict_category(self, transaction_detail, top_n=3):
        """Predicts the expense category for a transaction."""
        X_test = self.vectorizer.transform([transaction_detail])
        probabilities = self.classifier.predict_proba(X_test)[0]
        category_indices = np.argsort(probabilities)[::-1][:top_n]

        return [(self.label_encoder.inverse_transform([idx])[0], probabilities[idx]) for idx in category_indices]
