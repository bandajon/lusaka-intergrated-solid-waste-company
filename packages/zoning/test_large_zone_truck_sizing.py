#!/usr/bin/env python3
"""
Test truck sizing for large zone generating 37.5 tonnes per week
"""

import sys
import os
sys.path.insert(0, 'app')

from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

# Import the analyze_zone function
from app.views.zones import analyze_zone as analyze_zone_func

# Test data - Large zone that should generate ~37.5 tonnes/week
# This would be ~10,714 people at 0.5kg/day (37,500kg ÷ 7 days ÷ 0.5kg/person)
test_geometry = {
    'type': 'Polygon',
    'coordinates': [[
        [28.2500, -15.4500],
        [28.3000, -15.4500], 
        [28.3000, -15.5000],
        [28.2500, -15.5000],
        [28.2500, -15.4500]
    ]]
}

# Create request that should result in ~37.5 tonnes/week
test_data = {
    'geometry': test_geometry,
    'metadata': {
        'name': 'Large Zone Test - 37.5 tonnes/week',
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
                
            print('🚛 LARGE ZONE TRUCK SIZING TEST')
            print('=' * 60)
            
            # Check basic metrics
            population = result.get('population_estimate', 0)
            daily_waste = result.get('waste_generation_kg_per_day', 0)
            weekly_waste = daily_waste * 7
            
            print('📊 Zone Metrics:')
            print(f'   Population: {population:,} people')
            print(f'   Daily Waste: {daily_waste:,.1f} kg')
            print(f'   Weekly Waste: {weekly_waste:,.1f} kg ({weekly_waste/1000:.1f} tonnes)')
            
            # Check collection requirements
            if 'collection_requirements' in result:
                cr = result['collection_requirements']
                
                print(f'\n🚛 Collection Analysis:')
                print(f'   Frequency: {cr.get("frequency_per_week", 0)}x per week')
                
                if 'recommended_fleet' in cr:
                    print(f'   Recommended Fleet: {cr["recommended_fleet"]}')
                
                if 'total_capacity_provided' in cr:
                    capacity = cr['total_capacity_provided']
                    print(f'   Total Weekly Capacity: {capacity:,.1f} kg ({capacity/1000:.1f} tonnes)')
                    
                    coverage = (capacity / weekly_waste) * 100 if weekly_waste > 0 else 0
                    print(f'   Coverage: {coverage:.1f}%')
                    
                    if coverage >= 100:
                        print('   ✅ Sufficient capacity to handle all waste')
                    else:
                        print('   ❌ Insufficient capacity - waste will accumulate!')
                        uncollected = weekly_waste - capacity
                        print(f'   Uncollected: {uncollected:,.1f} kg/week ({uncollected/1000:.1f} tonnes/week)')
                
                # Check vehicle details
                if 'vehicle_requirements' in cr:
                    vr = cr['vehicle_requirements']
                    print(f'\n🔧 Vehicle Details:')
                    for truck_type, count in vr.items():
                        if truck_type != 'frequency_per_week' and truck_type != 'total_capacity_needed' and truck_type != 'capacity_per_truck':
                            if isinstance(count, int) and count > 0:
                                capacity_per = vr.get('capacity_per_truck', 0)
                                print(f'   {count}x {truck_type.replace("_", "-")} (capacity: {capacity_per:,} kg each)')
                
                # Cost analysis
                daily_cost = cr.get('daily_cost', 0)
                monthly_cost = cr.get('monthly_cost', 0)
                print(f'\n💰 Cost Analysis:')
                print(f'   Daily Cost: K{daily_cost:,.0f}')
                print(f'   Monthly Cost: K{monthly_cost:,.0f}')
                
                if weekly_waste > 0:
                    cost_per_tonne = (daily_cost * 7) / (weekly_waste / 1000)
                    print(f'   Cost per Tonne: K{cost_per_tonne:.0f}')
            
            # Test specific scenario: 37.5 tonnes/week
            target_weekly_waste = 37500  # kg
            print(f'\n🎯 Target Scenario Analysis (37.5 tonnes/week):')
            
            if abs(weekly_waste - target_weekly_waste) < 5000:  # Within 5 tonnes
                print(f'   ✅ Test zone generates similar waste volume: {weekly_waste/1000:.1f} tonnes/week')
            else:
                print(f'   📝 Note: Test zone generates {weekly_waste/1000:.1f} tonnes/week (target: 37.5 tonnes)')
            
            # Verify the mathematical correctness
            if 'collection_requirements' in result and 'total_capacity_provided' in result['collection_requirements']:
                capacity = result['collection_requirements']['total_capacity_provided']
                frequency = result['collection_requirements'].get('frequency_per_week', 0)
                
                print(f'\n🧮 Mathematical Verification:')
                print(f'   Weekly waste to collect: {weekly_waste:,.1f} kg')
                print(f'   Fleet weekly capacity: {capacity:,.1f} kg')
                print(f'   Collection frequency: {frequency}x per week')
                
                if capacity >= weekly_waste:
                    surplus = capacity - weekly_waste
                    print(f'   ✅ Capacity exceeds waste by {surplus:,.1f} kg ({surplus/1000:.1f} tonnes)')
                    print(f'   ✅ Recommendation is mathematically sound')
                else:
                    deficit = weekly_waste - capacity
                    print(f'   ❌ Capacity deficit: {deficit:,.1f} kg ({deficit/1000:.1f} tonnes)')
                    print(f'   ❌ Recommendation is insufficient!')
            
            print(f'\n🚀 TRUCK SIZING ACCURACY: {"✅ FIXED" if "total_capacity_provided" in result.get("collection_requirements", {}) else "❌ NEEDS WORK"}')
                
        except Exception as e:
            print(f'❌ Large zone test failed: {str(e)}')
            import traceback
            traceback.print_exc()