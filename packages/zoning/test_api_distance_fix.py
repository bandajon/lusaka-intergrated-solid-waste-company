#!/usr/bin/env python3
"""
Test script to verify the API endpoint distance calculation matches the web interface
This will test the actual API call that the web interface makes
"""

import os
import sys
import json
import requests
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app
from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer

def test_api_distance_calculation():
    """Test the actual API endpoint with web interface data format"""
    print("🧪 Testing API Distance Calculation (Web Interface Format)")
    print("=" * 70)
    
    # Create Flask app for testing
    app = create_app()
    
    # Test zones with different locations (matching web interface GeoJSON format)
    test_zones = [
        {
            "name": "Lusaka Center Zone",
            "geometry": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.2833, -15.4166],  # Lusaka center
                        [28.2900, -15.4166],
                        [28.2900, -15.4100],
                        [28.2833, -15.4100],
                        [28.2833, -15.4166]
                    ]]
                }
            },
            "expected": "~8-10 km"
        },
        {
            "name": "Near Chunga Zone",
            "geometry": {
                "type": "Feature", 
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [28.2750, -15.3600],  # Near Chunga
                        [28.2800, -15.3600],
                        [28.2800, -15.3550],
                        [28.2750, -15.3550],
                        [28.2750, -15.3600]
                    ]]
                }
            },
            "expected": "~2-4 km"
        },
        {
            "name": "Far from Chunga Zone",
            "geometry": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon", 
                    "coordinates": [[
                        [28.3200, -15.4800],  # Far from Chunga
                        [28.3300, -15.4800],
                        [28.3300, -15.4700],
                        [28.3200, -15.4700],
                        [28.3200, -15.4800]
                    ]]
                }
            },
            "expected": "~16-20 km"
        }
    ]
    
    print(f"📍 Chunga Dumpsite: [-15.350004, 28.270069]")
    print()
    
    results = []
    
    with app.test_client() as client:
        for test_zone in test_zones:
            print(f"🔍 Testing: {test_zone['name']} ({test_zone['expected']})")
            print("-" * 50)
            
            # Create API request data (matching web interface format)
            request_data = {
                "geometry": test_zone["geometry"],
                "metadata": {
                    "name": test_zone["name"],
                    "zone_type": "residential"
                },
                "session_id": "test_session_123"
            }
            
            # Make API call
            response = client.post(
                '/zones/api/analyze-zone',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                result = response.get_json()
                
                if result.get('success'):
                    analysis = result.get('analysis', {})
                    
                    # Extract distance information
                    collection_analysis = analysis.get('analysis_modules', {}).get('collection_feasibility', {})
                    truck_requirements = collection_analysis.get('truck_requirements', {})
                    
                    if truck_requirements and not truck_requirements.get('error'):
                        distance = truck_requirements.get('chunga_dumpsite_distance_km', 'Unknown')
                        print(f"✅ API Response received")
                        print(f"🚛 Distance to Chunga: {distance} km")
                        print(f"🎯 Expected: {test_zone['expected']}")
                        
                        # Check if there's a recommended solution
                        recommended = truck_requirements.get('recommended_solution', {})
                        if recommended:
                            print(f"📊 Recommended trucks: {recommended.get('trucks_required', 'N/A')}")
                            print(f"💰 Daily cost: ${recommended.get('daily_cost', 'N/A')}")
                        
                        results.append({
                            'zone_name': test_zone['name'],
                            'distance_km': distance,
                            'expected': test_zone['expected'],
                            'success': True
                        })
                    else:
                        print(f"❌ No truck requirements data in response")
                        print(f"   Error: {truck_requirements.get('error', 'Unknown')}")
                        results.append({
                            'zone_name': test_zone['name'],
                            'distance_km': 'Error',
                            'expected': test_zone['expected'],
                            'success': False
                        })
                else:
                    print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                    results.append({
                        'zone_name': test_zone['name'],
                        'distance_km': 'API Error',
                        'expected': test_zone['expected'],
                        'success': False
                    })
            else:
                print(f"❌ API call failed: {response.status_code}")
                results.append({
                    'zone_name': test_zone['name'],
                    'distance_km': 'HTTP Error',
                    'expected': test_zone['expected'],
                    'success': False
                })
            
            print()
    
    # Analysis of results
    print("=" * 70)
    print("📊 API ANALYSIS RESULTS")
    print("=" * 70)
    
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        print("❌ No successful API calls - check server setup")
        return results
    
    distances = [r['distance_km'] for r in successful_results if isinstance(r['distance_km'], (int, float))]
    
    if distances and len(set(distances)) == 1:
        print("❌ ISSUE FOUND: All API calls return the same distance!")
        print(f"   All zones showing: {distances[0]} km")
        print("   This confirms the web interface bug")
        
        # Provide debugging info
        print("\n🔧 DEBUGGING INFO:")
        print("   - Zone geometries are different")
        print("   - API receives correct GeoJSON data")
        print("   - Issue is in backend processing")
        
    elif distances and len(set(distances)) > 1:
        print("✅ SUCCESS: API returns different distances for different zones!")
        for result in successful_results:
            print(f"   {result['zone_name']}: {result['distance_km']} km")
    else:
        print("❓ MIXED RESULTS: Some API calls failed")
        for result in results:
            if result['success']:
                print(f"   ✅ {result['zone_name']}: {result['distance_km']} km")
            else:
                print(f"   ❌ {result['zone_name']}: {result['distance_km']}")
    
    return results

def test_direct_analyzer():
    """Test the analyzer directly with GeoJSON Feature format"""
    print("\n🧪 Testing Direct Analyzer with Feature Format")
    print("=" * 50)
    
    analyzer = EnhancedRealTimeZoneAnalyzer()
    
    # Test with GeoJSON Feature (matching web interface format)
    feature_geometry = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [28.2800, -15.4000],  # Test location
                [28.2850, -15.4000],
                [28.2850, -15.3950],
                [28.2800, -15.3950],
                [28.2800, -15.4000]
            ]]
        }
    }
    
    print("Testing with GeoJSON Feature format...")
    
    # Analyze the zone
    result = analyzer.analyze_drawn_zone(feature_geometry)
    
    # Extract distance information
    collection_analysis = result.get('analysis_modules', {}).get('collection_feasibility', {})
    truck_requirements = collection_analysis.get('truck_requirements', {})
    
    if truck_requirements and not truck_requirements.get('error'):
        distance = truck_requirements.get('chunga_dumpsite_distance_km', 'Unknown')
        print(f"✅ Direct analyzer distance: {distance} km")
        
        # Check centroid calculation
        if 'Calculated centroid for zone' in str(result):
            print("✅ Centroid calculation debug message found")
        else:
            print("❌ No centroid calculation debug message")
    else:
        print(f"❌ Direct analyzer failed: {truck_requirements.get('error', 'Unknown')}")
    
    return result

if __name__ == "__main__":
    print("🔍 API DISTANCE CALCULATION TEST")
    print("=" * 70)
    print("Testing the exact API endpoint that the web interface uses...")
    print()
    
    # Test 1: Direct analyzer with Feature format
    direct_result = test_direct_analyzer()
    
    # Test 2: API endpoint calls
    try:
        api_results = test_api_distance_calculation()
        
        print("\n" + "=" * 70)
        print("🎯 CONCLUSION")
        print("=" * 70)
        
        # Analyze results
        successful_api = [r for r in api_results if r['success']]
        if successful_api:
            distances = [r['distance_km'] for r in successful_api if isinstance(r['distance_km'], (int, float))]
            if distances and len(set(distances)) == 1:
                print(f"❌ CONFIRMED BUG: All zones show {distances[0]} km in API")
                print("   Root cause: Backend processing issue")
            elif distances and len(set(distances)) > 1:
                print("✅ BUG APPEARS FIXED: API shows different distances")
            else:
                print("❓ INCONCLUSIVE: Mixed API results")
        else:
            print("❌ API TESTING FAILED: Check server setup")
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        print("   This might be due to server not running or missing dependencies")