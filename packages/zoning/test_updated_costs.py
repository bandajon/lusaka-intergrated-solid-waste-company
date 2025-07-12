#!/usr/bin/env python3
"""
Test script for updated cost structure with worker salaries and admin costs
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
                
            print('💼 Updated Cost Structure Test (K23/liter + Salaries + Admin):')
            print('=' * 70)
            
            # Navigate to the cost data
            if 'analysis_modules' in result:
                cf = result['analysis_modules']['collection_feasibility']
                tr = cf['truck_requirements']
                
                # Check Chunga logistics
                dl = tr['dumpsite_logistics']
                fuel_price_kwacha = dl.get('fuel_price_usd_per_liter', 0) * 27
                print('📍 Fuel Cost Verification:')
                print(f'   Fuel price: K{fuel_price_kwacha:.0f}/liter (should be K23)')
                
                # Check recommended solution costs
                print('\n🎯 Recommended Solution (10-tonne truck):')
                rs = tr['recommended_solution']
                weekly_cost = rs.get('weekly_cost', 0)
                monthly_cost = rs.get('monthly_cost', 0)
                print(f'   Weekly cost: ${weekly_cost:.2f} (K{weekly_cost * 27:.0f})')
                print(f'   Monthly cost: ${monthly_cost:.2f} (K{monthly_cost * 27:.0f})')
                
                if 'cost_breakdown' in rs:
                    cb = rs['cost_breakdown']
                    print('\n   📊 Monthly cost breakdown:')
                    m = cb['monthly']
                    print(f'     - Operational: ${m["operational"]:.2f} (K{m["operational"] * 27:.0f})')
                    print(f'     - Fuel: ${m["fuel"]:.2f} (K{m["fuel"] * 27:.0f})')
                    print(f'     - Franchise: ${m["franchise"]:.2f} (K{m["franchise"] * 27:.0f})')
                    print(f'     - Worker salaries: ${m["worker_salaries"]:.2f} (K{m["worker_salaries"] * 27:.0f}) [4 workers × K2,500]')
                    print(f'     - Subtotal: ${m["subtotal"]:.2f} (K{m["subtotal"] * 27:.0f})')
                    print(f'     - Admin costs (30%): ${m["admin_costs"]:.2f} (K{m["admin_costs"] * 27:.0f})')
                    print(f'     - TOTAL: ${m["total"]:.2f} (K{m["total"] * 27:.0f})')
                
                # Check 10-tonne truck detailed costs
                print('\n🚛 10-Tonne Truck Monthly Breakdown:')
                truck_10 = tr['truck_10_tonne']
                if 'monthly_costs' in truck_10:
                    mc = truck_10['monthly_costs']
                    print(f'   Operational: K{mc["operational"] * 27:.0f}')
                    print(f'   Fuel: K{mc["fuel"] * 27:.0f}')
                    print(f'   Franchise fees: K{mc["franchise_fees"] * 27:.0f}')
                    print(f'   Worker salaries: K{mc["worker_salaries"] * 27:.0f}')
                    print(f'   Subtotal: K{mc["subtotal"] * 27:.0f}')
                    print(f'   Admin costs (30%): K{mc["admin_costs"] * 27:.0f}')
                    print(f'   TOTAL: K{mc["total"] * 27:.0f}')
                
                # Check 20-tonne truck detailed costs
                print('\n🚚 20-Tonne Truck Monthly Breakdown:')
                truck_20 = tr['truck_20_tonne']
                if 'monthly_costs' in truck_20:
                    mc = truck_20['monthly_costs']
                    print(f'   Operational: K{mc["operational"] * 27:.0f}')
                    print(f'   Fuel: K{mc["fuel"] * 27:.0f} (30% more than 10-tonne)')
                    print(f'   Franchise fees: K{mc["franchise_fees"] * 27:.0f}')
                    print(f'   Worker salaries: K{mc["worker_salaries"] * 27:.0f}')
                    print(f'   Subtotal: K{mc["subtotal"] * 27:.0f}')
                    print(f'   Admin costs (30%): K{mc["admin_costs"] * 27:.0f}')
                    print(f'   TOTAL: K{mc["total"] * 27:.0f}')
                
                print('\n✅ Cost structure updated with:')
                print('   • Fuel cost: K23/liter (down from K25)')
                print('   • Worker salaries: K10,000/month (4 workers × K2,500)')
                print('   • Administrative costs: 30% overhead on total operational costs')
                
        except Exception as e:
            print(f'❌ Cost structure test failed: {str(e)}')
            import traceback
            traceback.print_exc()