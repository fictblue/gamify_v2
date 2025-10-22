import sqlite3
import os
from datetime import datetime

# Connect to the database
db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)

try:
    # Add created_at column
    conn.execute("ALTER TABLE accounts_studentprofile ADD COLUMN created_at DATETIME")

    # Add updated_at column
    conn.execute("ALTER TABLE accounts_studentprofile ADD COLUMN updated_at DATETIME")

    conn.commit()
    print("Successfully added created_at and updated_at columns to StudentProfile table")

except sqlite3.Error as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
