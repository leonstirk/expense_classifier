# config.py
import logging

# Logging settings
LOG_LEVEL = logging.DEBUG  # Change to logging.INFO for less verbose output

# Configure logging globally
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("app.log"),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console
    ]
)

# File paths
CLASSIFICATION_FILE = "assets/expense_classifications.json"
EXPENSE_CATEGORIES_FILE = "assets/expense_categories.json"
CONFIDENCE_THRESHOLD = 0.8  # Set threshold for high-confidence classification
FUZZY_MATCH_THRESHOLD = 0.7  # Threshold for fuzzy matching similar transactions