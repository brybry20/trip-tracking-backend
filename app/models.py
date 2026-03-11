from app import db
from flask_login import UserMixin
from datetime import datetime

# ==================== MAIN DATABASE MODELS (BIND = 'main') ====================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __bind_key__ = 'main'  # Specify this is in main database
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    driver = db.relationship('Driver', backref='user', uselist=False, cascade='all, delete-orphan')

class Driver(db.Model):
    __tablename__ = 'drivers'
    __bind_key__ = 'main'  # Specify this is in main database
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    trips = db.relationship('Trip', backref='driver', lazy=True)

class Trip(db.Model):
    __tablename__ = 'trips'
    __bind_key__ = 'main'  # Specify this is in main database
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    helper = db.Column(db.String(100))
    dealer = db.Column(db.String(200), nullable=False)
    time_in = db.Column(db.String(10))
    time_out = db.Column(db.String(10))
    odometer = db.Column(db.Float)
    invoice_no = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== 2025 HISTORICAL DATABASE MODELS (BIND = 'historical') ====================
class Driver2025(db.Model):
    __tablename__ = 'drivers_2025'
    __bind_key__ = 'historical'  # This is in 2025 database
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    license_number = db.Column(db.String(50))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    trips = db.relationship('Trip2025', backref='driver', lazy=True)

class Trip2025(db.Model):
    __tablename__ = 'trips_2025'
    __bind_key__ = 'historical'  # This is in 2025 database
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers_2025.id'), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    helper = db.Column(db.String(100))
    dealer = db.Column(db.String(200), nullable=False)
    time_in = db.Column(db.String(10))
    time_out = db.Column(db.String(10))
    odometer = db.Column(db.Float)
    invoice_no = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)