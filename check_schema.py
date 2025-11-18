import sqlite3
import os

def check_schema():
    db_path = os.path.join('db.sqlite3')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the table info
    cursor.execute("PRAGMA table_info(accounts_studentprofile)")
    columns = cursor.fetchall()
    print("\nTable Structure:")
    for col in columns:
        print(f"- {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] == 1 else ''}")
    
    # Get the CREATE TABLE statement
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts_studentprofile'")
    create_table_sql = cursor.fetchone()[0]
    print("\nCREATE TABLE statement:")
    print(create_table_sql)
    
    # Check if there are any CHECK constraints on total_xp
    if 'CHECK ("total_xp" >= 0)' in create_table_sql:
        print("\nWARNING: CHECK constraint still exists on total_xp")
    else:
        print("\nSUCCESS: No CHECK constraint on total_xp")
    
    conn.close()

if __name__ == "__main__":
    check_schema()
