import logging
import os
import json
from expense_classifier import ExpenseClassifier
from fuzzy_utils import group_similar_transactions

class AppController:
    def __init__(self):
        self.classifier = ExpenseClassifier()
        self.transactions = []
        # self.classifications = self.classifier.classifications

    def set_transactions_df(self, df):
        self.df = df

    def get_grouped_transactions(self, target_row):
        # Assuming self.df is your DataFrame of transactions
        merged_rows = group_similar_transactions(self.df, target_row)
        return merged_rows

    def get_prediction(self, transaction_detail):
        """Predict the expense category for a given transaction."""
        return self.classifier.predict_category(transaction_detail, top_n=2)

    def save_classifications(self):
        self.classifier.save_classifications()
