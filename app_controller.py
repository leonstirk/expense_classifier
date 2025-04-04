from expense_classifier import ExpenseClassifier
from fuzzy_utils import group_similar_transactions
from utils import generate_transaction_id
import re
from collections import Counter

class AppController:
    def __init__(self):
        self.classifier = ExpenseClassifier()
        self.transactions = []
        # self.classifications = self.classifier.classifications

    def set_transactions_df(self, df):
        self.df = df

    # def get_unclassified_transactions(self):
    #     classified_indices = set(map(int, self.classifier.classifications.keys()))
    #     return self.df[~self.df.index.isin(classified_indices)]

    def get_unclassified_transactions(self):
        classified_ids = set(self.classifier.classifications.keys())
        return self.df[
            ~self.df.apply(generate_transaction_id, axis=1).isin(classified_ids)
        ]

    # def get_grouped_transactions(self, target_row):
    #     # Assuming self.df is your DataFrame of transactions
    #     merged_rows = group_similar_transactions(self.df, target_row)
    #     return merged_rows
    
    def get_grouped_transactions(self, row):
        unclassified_df = self.get_unclassified_transactions()
        return group_similar_transactions(unclassified_df, row)


    def get_prediction(self, transaction_detail):
        """Predict the expense category for a given transaction."""
        return self.classifier.predict_category(transaction_detail, top_n=2)

    def save_classifications(self):
        self.classifier.save_classifications()

    # def auto_classify_high_confidence(self):
    #     """
    #     Scan unclassified transactions and automatically classify those
    #     with very high confidence predictions.
    #     """
    #     unclassified_df = self.get_unclassified_transactions()

    #     for idx, row in unclassified_df.iterrows():
    #         predictions = self.get_prediction(row["Details"])
    #         top_prediction, top_prob = predictions[0]

    #         if top_prob >= AUTO_CLASSIFY_THRESHOLD:
    #             self.classifier.classifications[str(idx)] = {
    #                 "Description": row["Details"],
    #                 "Category": top_prediction,
    #                 "Method": "auto"
    #             }

    #     self.classifier.save_classifications()

    # Function to show the most common tokens in the transaction descriptions
    # Development only. Comment self.controller.show_common_tokens() in load_file()
    def show_common_tokens(self, top_n=30):
        if self.df is None:
            print("No data loaded.")
            return

        all_tokens = []

        for desc in self.df["Details"].astype(str):
            # Lowercase and remove special characters
            desc = desc.lower()
            tokens = re.findall(r"\b\w+\b", desc)
            all_tokens.extend(tokens)

        token_counts = Counter(all_tokens)
        print(f"\nTop {top_n} most common tokens:\n")
        for token, count in token_counts.most_common(top_n):
            print(f"{token:<15} {count}")   