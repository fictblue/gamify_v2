import sqlite3
import os

# Connect to the database
db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  {table[0]}")

# Check StudentProfile table structure
print("\nStudentProfile table structure:")
cursor.execute("PRAGMA table_info(accounts_studentprofile);")
columns = cursor.fetchall()
for column in columns:
    print(f"  {column[1]} ({column[2]}) - {column[3]}")

conn.close()
