#!/usr/bin/env python3
"""
Test script for Chunga dump site distance calculations
=======================================================

This script tests the Google Maps integration and fallback calculations
for distance and travel time to Chunga dump site.

Usage: python test_chunga_distance.py
"""

import sys
import os
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_google_maps_distance():
    """Test Google Maps distance calculator directly"""
    print("🧪 Testing Google Maps Distance Calculator")
    print("=" * 50)
    
    try:
        from app.utils.google_maps_distance import GoogleMapsDistanceCalculator
        
        # Initialize calculator
        calculator = GoogleMapsDistanceCalculator()
        
        # Test with sample Lusaka coordinates (near city center)
        test_locations = [
            {"name": "Lusaka City Center", "lat": -15.4166, "lng": 28.2833},
            {"name": "Garden Compound", "lat": -15.3928, "lng": 28.3474},
            {"name": "Kalingalinga", "lat": -15.3667, "lng": 28.3500},
            {"name": "Mtendere", "lat": -15.3833, "lng": 28.4000}
        ]
        
        for location in test_locations:
            print(f"\n📍 Testing from {location['name']} ({location['lat']:.4f}, {location['lng']:.4f})")
            
            # Test distance calculation
            result = calculator.calculate_distance_and_time(
                location['lat'], location['lng'],
                traffic_model="best_guess"
            )
            
            print(f"   Distance: {result['distance_km']} km")
            print(f"   Travel time: {result['duration_with_traffic_minutes']:.1f} minutes")
            print(f"   Fuel cost: K{result['fuel_cost_kwacha']:.2f}")
            print(f"   Data source: {result['data_source']}")
            print(f"   Success: {result['success']}")
            
            if not result['success'] and 'error_message' in result:
                print(f"   Error: {result['error_message']}")
        
        # Test comprehensive logistics
        print(f"\n🚛 Testing comprehensive logistics for Garden Compound")
        logistics = calculator.calculate_collection_logistics(-15.3928, 28.3474, 2)
        
        print(f"   Weekly distance: {logistics['weekly_metrics']['total_distance_km']} km")
        print(f"   Weekly cost: K{logistics['weekly_metrics']['total_cost_kwacha']:.2f}")
        print(f"   Monthly cost: K{logistics['monthly_metrics']['total_cost_kwacha']:.2f}")
        
        # Test calculator status
        print(f"\n⚙️ Calculator Status:")
        status = calculator.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Google Maps test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_unified_analyzer():
    """Test unified analyzer integration"""
    print("\n\n🔬 Testing Unified Analyzer Integration")
    print("=" * 50)
    
    try:
        from app.utils.unified_analyzer import UnifiedAnalyzer, AnalysisRequest, AnalysisType
        
        # Initialize analyzer
        analyzer = UnifiedAnalyzer()
        
        # Create sample zone geometry (Garden Compound area)
        sample_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [28.3400, -15.3850],  # Southwest corner
                [28.3550, -15.3850],  # Southeast corner
                [28.3550, -15.3950],  # Northeast corner
                [28.3400, -15.3950],  # Northwest corner
                [28.3400, -15.3850]   # Close polygon
            ]]
        }
        
        # Test waste analysis with distance calculations
        print("\n📊 Testing waste analysis with Chunga logistics")
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.WASTE,
            geometry=sample_geometry,
            zone_name="Test Garden Compound",
            options={'collection_frequency': 2}
        )
        
        result = analyzer.analyze(request)
        
        print(f"   Analysis successful: {result.success}")
        print(f"   Population estimate: {result.population_estimate}")
        print(f"   Daily waste: {result.waste_generation_kg_per_day} kg")
        
        if result.collection_requirements and 'chunga_logistics' in result.collection_requirements:
            logistics = result.collection_requirements['chunga_logistics']
            print(f"   Distance to Chunga: {logistics.get('distance_km', 'N/A')} km")
            print(f"   Travel time: {logistics.get('duration_with_traffic_minutes', 'N/A')} minutes")
            print(f"   Round trip fuel cost: K{logistics.get('round_trip_fuel_cost_kwacha', 'N/A')}")
            print(f"   Data source: {logistics.get('data_source', 'N/A')}")
        
        # Test comprehensive analysis
        print(f"\n🔍 Testing comprehensive analysis")
        
        comprehensive_request = AnalysisRequest(
            analysis_type=AnalysisType.COMPREHENSIVE,
            geometry=sample_geometry,
            zone_name="Test Comprehensive Zone"
        )
        
        comprehensive_result = analyzer.analyze(comprehensive_request)
        
        print(f"   Comprehensive analysis successful: {comprehensive_result.success}")
        print(f"   Building count: {comprehensive_result.building_count}")
        print(f"   Population: {comprehensive_result.population_estimate}")
        print(f"   Daily waste: {comprehensive_result.waste_generation_kg_per_day} kg")
        
        if comprehensive_result.collection_requirements and 'chunga_logistics' in comprehensive_result.collection_requirements:
            logistics = comprehensive_result.collection_requirements['chunga_logistics']
            print(f"   Logistics data source: {logistics.get('data_source', 'N/A')}")
        
        # Test analyzer status
        print(f"\n⚙️ Analyzer Status:")
        status = analyzer.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Unified analyzer test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_fallback_calculations():
    """Test fallback calculations when Google Maps is not available"""
    print("\n\n🔄 Testing Fallback Calculations")
    print("=" * 50)
    
    try:
        from app.utils.unified_analyzer import UnifiedAnalyzer
        
        analyzer = UnifiedAnalyzer()
        
        # Test fallback logistics directly
        zone_center = {'lat': -15.3928, 'lng': 28.3474}  # Garden Compound
        
        fallback_result = analyzer._fallback_chunga_logistics(zone_center, 2)
        
        print(f"   Fallback distance: {fallback_result['distance_km']} km")
        print(f"   Fallback travel time: {fallback_result['duration_with_traffic_minutes']} minutes")
        print(f"   Fallback fuel cost: K{fallback_result['fuel_cost_kwacha']:.2f}")
        print(f"   Round trip distance: {fallback_result['round_trip_distance_km']} km")
        print(f"   Data source: {fallback_result['data_source']}")
        
        # Test haversine distance calculation
        chunga_lat, chunga_lng = -15.349850, 28.268712
        haversine_dist = analyzer._haversine_distance_simple(
            -15.3928, 28.3474, chunga_lat, chunga_lng
        )
        
        print(f"   Haversine distance to Chunga: {haversine_dist:.2f} km")
        
    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Chunga Distance Calculation Tests")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    
    # Test individual components
    test_google_maps_distance()
    test_unified_analyzer()
    test_fallback_calculations()
    
    print(f"\n✅ All tests completed at: {datetime.now()}")
    print("=" * 60)