import sqlite3
import tempfile
import unittest
from pathlib import Path

from voyager_database import (
    DATABASE_PATH,
    delete_record,
    get_columns,
    get_records,
    get_tables,
    insert_record,
    update_record,
)


class VoyagerDatabaseTests(unittest.TestCase):
    def test_default_database_contains_voyager_tables(self) -> None:
        self.assertTrue(DATABASE_PATH.is_file())
        self.assertEqual(
            get_tables(),
            [
                "FormulaNumber",
                "ProjectData",
                "VoyagerInfo_Component",
                "VoyagerInfo_ElementSymbols",
            ],
        )

    def test_records_can_be_created_read_updated_and_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "test.sqlite3"
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    'CREATE TABLE "Element" ('
                    '"ElementID" INTEGER PRIMARY KEY AUTOINCREMENT, '
                    '"Symbol" TEXT NOT NULL, "Name" TEXT, "Metallic?" TEXT)'
                )

            columns = get_columns("Element", database_path)
            self.assertEqual(
                [column["name"] for column in columns],
                ["ElementID", "Symbol", "Name", "Metallic?"],
            )

            record_id = insert_record(
                "Element",
                {"Symbol": "Xx", "Name": "Example", "Metallic?": "No"},
                database_path,
            )
            self.assertEqual(
                get_records("Element", database_path),
                [
                    {
                        "ElementID": record_id,
                        "Symbol": "Xx",
                        "Name": "Example",
                        "Metallic?": "No",
                    }
                ],
            )

            key = {"ElementID": record_id}
            self.assertEqual(
                update_record("Element", key, {"Name": "Updated"}, database_path),
                1,
            )
            self.assertEqual(get_records("Element", database_path)[0]["Name"], "Updated")
            self.assertEqual(delete_record("Element", key, database_path), 1)
            self.assertEqual(get_records("Element", database_path), [])

    def test_unknown_tables_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown table"):
            get_columns("missing_table", DATABASE_PATH)


if __name__ == "__main__":
    unittest.main()