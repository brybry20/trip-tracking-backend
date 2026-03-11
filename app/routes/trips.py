from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Trip, Driver

trips_bp = Blueprint('trips', __name__, url_prefix='/trips')

@trips_bp.route('', methods=['GET'])
@login_required
def get_trips():
    if current_user.role == 'admin':
        # Admin can see all trips
        trips = Trip.query.all()
    else:
        # Driver can only see their own trips
        driver = Driver.query.filter_by(user_id=current_user.id).first()
        if not driver:
            return jsonify([])
        trips = Trip.query.filter_by(driver_id=driver.id).all()
    
    trips_list = []
    for trip in trips:
        trips_list.append({
            'id': trip.id,
            'driver_id': trip.driver_id,
            'driver_name': trip.driver_name,
            'date': trip.date,
            'helper': trip.helper,
            'dealer': trip.dealer,
            'time_in': trip.time_in,
            'time_out': trip.time_out,
            'odometer': trip.odometer,
            'invoice_no': trip.invoice_no,
            'created_at': trip.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(trips_list)

@trips_bp.route('', methods=['POST'])
@login_required
def create_trip():
    if current_user.role != 'driver':
        return jsonify({'success': False, 'message': 'Only drivers can create trips'}), 403
    
    data = request.get_json()
    
    # Get driver ID
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    if not driver:
        return jsonify({'success': False, 'message': 'Driver profile not found'}), 404
    
    new_trip = Trip(
        driver_id=driver.id,
        driver_name=driver.full_name,  # ✅ Kukunin sa database, hindi sa request
        date=data['date'],
        helper=data['helper'],
        dealer=data['dealer'],
        time_in=data['time_in'],
        time_out=data['time_out'],
        odometer=int(data['odometer']),
        invoice_no=data['invoice_no']
    )
    
    db.session.add(new_trip)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Trip saved successfully'})