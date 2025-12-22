import sqlite3

conn = sqlite3.connect('complaints.db')
cursor = conn.cursor()

# Get count
cursor.execute("SELECT COUNT(*) FROM complaints;")
count = cursor.fetchone()[0]
print(f"✅ Total complaints in database: {count}")

# Get schema
cursor.execute("PRAGMA table_info(complaints);")
schema = cursor.fetchall()
print("\n📊 Database Schema:")
for col in schema:
    print(f"   - {col[1]} ({col[2]})")

# Get data
if count > 0:
    cursor.execute("SELECT id, complaint_text, category, priority, sentiment, response, solution, action FROM complaints ORDER BY created_at DESC LIMIT 1;")
    comp = cursor.fetchone()
    if comp:
        print(f"\n📋 Latest Complaint:")
        print(f"   ID: {comp[0]}")
        print(f"   Text: {comp[1]}")
        print(f"   Category: {comp[2]}")
        print(f"   Priority: {comp[3]}")
        print(f"   Sentiment: {comp[4]}")
        print(f"   Response: {comp[5][:50]}..." if len(str(comp[5])) > 50 else f"   Response: {comp[5]}")
        print(f"   Solution: {comp[6][:50]}..." if len(str(comp[6])) > 50 else f"   Solution: {comp[6]}")
        print(f"   Action: {comp[7]}")

conn.close()
