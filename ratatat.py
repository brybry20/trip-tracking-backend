# migrate_db.py
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def migrate_trips_table():
    """Add new columns to trips table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get database inspector
            inspector = db.inspect(db.engine)
            
            # Check if trips table exists
            if 'trips' not in inspector.get_table_names():
                print("❌ Trips table doesn't exist yet. Create tables first.")
                return
            
            # Get existing columns
            columns = [col['name'] for col in inspector.get_columns('trips')]
            print(f"Existing columns: {columns}")
            
            # Add missing columns
            changes_made = False
            
            if 'time_departure' not in columns:
                print("Adding time_departure column...")
                db.session.execute(text('ALTER TABLE trips ADD COLUMN time_departure VARCHAR(10)'))
                changes_made = True
                
            if 'time_arrival' not in columns:
                print("Adding time_arrival column...")
                db.session.execute(text('ALTER TABLE trips ADD COLUMN time_arrival VARCHAR(10)'))
                changes_made = True
                
            if 'time_unload_end' not in columns:
                print("Adding time_unload_end column...")
                db.session.execute(text('ALTER TABLE trips ADD COLUMN time_unload_end VARCHAR(10)'))
                changes_made = True
                
            if 'is_completed' not in columns:
                print("Adding is_completed column...")
                db.session.execute(text('ALTER TABLE trips ADD COLUMN is_completed BOOLEAN DEFAULT 0'))
                changes_made = True
            
            if changes_made:
                db.session.commit()
                print("✅ Migration completed successfully!")
                
                # Verify the columns were added
                inspector = db.inspect(db.engine)
                updated_columns = [col['name'] for col in inspector.get_columns('trips')]
                print(f"Updated columns: {updated_columns}")
            else:
                print("✅ All columns already exist. No changes needed.")
                
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            db.session.rollback()

def migrate_historical_tables():
    """Add new columns to historical trips_2025 table"""
    app = create_app()
    
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            
            # Check if trips_2025 table exists
            if 'trips_2025' not in inspector.get_table_names():
                print("⚠️ trips_2025 table doesn't exist yet. Skipping...")
                return
            
            # Get existing columns
            columns = [col['name'] for col in inspector.get_columns('trips_2025')]
            
            # Add missing columns
            changes_made = False
            
            if 'time_departure' not in columns:
                print("Adding time_departure to trips_2025...")
                db.session.execute(text('ALTER TABLE trips_2025 ADD COLUMN time_departure VARCHAR(10)'))
                changes_made = True
                
            if 'time_arrival' not in columns:
                print("Adding time_arrival to trips_2025...")
                db.session.execute(text('ALTER TABLE trips_2025 ADD COLUMN time_arrival VARCHAR(10)'))
                changes_made = True
                
            if 'time_unload_end' not in columns:
                print("Adding time_unload_end to trips_2025...")
                db.session.execute(text('ALTER TABLE trips_2025 ADD COLUMN time_unload_end VARCHAR(10)'))
                changes_made = True
                
            if 'is_completed' not in columns:
                print("Adding is_completed to trips_2025...")
                db.session.execute(text('ALTER TABLE trips_2025 ADD COLUMN is_completed BOOLEAN DEFAULT 0'))
                changes_made = True
            
            if changes_made:
                db.session.commit()
                print("✅ Historical tables migration completed!")
            else:
                print("✅ Historical tables already have all columns.")
                
        except Exception as e:
            print(f"❌ Error during historical migration: {str(e)}")
            db.session.rollback()

def create_all_tables():
    """Create all tables if they don't exist"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating all tables...")
            db.create_all()
            print("✅ All tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")

if __name__ == '__main__':
    print("=== Database Migration Tool ===\n")
    
    # First, create tables if they don't exist
    create_all_tables()
    
    # Then migrate existing tables
    print("\n=== Migrating trips table ===")
    migrate_trips_table()
    
    print("\n=== Migrating historical tables ===")
    migrate_historical_tables()
    
    print("\n✅ Migration complete!")