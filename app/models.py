from app import db
from flask_login import UserMixin
from datetime import datetime

# ==================== MAIN DATABASE MODELS ====================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __bind_key__ = 'main'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NEW: Token management fields
    current_token = db.Column(db.String(500), nullable=True)
    token_created_at = db.Column(db.DateTime, nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    driver = db.relationship('Driver', backref='user', uselist=False, cascade='all, delete-orphan')

class Driver(db.Model):
    __tablename__ = 'drivers'
    __bind_key__ = 'main'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    trips = db.relationship('Trip', backref='driver', lazy=True)

class Trip(db.Model):
    __tablename__ = 'trips'
    __bind_key__ = 'main'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    helper = db.Column(db.String(100))
    dealer = db.Column(db.String(200), nullable=False)
    
    # Time tracking fields
    time_departure = db.Column(db.String(10))
    time_arrival = db.Column(db.String(10))
    time_unload_end = db.Column(db.String(10))
    
    # NEW: Odometer fields
    departure_odometer = db.Column(db.Float)  # Odo bago umalis
    arrival_odometer = db.Column(db.Float)    # Odo pagdating
    # computed: distance = arrival_odometer - departure_odometer
    
    # Flag
    is_completed = db.Column(db.Boolean, default=False)
    
    # Old odometer field (for backward compatibility)
    odometer = db.Column(db.Float)
    
    invoice_no = db.Column(db.String(100))
    amount = db.Column(db.Float, default=0)
    
    # Location fields
    location_lat = db.Column(db.Float)
    location_lng = db.Column(db.Float)
    location_accuracy = db.Column(db.Float)
    location_timestamp = db.Column(db.String(30))
    
    arrival_location_lat = db.Column(db.Float)
    arrival_location_lng = db.Column(db.Float)
    arrival_location_accuracy = db.Column(db.Float)
    arrival_location_timestamp = db.Column(db.String(30))
    
    end_location_lat = db.Column(db.Float)
    end_location_lng = db.Column(db.Float)
    end_location_accuracy = db.Column(db.Float)
    end_location_timestamp = db.Column(db.String(30))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='trip', lazy=True, cascade='all, delete-orphan')
    checks = db.relationship('Check', backref='trip', lazy=True, cascade='all, delete-orphan')

class Invoice(db.Model):
    __tablename__ = 'invoices'
    __bind_key__ = 'main'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    invoice_no = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Check(db.Model):
    __tablename__ = 'checks'
    __bind_key__ = 'main'
    
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    check_no = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    bank = db.Column(db.String(100))
    account_no = db.Column(db.String(100))
    check_date = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== 2025 HISTORICAL DATABASE MODELS ====================
class Driver2025(db.Model):
    __tablename__ = 'drivers_2025'
    __bind_key__ = 'historical'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    license_number = db.Column(db.String(50))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    trips = db.relationship('Trip2025', backref='driver', lazy=True)

class Trip2025(db.Model):
    __tablename__ = 'trips_2025'
    __bind_key__ = 'historical'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers_2025.id'), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    helper = db.Column(db.String(100))
    dealer = db.Column(db.String(200), nullable=False)
    time_departure = db.Column(db.String(10))
    time_arrival = db.Column(db.String(10))
    time_unload_end = db.Column(db.String(10))
    is_completed = db.Column(db.Boolean, default=False)
    odometer = db.Column(db.Float)
    invoice_no = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)