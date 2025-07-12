#!/usr/bin/env python3
"""
Test script for revenue calculation in formal area (should get K150 rate)
"""

import sys
import os
sys.path.insert(0, 'app')

from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

# Import the analyze_zone function
from app.views.zones import analyze_zone as analyze_zone_func

# Test data - Lusaka CBD area (should be formal/commercial)
test_geometry = {
    'type': 'Polygon',
    'coordinates': [[
        [28.2800, -15.4150],
        [28.2900, -15.4150], 
        [28.2900, -15.4250],
        [28.2800, -15.4250],
        [28.2800, -15.4150]
    ]]
}

test_data = {
    'geometry': test_geometry,
    'metadata': {
        'name': 'Test Lusaka CBD',
        'zone_type': 'commercial'
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
                
            print('🏢 Formal Area Revenue Test (CBD)')
            print('=' * 50)
            
            # Check revenue projections
            if 'revenue_projections' in result:
                rp = result['revenue_projections']
                
                if rp.get('success'):
                    print('📊 Results:')
                    print(f'   Settlement Type: {rp.get("settlement_description", "Unknown")}')
                    print(f'   Settlement Classification: {rp.get("settlement_type", "Unknown")}')
                    print(f'   Rate per Building: K{rp.get("rate_per_building_kwacha", 0)}/month')
                    print(f'   Total Buildings: {rp.get("total_buildings", 0)}')
                    print(f'   Monthly Revenue: K{rp.get("realistic_monthly_revenue_kwacha", 0):,.0f}')
                    print(f'   Revenue Potential: {rp.get("revenue_potential", "unknown").upper()}')
                    
                    # Verify rate logic
                    rate = rp.get('rate_per_building_kwacha', 0)
                    settlement_type = rp.get('settlement_type', '')
                    
                    print(f'\n🎯 Rate Logic Test:')
                    print(f'   Settlement Type: {settlement_type}')
                    if rate == 150:
                        print('   ✅ Correct K150 rate for formal area')
                    elif rate == 30:
                        print('   ✅ Correct K30 rate for informal area')
                    elif rate == 90:
                        print('   ✅ Correct K90 rate for mixed area')
                    else:
                        print(f'   ❓ Unexpected rate: K{rate}')
                        
                else:
                    print(f'❌ Revenue calculation failed: {rp.get("error", "Unknown")}')
            else:
                print('❌ No revenue projections found')
                
        except Exception as e:
            print(f'❌ Test failed: {str(e)}')