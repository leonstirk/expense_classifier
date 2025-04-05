# 💸 Expense Classifier

An interactive desktop application to classify and track your personal spending by analyzing bank transaction files. The app uses machine learning to suggest categories for transactions, allows for manual reclassification, and summarizes spending over time.

This project is a work-in-progress with long-term goals of real-time budget tracking, cross-platform accessibility, and usability for non-technical users.

---

## ✨ Features

- ✅ Load monthly transaction files (CSV or XLSX)
- ✅ Automatically group similar transactions with fuzzy matching
- ✅ Predict expense categories using a trainable ML classifier
- ✅ Confirm or manually classify transactions
- ✅ Save and reuse classifications across sessions
- ✅ View summaries by category, including total spend and transaction counts
- ✅ Track progress of classification (percent complete)
- ✅ Custom stopword filtering (e.g. ignoring filler terms like "POS")

---

## 📊 Planned Features

### Phase 1: Personal Insights

-

### Phase 2: Automation

-

### Phase 3: Generalization & Distribution

-

### Phase 4: Web App Conversion

-

---

## 🗂 Roadmap

### 🔭 GitHub Project Board

Track development progress, features, and bugs: 🔗 [Project Board](https://github.com/your-username/your-repo/projects/1)

### 🎯 Milestones

- `v0.5` - Core desktop functionality: classification, summary, reclassification
- `v1.0` - Weekly/monthly analysis, auto-import, real-time alerts
- `v2.0` - Web app prototype, multi-user dashboard, hosted release

---

## 🛠 Getting Started

Clone the repo and install dependencies in a virtual environment:

```bash
git clone https://github.com/your-username/expense-classifier.git
cd expense-classifier
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python gui.py
```

You can load any CSV or Excel file with a transaction list. Make sure it contains columns for date, amount, and description (default: `Date`, `Amount`, `Details`).

---

## 📁 Project Structure

```
├── gui.py                    # Main Tkinter GUI
├── app_controller.py         # Business logic layer
├── expense_classifier.py     # ML classifier and training logic
├── utils.py                  # Fuzzy matching, UID generator, helpers
├── config.py                 # Paths and global constants
├── expense_classifications.json  # Stored classifications
├── test_data.csv             # Sample input file
```

---

## 🤝 Contributing

This project is currently under active solo development. Contributions, ideas, and issue reports are welcome!

---

## 📝 License

MIT License. See `LICENSE` file.

---

## 📬 Contact

Built by [Your Name] — [[your.email@example.com](mailto\:your.email@example.com)]\
Follow along at [your-website.com] or [@yourhandle]

---

Let me know if you'd like to update this `README.md` automatically with the current milestone list or GitHub links.

