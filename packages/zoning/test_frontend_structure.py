#!/usr/bin/env python3
"""
Test script to verify frontend data structure matches JavaScript expectations
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
                
            print('🔧 Frontend Data Structure Verification:')
            print('=' * 60)
            
            # Navigate to truck requirements (what frontend expects)
            if 'analysis_modules' in result:
                cf = result['analysis_modules']['collection_feasibility']
                tr = cf['truck_requirements']
                
                # Check dumpsite_logistics structure
                dl = tr.get('dumpsite_logistics', {})
                print('📍 Dumpsite Logistics Fields:')
                print(f'   ✅ chunga_dumpsite_distance_km: {dl.get("chunga_dumpsite_distance_km", "MISSING")}')
                print(f'   ✅ round_trip_distance_km: {dl.get("round_trip_distance_km", "MISSING")}')
                print(f'   ✅ fuel_price_usd_per_liter: {dl.get("fuel_price_usd_per_liter", "MISSING")}')
                print(f'   ✅ franchise_cost_kwacha_per_tonne: {dl.get("franchise_cost_kwacha_per_tonne", "MISSING")}')
                
                # Check recommended solution structure
                rs = tr.get('recommended_solution', {})
                print('\n🎯 Recommended Solution Fields:')
                print(f'   ✅ monthly_cost: ${rs.get("monthly_cost", "MISSING")}')
                
                # Check 10-tonne truck structure
                truck_10 = tr.get('truck_10_tonne', {})
                print('\n🚛 10-Tonne Truck Fields:')
                print(f'   ✅ monthly_cost: ${truck_10.get("monthly_cost", "MISSING")}')
                print(f'   ✅ monthly_costs.total: ${truck_10.get("monthly_costs", {}).get("total", "MISSING")}')
                
                # Check 20-tonne truck structure  
                truck_20 = tr.get('truck_20_tonne', {})
                print('\n🚚 20-Tonne Truck Fields:')
                print(f'   ✅ monthly_cost: ${truck_20.get("monthly_cost", "MISSING")}')
                print(f'   ✅ monthly_costs.total: ${truck_20.get("monthly_costs", {}).get("total", "MISSING")}')
                
                # Verify all expected fields exist
                print('\n✅ Frontend Compatibility Check:')
                missing_fields = []
                
                if not dl.get('chunga_dumpsite_distance_km'):
                    missing_fields.append('dumpsite_logistics.chunga_dumpsite_distance_km')
                if not rs.get('monthly_cost'):
                    missing_fields.append('recommended_solution.monthly_cost')
                if not truck_10.get('monthly_cost'):
                    missing_fields.append('truck_10_tonne.monthly_cost')
                if not truck_20.get('monthly_cost'):
                    missing_fields.append('truck_20_tonne.monthly_cost')
                
                if missing_fields:
                    print('   ❌ Missing fields for frontend:')
                    for field in missing_fields:
                        print(f'     - {field}')
                else:
                    print('   ✅ All frontend fields present!')
                    print('   ✅ Frontend should now display non-zero values')
                
        except Exception as e:
            print(f'❌ Frontend structure test failed: {str(e)}')
            import traceback
            traceback.print_exc()