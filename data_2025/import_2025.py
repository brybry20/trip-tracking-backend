import sqlite3
import csv
from datetime import datetime
import os

print("="*60)
print("🚚 2025 TRIP DATA IMPORT (WITH BLANK LINE HANDLING)")
print("="*60)

# Set the paths
csv_path = r'C:\Users\Bryan Batan\OneDrive\Desktop\Trip_Tracking_System\trips_data.csv'
db_path = r'C:\Users\Bryan Batan\OneDrive\Desktop\Trip_Tracking_System\data_2025\trips_2025.db'

# Check if CSV file exists
if not os.path.exists(csv_path):
    print(f"❌ ERROR: CSV file not found!")
    print(f"   Expected at: {csv_path}")
    exit()

print(f"✅ Found CSV file: {csv_path}")

# Delete existing database if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print("🗑️ Removed existing database")

# Create new database and connect
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
print("✅ Created new database: trips_2025.db")

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS drivers_2025 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT,
    license_number TEXT,
    email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS trips_2025 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id INTEGER NOT NULL,
    driver_name TEXT NOT NULL,
    date TEXT NOT NULL,
    helper TEXT,
    dealer TEXT NOT NULL,
    time_in TEXT,
    time_out TEXT,
    odometer REAL,
    invoice_no TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers_2025(id)
)
''')
print("✅ Created tables: drivers_2025 and trips_2025")

# Start import
print("\n📖 Reading CSV file...")
print("-"*50)

drivers_cache = {}
trips_count = 0
drivers_count = 0
error_count = 0
blank_lines = 0
line_errors = []

try:
    with open(csv_path, 'r', encoding='utf-8') as file:
        # Basahin lahat ng lines
        lines = file.readlines()
        
        # Hanapin kung saan ang header
        header_line = None
        data_start_line = 0
        
        for i, line in enumerate(lines):
            if 'DATE' in line.upper() and 'DRIVER' in line.upper():
                header_line = i
                data_start_line = i + 1
                break
        
        if header_line is None:
            print("❌ Could not find header line. Assuming first line is header.")
            data_start_line = 1
        else:
            print(f"✅ Found header at line {header_line + 1}")
        
        total_potential_lines = len(lines) - data_start_line
        print(f"Total lines after header: {total_potential_lines}")
        print("-"*50)
        
        # Process each line
        for line_num, line in enumerate(lines[data_start_line:], start=data_start_line + 1):
            # Remove whitespace
            line = line.strip()
            
            # Skip completely empty lines
            if not line:
                blank_lines += 1
                continue
            
            try:
                # Split by comma
                parts = line.split(',')
                
                # Check if this looks like a data line (should have at least 3 columns)
                if len(parts) < 3:
                    blank_lines += 1
                    continue
                
                # Make sure we have at least 8 columns, pad with empty strings if needed
                while len(parts) < 8:
                    parts.append('')
                
                # Extract data
                date = parts[0].strip()
                driver_name = parts[1].strip()
                helper = parts[2].strip() if len(parts) > 2 else ''
                time_in = parts[3].strip() if len(parts) > 3 else ''
                time_out = parts[4].strip() if len(parts) > 4 else ''
                odometer = parts[5].strip() if len(parts) > 5 else ''
                invoice_no = parts[6].strip() if len(parts) > 6 else ''
                dealer = parts[7].strip() if len(parts) > 7 else ''
                
                # Validate required fields
                if not date or not driver_name or not dealer:
                    line_errors.append(f"Line {line_num}: Missing required fields")
                    error_count += 1
                    continue
                
                # Clean up N/A values
                helper = None if helper in ['N/A', ''] else helper
                time_in = None if time_in in ['N/A', ''] else time_in
                time_out = None if time_out in ['N/A', ''] else time_out
                
                # Handle odometer
                if odometer in ['N/A', '']:
                    odometer = None
                else:
                    try:
                        # Remove any non-numeric characters except decimal point
                        odometer = ''.join(c for c in odometer if c.isdigit() or c == '.')
                        odometer = float(odometer) if odometer else None
                    except:
                        odometer = None
                
                invoice_no = None if invoice_no in ['N/A', ''] else invoice_no
                
                # Handle driver
                if driver_name not in drivers_cache:
                    # Check if driver exists in database
                    cursor.execute('SELECT id FROM drivers_2025 WHERE full_name = ?', (driver_name,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        drivers_cache[driver_name] = existing[0]
                    else:
                        # Insert new driver
                        cursor.execute('''
                            INSERT INTO drivers_2025 (full_name, phone, license_number, email, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            driver_name, 
                            'N/A', 
                            'N/A', 
                            f"{driver_name.lower().replace(' ', '_')}@email.com",
                            datetime.now()
                        ))
                        driver_id = cursor.lastrowid
                        drivers_cache[driver_name] = driver_id
                        drivers_count += 1
                        
                        if drivers_count <= 5:
                            print(f"  ✅ New driver: {driver_name}")
                        elif drivers_count == 6:
                            print("  ... (more drivers being added)")
                
                driver_id = drivers_cache[driver_name]
                
                # Insert trip
                cursor.execute('''
                    INSERT INTO trips_2025 
                    (driver_id, driver_name, date, helper, dealer, time_in, time_out, odometer, invoice_no, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    driver_id,
                    driver_name,
                    date,
                    helper,
                    dealer,
                    time_in,
                    time_out,
                    odometer,
                    invoice_no,
                    datetime.now()
                ))
                
                trips_count += 1
                
                # Show progress
                if trips_count % 50 == 0:
                    print(f"  📊 Progress: {trips_count} trips imported...")
                
            except Exception as e:
                line_errors.append(f"Line {line_num}: {str(e)[:50]}")
                error_count += 1
                continue
        
        # Save all changes
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ IMPORT COMPLETED!")
        print("="*60)
        print(f"   📊 Database: {db_path}")
        print(f"   👤 Drivers imported: {drivers_count}")
        print(f"   📦 Trips imported: {trips_count}")
        print(f"   📄 Blank lines skipped: {blank_lines}")
        print(f"   ⚠️ Errors: {error_count}")
        print("="*60)
        
        # Show sample data
        if trips_count > 0:
            print("\n📋 Sample of imported trips:")
            cursor.execute('''
                SELECT date, driver_name, dealer, time_in, time_out 
                FROM trips_2025 
                LIMIT 5
            ''')
            samples = cursor.fetchall()
            for i, sample in enumerate(samples, 1):
                print(f"   {i}. {sample[0]} | {sample[1]} | {sample[2]} | {sample[3]} | {sample[4]}")
        
        # Show errors if any
        if line_errors:
            print("\n⚠️ First 5 errors encountered:")
            for err in line_errors[:5]:
                print(f"   {err}")
            if len(line_errors) > 5:
                print(f"   ... and {len(line_errors)-5} more errors")
        
except Exception as e:
    print(f"\n❌ FATAL ERROR: {str(e)}")
    conn.rollback()
finally:
    conn.close()
    print("\n🔌 Database connection closed.")