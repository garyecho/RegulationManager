r"""
修复数据库 - 在 Windows 上运行
用法: cd D:\Code\RegulationManager && python fix_db.py
"""
import sqlite3
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "regulation.db")
BACKUP = os.path.join(BASE, "data", "regulation_old_20260604_090944.db")
REAL_TABLES = ["categories", "tags", "documents", "document_tags",
               "document_versions", "recycle_bin", "usage_logs"]


def main():
    if not os.path.exists(BACKUP):
        print(f"Error: backup not found: {BACKUP}")
        return

    # Remove old db
    for suffix in ["", "-wal", "-shm"]:
        p = DB_PATH + suffix
        if os.path.exists(p):
            os.remove(p)
            print(f"Removed: {p}")

    # Read from backup
    src = sqlite3.connect(BACKUP)
    schemas = {}
    data = {}
    for table in REAL_TABLES:
        sql = src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if sql:
            schemas[table] = sql[0]
        rows = src.execute(f"SELECT * FROM [{table}]").fetchall()
        data[table] = rows
        print(f"  {table}: {len(rows)} rows")
    src.close()

    # Create new db with Windows native sqlite3
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")

    for table in REAL_TABLES:
        if table in schemas:
            db.execute(schemas[table])

    for table in REAL_TABLES:
        rows = data.get(table, [])
        if rows:
            ph = ",".join(["?"] * len(rows[0]))
            db.executemany(f"INSERT INTO [{table}] VALUES ({ph})", rows)

    db.commit()

    # Verify
    for table in REAL_TABLES:
        count = db.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        print(f"  {table}: {count} OK")

    result = db.execute("PRAGMA integrity_check").fetchone()
    print(f"\nIntegrity: {result[0]}")
    db.close()

    print("\nDone! Run: python main.py")


if __name__ == "__main__":
    main()
