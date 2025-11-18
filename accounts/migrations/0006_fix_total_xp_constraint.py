from django.db import migrations, models

def fix_total_xp_constraint(apps, schema_editor):
    """Fix the total_xp constraint to allow zero or positive values"""
    # Get the current table name
    db_table = 'accounts_studentprofile'
    
    # Get the current table definition
    with schema_editor.connection.cursor() as cursor:
        # Get the CREATE TABLE statement
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{db_table}'")
        create_table_sql = cursor.fetchone()[0]
        
        # Modify the CREATE TABLE statement to remove any CHECK constraints on total_xp
        create_table_sql = create_table_sql.replace('"total_xp" integer NOT NULL', '"total_xp" integer NOT NULL DEFAULT 0')
        create_table_sql = create_table_sql.replace('CHECK ("total_xp" >= 0)', '')  # Remove CHECK constraint if exists
        
        # Create a temporary table with the new definition
        temp_table = f"{db_table}_new"
        create_temp_sql = create_table_sql.replace(f'CREATE TABLE "{db_table}"', f'CREATE TABLE "{temp_table}"')
        
        # Create the new table
        cursor.execute(create_temp_sql)
        
        # Copy data to the new table
        cursor.execute(f'INSERT INTO "{temp_table}" SELECT * FROM "{db_table}"')
        
        # Drop the old table
        cursor.execute(f'DROP TABLE "{db_table}"')
        
        # Rename the new table to the original name
        cursor.execute(f'ALTER TABLE "{temp_table}" RENAME TO "{db_table}"')
        
        # Recreate indexes
        cursor.execute(f'CREATE INDEX IF NOT EXISTS "accounts_studentprofile_user_id_idx" ON "{db_table}" ("user_id")')
        cursor.execute(f'CREATE INDEX IF NOT EXISTS "accounts_studentprofile_level_idx" ON "{db_table}" ("level")')

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_customuser_avatar'),  # Migrasi terakhir yang ada
    ]

    operations = [
        migrations.RunPython(fix_total_xp_constraint, migrations.RunPython.noop, atomic=False),
    ]
