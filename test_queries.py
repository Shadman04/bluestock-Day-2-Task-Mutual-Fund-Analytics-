import sqlite3
import re
from pathlib import Path

db = sqlite3.connect("bluestock_mf.db")
lines = Path("queries.sql").read_text(encoding="utf-8-sig").splitlines()

queries = {}
current = None

for line in lines:
    match = re.match(r"^\s*--\s*(\d+)\.\s*(.*)$", line)

    if match:
        current = int(match.group(1))
        queries[current] = []
        continue

    if current is not None:
        if line.strip().startswith("--"):
            continue
        queries[current].append(line)

passed = 0
failed = 0

print("\n========== SQL QUERY TEST REPORT ==========\n")

for number in sorted(queries):
    query = "\n".join(queries[number]).strip()

    if not query:
        print(f"Query {number}: SKIPPED - Empty query")
        failed += 1
        continue

    try:
        cursor = db.execute(query)
        rows = cursor.fetchall()
        print(f"Query {number}: PASS | {len(rows)} rows")
        passed += 1
    except Exception as error:
        print(f"Query {number}: FAIL | {error}")
        failed += 1

print("\n========== FINAL SUMMARY ==========")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total: {passed + failed}")

db.close()
