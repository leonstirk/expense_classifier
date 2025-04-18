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

- **Transaction summaries over time**
    - Weekly and monthly grouping
    - Compare vs. rolling average (3m, 6m) or all-time
- **Category-level trends**
    - Grocery spend over time
    - Identify top categories per month
    - Visuals: line plots, bar charts, percent changes
- **Reclassification tools**
    - Click to change category on past transactions
    - View transactions by class (filterable table)
- **Clean visual summary UI**
    - Embed charts or summary tables below cards
    - Use tabs or collapsible panels for clarity
- **Save historical data across files (persist classification + metadata like date)**
- ** Handle date parsing + weekly/monthly grouping**
- **Add `matplotlib`/`tkinter-canvas` for simple charts**
- **CLI or GUI reclassification view (by class or vendor)**

### Phase 2: Automation

- **🔄 Data automation**
    - Daily or real-time bank transaction sync (e.g. email-to-CSV, scraping, API)
    - Automatically append new transactions to history
    - Alert when over weekly/fortnightly budget threshold
- **📈 Real-time insights**
    - Show “current week” progress vs budget
    - Forecast remaining discretionary funds

### Phase 3: Generalization & Distribution
- **🧭 User-friendly setup**
    - Generalize column mapping (user picks "date", "amount", etc.)
    - UI for setting ignored terms
   -  Clear instructions for different bank CSVs
- **📦 Packaging + Docs**
    - Clean repo structure
    - Markdown docs for setup, usage
    - Add sample data + screenshots
    - Write blog post (walkthrough + architecture)

### Phase 4: Web App Conversion
- **🔐 User platform**
    - Login/signup system
    - Upload CSVs securely
    - Store classification data per user
- **📊 Dashboards + Budgeting**
    - Interactive dashboards (weekly/monthly trends, progress bars)
    - Editable budgets
    - Alert system (email/SMS/web)
- **🛠 Tech stack**
    - Backend: FastAPI or Flask
    - Frontend: React or Svelte (with Plotly or Chart.js)
    - Auth: OAuth or custom
    - DB: PostgreSQL or Firebase
    - Hosting: Render, Heroku, or self-hosted

---

## 🗂 Roadmap

### 🔭 GitHub Project Board

Track development progress, features, and bugs: 🔗 [Project Board](https://github.com/leonstirk/expense-classifier/projects/1)

### 🎯 Milestones

- `v1.0` - Core desktop functionality: classification, summary, reclassification etc
- `v2.0` - Automation: weekly/monthly analysis, auto-import, real-time alerts
- `v3.0` - Generalisation & Distribution: documentation, etc.
- `v4.0` - Web app prototype, multi-user dashboard, hosted release.
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

Built by [Leon Stirk-Wang] — [[leon@stirkwang.com](mailto\:leon@stirkwang.com)]\
Follow along at [leonstirkwang.com] or [@die_flator_maus]

---
