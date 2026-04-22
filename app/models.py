from flask_login import UserMixin
from datetime import datetime
import mongoengine as me

# ==================== EMBEDDED MODELS ====================
class Invoice(me.EmbeddedDocument):
    invoice_no = me.StringField(required=True)
    amount = me.FloatField(default=0)
    created_at = me.DateTimeField(default=datetime.utcnow)

class Check(me.EmbeddedDocument):
    check_no = me.StringField(required=True)
    amount = me.FloatField(default=0)
    bank = me.StringField()
    account_no = me.StringField()
    check_date = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)

# ==================== MAIN DATABASE MODELS ====================
class User(UserMixin, me.Document):
    meta = {'collection': 'users'}
    
    username = me.StringField(required=True, unique=True)
    password_hash = me.StringField(required=True)
    role = me.StringField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)
    
    # Token management fields
    current_token = me.StringField()
    token_created_at = me.DateTimeField()
    last_active = me.DateTimeField(default=datetime.utcnow)

class Driver(me.Document):
    meta = {'collection': 'drivers'}
    
    user = me.ReferenceField(User, reverse_delete_rule=me.CASCADE)
    full_name = me.StringField(required=True)
    phone = me.StringField(required=True)
    license_number = me.StringField(required=True, unique=True)
    email = me.StringField(required=True, unique=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

class Trip(me.Document):
    meta = {'collection': 'trips'}
    
    driver = me.ReferenceField(Driver, reverse_delete_rule=me.CASCADE)
    driver_name = me.StringField(required=True)
    date = me.StringField(required=True)
    helper = me.StringField()
    dealer = me.StringField(required=True)
    
    # Time tracking fields
    time_departure = me.StringField()
    time_arrival = me.StringField()
    time_unload_end = me.StringField()
    
    # Odometer fields
    departure_odometer = me.FloatField()
    arrival_odometer = me.FloatField()
    
    # Flag
    is_completed = me.BooleanField(default=False)
    
    # Old odometer field (for backward compatibility)
    odometer = me.FloatField()
    
    invoice_no = me.StringField()
    amount = me.FloatField(default=0)
    
    # Location fields
    location_lat = me.FloatField()
    location_lng = me.FloatField()
    location_accuracy = me.FloatField()
    location_timestamp = me.StringField()
    
    arrival_location_lat = me.FloatField()
    arrival_location_lng = me.FloatField()
    arrival_location_accuracy = me.FloatField()
    arrival_location_timestamp = me.StringField()
    
    end_location_lat = me.FloatField()
    end_location_lng = me.FloatField()
    end_location_accuracy = me.FloatField()
    end_location_timestamp = me.StringField()
    
    created_at = me.DateTimeField(default=datetime.utcnow)
    
    # Embedded Relationships
    invoices = me.EmbeddedDocumentListField(Invoice)
    checks = me.EmbeddedDocumentListField(Check)

# ==================== 2025 HISTORICAL DATABASE MODELS ====================
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
    time_in = me.StringField() # maps from time_departure in SQL but used as time_in in historical routes
    time_out = me.StringField() # maps from time_unload_end
    is_completed = me.BooleanField(default=False)
    odometer = me.FloatField()
    invoice_no = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)