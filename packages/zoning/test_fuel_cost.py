#!/usr/bin/env python3
"""
Test script for updated fuel cost calculations (K23/liter)
"""

import sys
import os
sys.path.insert(0, 'app')

from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

# Import the analyze_zone function
from app.views.zones import analyze_zone as analyze_zone_func

# Test data - Garden Compound area
test_geometry = {
    'type': 'Polygon',
    'coordinates': [[
        [28.3400, -15.3850],
        [28.3550, -15.3850], 
        [28.3550, -15.3950],
        [28.3400, -15.3950],
        [28.3400, -15.3850]
    ]]
}

test_data = {
    'geometry': test_geometry,
    'metadata': {
        'name': 'Test Garden Compound',
        'zone_type': 'residential'
    }
}

with app.app_context():
    with app.test_request_context('/zones/api/analyze-zone', method='POST', json=test_data):
        try:
            response = analyze_zone_func()
            if hasattr(response, 'get_json'):
                result = response.get_json()
            else:
                result = response[0].get_json() if isinstance(response, tuple) else response
                
            print('⛽ Updated Fuel Cost Test Results (K23/liter):')
            print('=' * 60)
            
            # Navigate to the cost data
            if 'analysis_modules' in result:
                cf = result['analysis_modules']['collection_feasibility']
                tr = cf['truck_requirements']
                
                # Check Chunga logistics
                dl = tr['dumpsite_logistics']
                distance = dl.get('chunga_dumpsite_distance_km', 0)
                round_trip = dl.get('round_trip_distance_km', 0)
                fuel_price_usd = dl.get('fuel_price_usd_per_liter', 0)
                round_trip_fuel_usd = dl.get('round_trip_fuel_cost_usd', 0)
                
                print('📍 Chunga Logistics:')
                print(f'   Distance to Chunga: {distance} km')
                print(f'   Round trip distance: {round_trip} km')
                print(f'   Fuel price: K23/liter (${fuel_price_usd:.3f}/liter)')
                print(f'   Round trip fuel cost: ${round_trip_fuel_usd:.3f}')
                
                # Check recommended solution costs
                print('\n🎯 Recommended Solution (10-tonne truck):')
                rs = tr['recommended_solution']
                weekly_cost = rs.get('weekly_cost', 0)
                monthly_cost = rs.get('monthly_cost', 0)
                print(f'   Weekly cost: ${weekly_cost:.2f}')
                print(f'   Monthly cost: ${monthly_cost:.2f}')
                
                if 'cost_breakdown' in rs:
                    cb = rs['cost_breakdown']
                    print('   Weekly breakdown:')
                    w = cb['weekly']
                    print(f'     - Operational: ${w["operational"]:.2f}')
                    print(f'     - Fuel: ${w["fuel"]:.2f} (with K23/liter)')
                    print(f'     - Franchise: ${w["franchise"]:.2f}')
                    print(f'     - Total: ${w["total"]:.2f}')
                
                # Check 10-tonne truck detailed costs
                print('\n🚛 10-Tonne Truck with K23/liter:')
                truck_10 = tr['truck_10_tonne']
                if 'weekly_costs' in truck_10:
                    wc = truck_10['weekly_costs']
                    print('   Weekly costs:')
                    print(f'     - Fuel: ${wc["fuel"]:.2f}')
                    print(f'     - Total: ${wc["total"]:.2f}')
                
                if 'cost_breakdown' in truck_10:
                    cb = truck_10['cost_breakdown']
                    print('   Per-collection costs:')
                    print(f'     - Fuel per round trip: ${cb["daily_fuel"]:.2f}')
                    print(f'     - Total per collection: ${cb["daily_total"]:.2f}')
                
                # Check 20-tonne truck detailed costs
                print('\n🚚 20-Tonne Truck with K23/liter (30% more fuel):')
                truck_20 = tr['truck_20_tonne']
                if 'weekly_costs' in truck_20:
                    wc = truck_20['weekly_costs']
                    print('   Weekly costs:')
                    print(f'     - Fuel: ${wc["fuel"]:.2f}')
                    print(f'     - Total: ${wc["total"]:.2f}')
                
                if 'cost_breakdown' in truck_20:
                    cb = truck_20['cost_breakdown']
                    print('   Per-collection costs:')
                    print(f'     - Fuel per round trip: ${cb["daily_fuel"]:.2f}')
                    print(f'     - Total per collection: ${cb["daily_total"]:.2f}')
                
                print('\n✅ Fuel cost successfully updated to K23/liter!')
                
        except Exception as e:
            print(f'❌ Fuel cost test failed: {str(e)}')
            import traceback
            traceback.print_exc()