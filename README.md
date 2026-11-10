# Wave: local expense tracker

A native desktop expense tracker built in Python with PySide6. Track expenses and income, organize them into categories, and set monthly category budgets. All records stay in a local SQLite database; the app has no bank connection, sign-in, or network dependency.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The database is created at `~/.local/share/wave/expenses.db` (or `$XDG_DATA_HOME/wave/expenses.db`). Wave starts with **no transactions and no preset budgets**. It includes only a set of common category names so you can add your first entry immediately. Set `WAVE_DB_PATH` to choose a different database location. Any earlier Tide database is left untouched.

## Features

- Overview with monthly spending, income, cash-flow difference, spending rhythm, and budget progress
- Overview charts with category spending shares and weekly expense bars
- Light and dark forest-green themes, with your choice remembered on this device
- Amounts displayed in Indian rupees (₹) with Indian digit grouping. Existing amounts are not converted.
- Add, edit, and remove expense or income entries
- Quick entry with `Ctrl+N`; Wave remembers the last-used category by type
- Search and filter activity; export a CSV copy
- Create and rename expense/income categories
- Set and adjust monthly category budgets
- Budget pacing shows current progress and a month-end projection
- Weekly, monthly, or yearly reminders; recurring entries are added only after you confirm them
- Create and restore a full local backup from the **Data** menu
- Month-by-month navigation with local SQLite persistence

Due reminders appear in Wave while it is open; there are no background or OS notifications. Restoring a backup replaces the current Wave data after confirmation.

The interface and data layer are Python. Qt paints the chart, wave mark, and interaction states natively; there is no browser or React runtime.
