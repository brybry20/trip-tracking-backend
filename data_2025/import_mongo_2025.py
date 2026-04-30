import os
import csv
import mongoengine as me
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

MONGO_URI = os.environ.get('MONGO_URI')

if not MONGO_URI:
    print("❌ MONGO_URI not found in .env")
    exit(1)

# Connect to MongoDB
print(f"Connecting to MongoDB...")
me.connect(host=MONGO_URI)

# Define models (same as in app/models.py to ensure compatibility)
class Driver2025(me.Document):
    meta = {'collection': 'drivers_2025'}
    full_name = me.StringField(required=True)
    phone = me.StringField()
    license_number = me.StringField()
    email = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)

class Trip2025(me.Document):
    meta = {'collection': 'trips_2025'}
    driver_name = me.StringField(required=True)
    date = me.StringField(required=True)
    helper = me.StringField()
    dealer = me.StringField(required=True)
    time_in = me.StringField()
    time_out = me.StringField()
    is_completed = me.BooleanField(default=False)
    odometer = me.FloatField()
    invoice_no = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)

def clean_float(value):
    if not value or value.strip() == 'N/A' or value.strip() == '':
        return 0.0
    try:
        # Handle cases like "6853.0" or "N/A"
        return float(value.replace(',', '').strip())
    except ValueError:
        return 0.0

def import_data():
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'trips_data.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found at {csv_path}")
        return

    print(f"Reading data from {csv_path}...")
    
    trips_to_insert = []
    drivers_set = set()
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('DATE') or not row.get('DRIVER'):
                continue
                
            driver_name = row['DRIVER'].strip().upper()
            drivers_set.add(driver_name)
            
            trip = Trip2025(
                date=row['DATE'].strip(),
                driver_name=driver_name,
                helper=row['HELPER'].strip() if row.get('HELPER') else None,
                time_in=row['IN'].strip() if row.get('IN') else None,
                time_out=row['OUT'].strip() if row.get('OUT') else None,
                odometer=clean_float(row['ODOMETER READING']),
                invoice_no=row['NO. INVOICE/S'].strip() if row.get('NO. INVOICE/S') else None,
                dealer=row['DEALER'].strip() if row.get('DEALER') else "UNKNOWN",
                is_completed=True # Assuming historical data is completed
            )
            trips_to_insert.append(trip)

    print(f"Found {len(trips_to_insert)} trips and {len(drivers_set)} unique drivers.")
    
    # Clear existing data if any (optional, but usually safer for a clean import)
    # Trip2025.objects.delete()
    # Driver2025.objects.delete()

    # Import Drivers
    print("Importing drivers...")
    existing_drivers = {d.full_name for d in Driver2025.objects.all()}
    new_drivers_count = 0
    for driver_name in drivers_set:
        if driver_name not in existing_drivers:
            Driver2025(full_name=driver_name).save()
            new_drivers_count += 1
    print(f"✅ Added {new_drivers_count} new drivers.")

    # Import Trips
    print("Importing trips...")
    # Use bulk insert for better performance
    if trips_to_insert:
        Trip2025.objects.insert(trips_to_insert)
    
    print(f"✅ Successfully imported {len(trips_to_insert)} trips into MongoDB!")

if __name__ == '__main__':
    start_time = datetime.now()
    import_data()
    end_time = datetime.now()
    print(f"Total time taken: {end_time - start_time}")
