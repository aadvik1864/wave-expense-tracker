import tempfile
import unittest
from datetime import date
from pathlib import Path

from storage import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp_dir.name) / "test.db")

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_first_run_has_no_transactions_or_preset_budgets(self):
        month = date.today().strftime("%Y-%m")
        self.assertGreaterEqual(len(self.store.categories()), 8)
        self.assertEqual(self.store.transactions(month=month), [])
        self.assertEqual(self.store.recurring_entries(), [])
        self.assertTrue(all(row["limit_cents"] == 0 for row in self.store.budget_rows(month)))

    def test_custom_entry_and_budget_persist(self):
        category_id = self.store.categories("expense")[0]["id"]
        self.store.add_transaction("Test purchase", 1234, "expense", category_id, date.today().isoformat())
        self.assertEqual(self.store.preference("last_category_expense"), str(category_id))
        self.store.save_budget(category_id, 50000)
        matching = self.store.transactions(search="Test purchase")
        self.assertEqual(matching[0]["amount_cents"], 1234)
        self.store.update_transaction(
            matching[0]["id"], "Renamed purchase", 2500, "expense", category_id,
            date.today().isoformat(), "updated note",
        )
        updated = self.store.transactions(search="Renamed purchase")[0]
        self.assertEqual(updated["amount_cents"], 2500)
        self.assertEqual(updated["note"], "updated note")
        budget = next(row for row in self.store.budget_rows(date.today().strftime("%Y-%m")) if row["id"] == category_id)
        self.assertEqual(budget["limit_cents"], 50000)

    def test_reopening_empty_store_keeps_it_empty(self):
        self.assertEqual(self.store.transactions(), [])
        self.store.close()
        self.store = Store(Path(self.temp_dir.name) / "test.db")
        self.assertEqual(self.store.transactions(), [])

    def test_removing_all_categories_is_not_undone_on_restart(self):
        for category in self.store.categories():
            self.assertTrue(self.store.delete_category(category["id"]))
        self.store.close()
        self.store = Store(Path(self.temp_dir.name) / "test.db")
        self.assertEqual(self.store.categories(), [])

    def test_recurring_entry_requires_confirmation_and_advances_monthly(self):
        category_id = self.store.categories("expense")[0]["id"]
        recurring_id = self.store.add_recurring(
            "Rent", 120000, "expense", category_id, "monthly", "2024-01-31"
        )
        self.assertEqual(self.store.transactions(), [])
        self.assertEqual(len(self.store.due_recurring(date(2024, 1, 31))), 1)
        self.store.post_recurring(recurring_id)
        self.assertEqual(self.store.transactions()[0]["happened_on"], "2024-01-31")
        self.assertEqual(self.store.recurring_entries()[0]["next_due"], "2024-02-29")
        self.store.post_recurring(recurring_id)
        self.assertEqual(self.store.recurring_entries()[0]["next_due"], "2024-03-31")

    def test_backup_restore_round_trip_includes_transactions_and_recurring(self):
        category_id = self.store.categories("expense")[0]["id"]
        self.store.add_transaction("Market", 1234, "expense", category_id, date.today().isoformat())
        self.store.save_budget(category_id, 50000)
        self.store.add_recurring("Rent", 120000, "expense", category_id, "monthly", "2026-12-01")
        backup = Path(self.temp_dir.name) / "wave.wavebackup"
        self.store.export_backup(backup)
        self.store.delete_transaction(self.store.transactions()[0]["id"])
        self.store.delete_recurring(self.store.recurring_entries()[0]["id"])
        self.store.restore_backup(backup)
        self.assertEqual(len(self.store.transactions()), 1)
        self.assertEqual(len(self.store.recurring_entries()), 1)
        restored_budget = next(row for row in self.store.budget_rows(date.today().strftime("%Y-%m")) if row["id"] == category_id)
        self.assertEqual(restored_budget["limit_cents"], 50000)


if __name__ == "__main__":
    unittest.main()
