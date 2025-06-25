#!/usr/bin/env python3
"""
Debug script to identify why GHSL population extraction is returning 0
This will help diagnose the waste generation calculation issue
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_population_extraction():
    """Test GHSL population extraction to identify the issue"""
    print("🔍 DEBUGGING POPULATION EXTRACTION ISSUE")
    print("=" * 60)
    print(f"⏰ Debug started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Check Earth Engine Initialization
    print("🧪 Test 1: Earth Engine Initialization")
    print("-" * 40)
    
    try:
        from app.utils.earth_engine_analysis import EarthEngineAnalyzer
        earth_engine = EarthEngineAnalyzer()
        
        auth_status = earth_engine.get_auth_status()
        print(f"✅ Earth Engine initialized: {auth_status['initialized']}")
        if not auth_status['initialized']:
            print(f"❌ Error details: {auth_status['error_details']}")
            print("⚠️  This is the root cause - Earth Engine is not initialized!")
            return False
        else:
            print("✅ Earth Engine is working properly")
        
    except Exception as e:
        print(f"❌ Earth Engine initialization failed: {str(e)}")
        return False
    
    # Test 2: Create Mock Zone for Testing
    print("\n🧪 Test 2: Create Mock Zone for Lusaka")
    print("-" * 40)
    
    try:
        # Create a mock zone in central Lusaka
        class MockZone:
            def __init__(self):
                self.id = 'debug_zone'
                self.name = 'Debug Zone - Central Lusaka'
                # Coordinates for central Lusaka area
                self.geojson = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [28.280, -15.420],  # Southwest corner
                            [28.285, -15.420],  # Southeast corner
                            [28.285, -15.415],  # Northeast corner
                            [28.280, -15.415],  # Northwest corner
                            [28.280, -15.420]   # Close polygon
                        ]]
                    },
                    "properties": {
                        "name": "Debug Zone - Central Lusaka"
                    }
                }
        
        mock_zone = MockZone()
        print("✅ Mock zone created for central Lusaka")
        print(f"   Zone coordinates: {mock_zone.geojson['geometry']['coordinates'][0]}")
        
    except Exception as e:
        print(f"❌ Mock zone creation failed: {str(e)}")
        return False
    
    # Test 3: Test GHSL Population Extraction
    print("\n🧪 Test 3: GHSL Population Extraction")
    print("-" * 40)
    
    try:
        ghsl_result = earth_engine.extract_ghsl_population_for_zone(mock_zone, 2025)
        
        if 'error' in ghsl_result:
            print(f"❌ GHSL extraction failed: {ghsl_result['error']}")
            print("⚠️  This is likely the cause of the waste generation issue!")
        else:
            print("✅ GHSL extraction successful")
            print(f"   Total population: {ghsl_result.get('total_population', 0)}")
            print(f"   Density category: {ghsl_result.get('density_category', 'Unknown')}")
            print(f"   Confidence score: {ghsl_result.get('confidence_assessment', {}).get('confidence_score', 0)}")
            
            if ghsl_result.get('total_population', 0) == 0:
                print("❌ Population is 0 - this is the root cause!")
                print("   Possible reasons:")
                print("   - Zone coordinates are outside GHSL data coverage")
                print("   - Zone area is too small")
                print("   - GHSL dataset year not available")
                print("   - Zone is in unpopulated area")
            else:
                print("✅ Population data looks good")
        
    except Exception as e:
        print(f"❌ GHSL extraction test failed: {str(e)}")
        return False
    
    # Test 4: Test Alternative WorldPop Extraction
    print("\n🧪 Test 4: WorldPop Population Extraction (Alternative)")
    print("-" * 40)
    
    try:
        worldpop_result = earth_engine.extract_population_for_zone(mock_zone, 2020)
        
        if 'error' in worldpop_result:
            print(f"❌ WorldPop extraction failed: {worldpop_result['error']}")
        else:
            print("✅ WorldPop extraction successful")
            print(f"   Total population: {worldpop_result.get('total_population', 0)}")
            print(f"   Population density: {worldpop_result.get('population_density_per_sqkm', 0)}")
            
            if worldpop_result.get('total_population', 0) == 0:
                print("❌ WorldPop also returns 0 population")
            else:
                print("✅ WorldPop has population data - could use as fallback")
        
    except Exception as e:
        print(f"❌ WorldPop extraction test failed: {str(e)}")
    
    # Test 5: Test Waste Generation with Mock Data
    print("\n🧪 Test 5: Test Waste Generation with Mock Population Data")
    print("-" * 40)
    
    try:
        # Create mock population data to test waste calculation
        mock_population_data = {
            'total_population': 1000,  # Mock 1000 people
            'household_count': 222,
            'density_category': 'Medium Density Urban',
            'waste_generation_inputs': {
                'urban_classification': 'urban'
            }
        }
        
        mock_density_features = {
            'built_up_ratio_percent': 35,
            'buildings_per_hectare': 25
        }
        
        mock_area_features = {
            'total_area': 100000  # 10 hectares
        }
        
        waste_result = earth_engine.calculate_comprehensive_waste_generation(
            mock_population_data, mock_density_features, mock_area_features, mock_zone
        )
        
        if 'error' in waste_result:
            print(f"❌ Waste generation calculation failed: {waste_result['error']}")
        else:
            print("✅ Waste generation calculation successful with mock data")
            daily_waste = waste_result.get('daily_waste_generation', {}).get('annual_average_kg_day', 0)
            print(f"   Daily waste generation: {daily_waste} kg/day")
            
            # Test truck calculations
            collection_reqs = waste_result.get('collection_requirements', {})
            if collection_reqs:
                print(f"   Collection frequency: {collection_reqs.get('recommended_collection_frequency', 'Unknown')}")
                trucks_needed = collection_reqs.get('vehicles_required', {})
                if trucks_needed:
                    print(f"   10-tonne trucks: {trucks_needed.get('10_tonne_trucks', 0)}")
                    print(f"   20-tonne trucks: {trucks_needed.get('20_tonne_trucks', 0)}")
        
    except Exception as e:
        print(f"❌ Waste generation test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    if not auth_status['initialized']:
        print("❌ ROOT CAUSE: Earth Engine is not properly initialized")
        print("💡 SOLUTION: Fix Earth Engine authentication")
        print("   - Check service account credentials")
        print("   - Verify Earth Engine project setup")
        print("   - Try running 'earthengine authenticate'")
    elif 'ghsl_result' in locals() and 'error' in ghsl_result:
        print("❌ ROOT CAUSE: GHSL data extraction is failing")
        print("💡 SOLUTION: Debug GHSL dataset access")
        print("   - Check if zone coordinates are valid")
        print("   - Verify GHSL dataset availability")
        print("   - Consider using WorldPop as fallback")
    elif 'ghsl_result' in locals() and ghsl_result.get('total_population', 0) == 0:
        print("❌ ROOT CAUSE: Zone has 0 population in GHSL dataset")
        print("💡 SOLUTION: Adjust zone location or use fallback estimation")
        print("   - Move zone to populated area")
        print("   - Use building-based population estimation")
        print("   - Implement fallback population estimation")
    else:
        print("✅ No obvious issues found - may need deeper investigation")
        print("💡 Check the specific zone coordinates being used in the actual system")
    
    return True

if __name__ == "__main__":
    print("🔍 POPULATION EXTRACTION DEBUG TOOL")
    print("Diagnosing why waste generation calculations return 0")
    print()
    
    success = test_population_extraction()
    
    if success:
        print("\n🏁 Debug completed successfully")
    else:
        print("\n❌ Debug encountered critical errors")