from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Trip2025, Driver2025
from sqlalchemy import func

trips2025_bp = Blueprint('trips2025', __name__, url_prefix='/api/2025')

# ========== GET ALL TRIPS ==========
@trips2025_bp.route('/trips', methods=['GET'])
@login_required
def get_trips_2025():
    """Get trips from 2025 database"""
    try:
        if current_user.role == 'admin':
            # Admin can see all trips
            trips = Trip2025.query.all()
        else:
            # Driver can only see their trips (convert username to uppercase for matching)
            driver_upper = current_user.username.upper()
            trips = Trip2025.query.filter_by(driver_name=driver_upper).all()
        
        trips_list = []
        for trip in trips:
            trips_list.append({
                'id': trip.id,
                'date': trip.date,
                'driver_name': trip.driver_name,
                'helper': trip.helper,
                'dealer': trip.dealer,
                'time_in': trip.time_in,
                'time_out': trip.time_out,
                'odometer': trip.odometer,
                'invoice_no': trip.invoice_no
            })
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'count': len(trips_list),
            'trips': trips_list
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500


# ========== GET ALL DRIVERS ==========
@trips2025_bp.route('/drivers', methods=['GET'])
@login_required
def get_drivers_2025():
    """Get drivers from 2025 database"""
    try:
        drivers = Driver2025.query.all()
        drivers_list = []
        for driver in drivers:
            drivers_list.append({
                'id': driver.id,
                'full_name': driver.full_name,
                'phone': driver.phone,
                'license_number': driver.license_number,
                'email': driver.email,
                'trip_count': len(driver.trips)
            })
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'count': len(drivers_list),
            'drivers': drivers_list
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500


# ========== GET STATISTICS ==========
@trips2025_bp.route('/stats', methods=['GET'])
@login_required
def get_stats_2025():
    """Get statistics from 2025 database"""
    try:
        total_trips = Trip2025.query.count()
        total_drivers = Driver2025.query.count()
        
        # Top drivers
        top_drivers = db.session.query(
            Trip2025.driver_name, 
            func.count(Trip2025.id).label('trip_count')
        ).group_by(Trip2025.driver_name).order_by(func.desc('trip_count')).limit(5).all()
        
        # Top dealers
        top_dealers = db.session.query(
            Trip2025.dealer, 
            func.count(Trip2025.id).label('trip_count')
        ).group_by(Trip2025.dealer).order_by(func.desc('trip_count')).limit(5).all()
        
        # Total kilometers
        total_km = db.session.query(func.sum(Trip2025.odometer)).scalar() or 0
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'total_trips': total_trips,
            'total_drivers': total_drivers,
            'total_km': total_km,
            'top_drivers': [{'name': d[0], 'count': d[1]} for d in top_drivers],
            'top_dealers': [{'name': d[0], 'count': d[1]} for d in top_dealers]
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500


# ========== SEARCH TRIPS ==========
@trips2025_bp.route('/search', methods=['GET'])
@login_required
def search_trips_2025():
    """Search trips in 2025 database"""
    try:
        driver = request.args.get('driver', '')
        dealer = request.args.get('dealer', '')
        date_from = request.args.get('from', '')
        date_to = request.args.get('to', '')
        
        query = Trip2025.query
        
        if driver:
            query = query.filter(Trip2025.driver_name.contains(driver.upper()))
        if dealer:
            query = query.filter(Trip2025.dealer.contains(dealer))
        if date_from:
            query = query.filter(Trip2025.date >= date_from)
        if date_to:
            query = query.filter(Trip2025.date <= date_to)
        
        # Limit to 100 results for performance
        trips = query.limit(100).all()
        
        trips_list = []
        for trip in trips:
            trips_list.append({
                'id': trip.id,
                'date': trip.date,
                'driver_name': trip.driver_name,
                'dealer': trip.dealer,
                'helper': trip.helper,
                'time_in': trip.time_in,
                'time_out': trip.time_out,
                'odometer': trip.odometer,
                'invoice_no': trip.invoice_no
            })
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'count': len(trips_list),
            'trips': trips_list
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500


# ========== GET TRIPS BY DRIVER ==========
@trips2025_bp.route('/drivers/<string:driver_name>/trips', methods=['GET'])
@login_required
def get_driver_trips_2025(driver_name):
    """Get trips for a specific driver from 2025 database"""
    try:
        trips = Trip2025.query.filter_by(driver_name=driver_name.upper()).all()
        
        trips_list = []
        for trip in trips:
            trips_list.append({
                'id': trip.id,
                'date': trip.date,
                'helper': trip.helper,
                'dealer': trip.dealer,
                'time_in': trip.time_in,
                'time_out': trip.time_out,
                'odometer': trip.odometer,
                'invoice_no': trip.invoice_no
            })
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'driver': driver_name,
            'count': len(trips_list),
            'trips': trips_list
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500


# ========== GET DAILY SUMMARY ==========
@trips2025_bp.route('/summary/daily', methods=['GET'])
@login_required
def get_daily_summary():
    """Get daily trip summary from 2025 database"""
    try:
        results = db.session.query(
            Trip2025.date,
            func.count(Trip2025.id).label('trip_count'),
            func.sum(Trip2025.odometer).label('total_km')
        ).group_by(Trip2025.date).order_by(Trip2025.date.desc()).limit(30).all()
        
        summary = []
        for r in results:
            summary.append({
                'date': r.date,
                'trip_count': r.trip_count,
                'total_km': float(r.total_km) if r.total_km else 0
            })
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500