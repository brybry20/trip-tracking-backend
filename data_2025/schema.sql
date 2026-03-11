-- Create tables for 2025 data
CREATE TABLE IF NOT EXISTS drivers_2025 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT,
    license_number TEXT,
    email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

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
);