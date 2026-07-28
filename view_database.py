import sqlite3

conn = sqlite3.connect("database/opportunities.db")

cursor = conn.cursor()

cursor.execute("""
SELECT
    id,
    source,
    title,
    opportunity_score
FROM opportunities
ORDER BY id DESC
LIMIT 20
""")

for row in cursor.fetchall():
    print(row)

conn.close()