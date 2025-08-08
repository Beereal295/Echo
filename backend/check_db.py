import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "echo.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=== Agent Memories Table Schema ===")
cursor.execute("PRAGMA table_info(agent_memories)")
columns = cursor.fetchall()

for column in columns:
    print(f"{column[1]:25} {column[2]:15} {column[3]:15} {column[4]}")

print(f"\nTotal columns: {len(columns)}")

print("\n=== Recent Migrations ===")
cursor.execute("SELECT * FROM schema_version ORDER BY version DESC LIMIT 5")
migrations = cursor.fetchall()

for migration in migrations:
    print(f"Version {migration[0]}: {migration[2]} (Applied: {migration[1]})")

print("\n=== Sample Memory Record ===")
cursor.execute("SELECT * FROM agent_memories LIMIT 1")
memory = cursor.fetchone()
if memory:
    print(f"Found sample memory with {len(memory)} fields")
else:
    print("No memories found")

conn.close()