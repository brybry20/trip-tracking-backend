import sqlite3

# Connect to database
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

try:
    # I-check muna kung anong klaseng column ang time_out
    cursor.execute("PRAGMA table_info(trips)")
    columns = cursor.fetchall()
    
    for col in columns:
        if col[1] == 'time_out':
            print(f"Current time_out definition: {col}")
            break
    
    # I-update ang time_out para maging nullable
    # Sa SQLite, kailangan nating i-recreate ang table para baguhin ang constraint
    
    # I-save muna ang existing data
    cursor.execute('''
        CREATE TABLE trips_backup AS SELECT * FROM trips
    ''')
    
    # I-drop ang old table
    cursor.execute('DROP TABLE trips')
    
    # I-recreate ang table na may nullable time_out
    cursor.execute('''
        CREATE TABLE trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            driver_name TEXT NOT NULL,
            date TEXT NOT NULL,
            helper TEXT,
            dealer TEXT NOT NULL,
            time_in TEXT,
            time_out TEXT,
            odometer FLOAT,
            invoice_no TEXT,
            amount FLOAT DEFAULT 0,
            location_lat FLOAT,
            location_lng FLOAT,
            location_accuracy FLOAT,
            location_timestamp TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
    ''')
    
    # I-restore ang data
    cursor.execute('''
        INSERT INTO trips 
        (id, driver_id, driver_name, date, helper, dealer, time_in, time_out, 
         odometer, invoice_no, amount, location_lat, location_lng, 
         location_accuracy, location_timestamp, created_at)
        SELECT 
            id, driver_id, driver_name, date, helper, dealer, time_in, time_out,
            odometer, invoice_no, amount, location_lat, location_lng,
            location_accuracy, location_timestamp, created_at
        FROM trips_backup
    ''')
    
    # I-drop ang backup
    cursor.execute('DROP TABLE trips_backup')
    
    print("✅ 'time_out' column updated to be nullable!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

conn.commit()
conn.close()