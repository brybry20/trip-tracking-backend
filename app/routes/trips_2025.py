from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import Trip2025, Driver2025
from mongoengine import Q

trips2025_bp = Blueprint('trips2025', __name__, url_prefix='/api/2025')

# ========== GET ALL TRIPS ==========
@trips2025_bp.route('/trips', methods=['GET'])
@login_required
def get_trips_2025():
    """Get trips from 2025 database"""
    try:
        if current_user.role == 'admin':
            trips = Trip2025.objects.all()
        else:
            driver_upper = current_user.username.upper()
            trips = Trip2025.objects(driver_name=driver_upper).all()
        
        trips_list = []
        for trip in trips:
            trips_list.append({
                'id': str(trip.id),
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

# ========== UPDATE TRIP (2025) ==========
@trips2025_bp.route('/trips/<string:trip_id>', methods=['PUT'])
@login_required
def update_trip_2025(trip_id):
    """Update a 2025 trip"""
    try:
        trip = Trip2025.objects(id=trip_id).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        # Check if the trip belongs to the current driver
        if current_user.role == 'driver':
            driver_upper = current_user.username.upper()
            if trip.driver_name != driver_upper:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update fields
        trip.date = data.get('date', trip.date)
        trip.helper = data.get('helper', trip.helper)
        trip.dealer = data.get('dealer', trip.dealer)
        trip.time_in = data.get('time_in', trip.time_in)
        trip.time_out = data.get('time_out', trip.time_out)
        trip.odometer = float(data.get('odometer', trip.odometer)) if data.get('odometer') else None
        trip.invoice_no = data.get('invoice_no', trip.invoice_no)
        
        trip.save()
        
        return jsonify({'success': True, 'message': 'Trip updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== DELETE TRIP (2025) ==========
@trips2025_bp.route('/trips/<string:trip_id>', methods=['DELETE'])
@login_required
def delete_trip_2025(trip_id):
    """Delete a 2025 trip"""
    try:
        trip = Trip2025.objects(id=trip_id).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
        
        # Check if the trip belongs to the current driver
        if current_user.role == 'driver':
            driver_upper = current_user.username.upper()
            if trip.driver_name != driver_upper:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        trip.delete()
        
        return jsonify({'success': True, 'message': 'Trip deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== GET ALL DRIVERS (2025) ==========
@trips2025_bp.route('/drivers', methods=['GET'])
@login_required
def get_drivers_2025():
    """Get drivers from 2025 database"""
    try:
        drivers = Driver2025.objects.all()
        drivers_list = []
        for driver in drivers:
            drivers_list.append({
                'id': str(driver.id),
                'full_name': driver.full_name,
                'phone': driver.phone,
                'license_number': driver.license_number,
                'email': driver.email
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
        total_trips = Trip2025.objects.count()
        total_drivers = Driver2025.objects.count()
        
        # Aggregation for top drivers
        top_drivers_pipe = [
            {"$group": {"_id": "$driver_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_drivers = list(Trip2025.objects.aggregate(top_drivers_pipe))
        
        # Aggregation for top dealers
        top_dealers_pipe = [
            {"$group": {"_id": "$dealer", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_dealers = list(Trip2025.objects.aggregate(top_dealers_pipe))
        
        total_km = Trip2025.objects.sum('odometer')
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'total_trips': total_trips,
            'total_drivers': total_drivers,
            'total_km': total_km,
            'top_drivers': [{'name': d['_id'], 'count': d['count']} for d in top_drivers],
            'top_dealers': [{'name': d['_id'], 'count': d['count']} for d in top_dealers]
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
        
        query = Q()
        
        if driver:
            query &= Q(driver_name__icontains=driver)
        if dealer:
            query &= Q(dealer__icontains=dealer)
        if date_from:
            query &= Q(date__gte=date_from)
        if date_to:
            query &= Q(date__lte=date_to)
        
        trips = Trip2025.objects(query).limit(100)
        
        trips_list = []
        for trip in trips:
            trips_list.append({
                'id': str(trip.id),
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
        trips = Trip2025.objects(driver_name=driver_name.upper()).all()
        
        trips_list = []
        for trip in trips:
            trips_list.append({
                'id': str(trip.id),
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
        # Aggregation for daily summary
        pipeline = [
            {"$group": {
                "_id": "$date", 
                "trip_count": {"$sum": 1},
                "total_km": {"$sum": "$odometer"}
            }},
            {"$sort": {"_id": -1}},
            {"$limit": 30}
        ]
        results = list(Trip2025.objects.aggregate(pipeline))
        
        summary = []
        for r in results:
            summary.append({
                'date': r['_id'],
                'trip_count': r['trip_count'],
                'total_km': float(r['total_km']) if r['total_km'] else 0
            })
        
        return jsonify({
            'success': True,
            'database': 'historical_2025',
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e), 'database': 'historical_2025'}), 500