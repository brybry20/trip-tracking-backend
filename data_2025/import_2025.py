# fix_database.py
import sqlite3
import os

def fix_database():
    """Add new columns to SQLite database"""
    
    # Try to find the database file
    db_path = 'instance/app.db'
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Looking for database files...")
        
        # Search for .db files in the backend folder
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.db'):
                    db_path = os.path.join(root, file)
                    print(f"✅ Found: {db_path}")
                    break
        
        if not os.path.exists(db_path):
            print("\n❌ No database found. The app will create it when you run it.")
            print("   Please run the app first to create the database, then run this script.")
            return False
    
    print(f"\n📁 Using database: {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if trips table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trips'")
        if not cursor.fetchone():
            print("❌ Trips table doesn't exist yet.")
            print("   Please run the Flask app first to create the tables.")
            return False
        
        # Get existing columns in trips table
        cursor.execute("PRAGMA table_info(trips)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"\n📋 Existing columns in trips table:")
        print(f"   {', '.join(columns)}")
        
        # Add new columns if they don't exist
        changes_made = False
        
        if 'time_departure' not in columns:
            print("\n➕ Adding time_departure column...")
            cursor.execute("ALTER TABLE trips ADD COLUMN time_departure VARCHAR(10)")
            changes_made = True
            print("   ✅ Added time_departure")
        
        if 'time_arrival' not in columns:
            print("➕ Adding time_arrival column...")
            cursor.execute("ALTER TABLE trips ADD COLUMN time_arrival VARCHAR(10)")
            changes_made = True
            print("   ✅ Added time_arrival")
        
        if 'time_unload_end' not in columns:
            print("➕ Adding time_unload_end column...")
            cursor.execute("ALTER TABLE trips ADD COLUMN time_unload_end VARCHAR(10)")
            changes_made = True
            print("   ✅ Added time_unload_end")
        
        if 'is_completed' not in columns:
            print("➕ Adding is_completed column...")
            cursor.execute("ALTER TABLE trips ADD COLUMN is_completed BOOLEAN DEFAULT 0")
            changes_made = True
            print("   ✅ Added is_completed")
        
        # Commit changes
        if changes_made:
            conn.commit()
            print("\n" + "="*50)
            print("✅ DATABASE MIGRATION COMPLETED!")
            print("="*50)
            
            # Show updated columns
            cursor.execute("PRAGMA table_info(trips)")
            updated_columns = [column[1] for column in cursor.fetchall()]
            print(f"\n📋 Updated columns in trips table:")
            print(f"   {', '.join(updated_columns)}")
            
        else:
            print("\n" + "="*50)
            print("✅ All columns already exist! No changes needed.")
            print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()
        print("\n🔌 Database connection closed.")

def check_trips_table():
    """Check what columns exist in trips table"""
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(trips)")
        columns = cursor.fetchall()
        
        print("\n" + "="*50)
        print("📋 TRIPS TABLE STRUCTURE")
        print("="*50)
        for col in columns:
            print(f"   {col[1]:<20} {col[2]}")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("🔧 SQLITE DATABASE MIGRATION TOOL")
    print("="*60)
    
    # First, check current structure
    check_trips_table()
    
    # Then, fix the database
    print("\n")
    success = fix_database()
    
    if success:
        print("\n✅ You can now restart your Flask app and try creating trips again!")
    else:
        print("\n⚠️ Please run your Flask app first to create the database, then run this script again.")