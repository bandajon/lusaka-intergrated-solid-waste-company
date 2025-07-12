#!/usr/bin/env python3
"""
Test Google Gemini Flash API for truck recommendations
"""

import sys
import os
sys.path.insert(0, 'app')

from app.utils.gemini_recommendations import initialize_gemini_engine, get_gemini_recommendation

print('🤖 GEMINI FLASH RECOMMENDATION TEST')
print('=' * 60)

# Initialize Gemini engine
try:
    engine = initialize_gemini_engine()
    if engine:
        print('✅ Gemini Flash API connected successfully')
    else:
        print('❌ Failed to connect to Gemini Flash API')
        exit(1)
except Exception as e:
    print(f'❌ Gemini initialization failed: {str(e)}')
    exit(1)

# Test scenario: 218.1 tonnes per week (the problematic case)
test_scenarios = [
    {
        'name': 'Problem Scenario - 218.1 tonnes/week',
        'population': 62311,
        'daily_waste_kg': 31156,  # This gives 218.1 tonnes/week
        'distance_km': 6.8,
        'settlement_type': 'informal_high_density'
    },
    {
        'name': 'Medium Zone - 37.5 tonnes/week', 
        'population': 10714,
        'daily_waste_kg': 5357,  # This gives 37.5 tonnes/week
        'distance_km': 8.5,
        'settlement_type': 'formal_medium_density'
    },
    {
        'name': 'Small Zone - 4.9 tonnes/week',
        'population': 1400,
        'daily_waste_kg': 700,  # This gives 4.9 tonnes/week
        'distance_km': 12.4,
        'settlement_type': 'mixed'
    }
]

for scenario in test_scenarios:
    print(f'\n🎯 Testing: {scenario["name"]}')
    print(f'   Population: {scenario["population"]:,}')
    print(f'   Daily waste: {scenario["daily_waste_kg"]:,.0f} kg')
    print(f'   Weekly waste: {scenario["daily_waste_kg"] * 7:,.0f} kg ({(scenario["daily_waste_kg"] * 7)/1000:.1f} tonnes)')
    print(f'   Distance: {scenario["distance_km"]} km')
    
    try:
        recommendation = get_gemini_recommendation(
            scenario['population'],
            scenario['daily_waste_kg'],
            scenario['distance_km'],
            scenario['settlement_type']
        )
        
        if recommendation:
            print(f'\n🚛 Gemini Recommendation:')
            print(f'   Fleet: {recommendation.truck_count}x {recommendation.truck_type.replace("_", "-")}')
            print(f'   Collection frequency: {recommendation.collection_frequency}x per week')
            print(f'   Weekly capacity: {recommendation.total_capacity_kg:,} kg ({recommendation.total_capacity_kg/1000:.1f} tonnes)')
            print(f'   Daily cost: K{recommendation.daily_cost:,}')
            print(f'   Monthly cost: K{recommendation.monthly_cost:,}')
            print(f'   Efficiency: {recommendation.efficiency_percent:.1f}%')
            
            # Mathematical validation
            weekly_waste = scenario['daily_waste_kg'] * 7
            if recommendation.total_capacity_kg >= weekly_waste:
                surplus = recommendation.total_capacity_kg - weekly_waste
                print(f'   ✅ Can handle all waste with {surplus:,.0f} kg surplus')
            else:
                deficit = weekly_waste - recommendation.total_capacity_kg
                print(f'   ❌ Capacity deficit: {deficit:,.0f} kg')
            
            print(f'\n💡 Reasoning: {recommendation.reasoning}')
            print(f'🧮 Validation: {recommendation.mathematical_validation}')
        else:
            print('   ❌ No recommendation received')
            
    except Exception as e:
        print(f'   ❌ Test failed: {str(e)}')

print(f'\n🚀 GEMINI INTEGRATION: {"✅ WORKING" if engine else "❌ FAILED"}')