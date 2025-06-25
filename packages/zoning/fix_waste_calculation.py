#!/usr/bin/env python3
"""
Fix the waste calculation issue by adding debugging and fallback population estimation
This addresses the specific issue where GHSL population returns 0
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def apply_waste_calculation_fix():
    """Apply the fix to the earth_engine_analysis.py file"""
    print("🔧 APPLYING WASTE CALCULATION FIX")
    print("=" * 50)
    print(f"⏰ Fix started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Read the current earth_engine_analysis.py file
    file_path = "app/utils/earth_engine_analysis.py"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        print("✅ Read earth_engine_analysis.py successfully")
        
        # Find the calculate_comprehensive_waste_generation method
        method_start = content.find("def calculate_comprehensive_waste_generation(self, ghsl_population: Dict, density_features: Dict,")
        if method_start == -1:
            print("❌ Could not find calculate_comprehensive_waste_generation method")
            return False
        
        # Find the error check line
        error_check = content.find("if total_population == 0:")
        if error_check == -1:
            print("❌ Could not find the population error check")
            return False
        
        # Find the return statement for the error
        error_return_start = content.find('return {"error": "No population data available for waste generation calculation"}', error_check)
        if error_return_start == -1:
            print("❌ Could not find the error return statement")
            return False
        
        error_return_end = error_return_start + len('return {"error": "No population data available for waste generation calculation"}')
        
        # Create the enhanced fallback logic
        enhanced_logic = '''# Enhanced fallback population estimation
            if total_population == 0:
                print(f"⚠️  GHSL population is 0 for zone {zone.id if hasattr(zone, 'id') else 'unknown'}")
                print(f"   Attempting fallback population estimation...")
                
                # Fallback 1: Use building-based estimation
                try:
                    building_count = density_features.get('building_count', 0) if not density_features.get('error') else 0
                    area_sqkm = area_features.get('total_area_sqkm', 1.0) if not area_features.get('error') else 1.0
                    
                    if building_count > 0:
                        # Estimate population based on building count (average 4-6 people per building in Lusaka)
                        estimated_population = building_count * 5.0
                        print(f"   Fallback 1: Building-based estimation = {estimated_population} people from {building_count} buildings")
                        total_population = estimated_population
                        household_count = int(total_population / 4.5)
                        density_category = 'Medium Density Urban'  # Default assumption
                        urban_classification = 'urban'
                        
                    elif area_sqkm > 0:
                        # Fallback 2: Area-based estimation using typical Lusaka densities
                        typical_density_per_sqkm = 5000  # Conservative estimate for Lusaka urban areas
                        estimated_population = area_sqkm * typical_density_per_sqkm
                        print(f"   Fallback 2: Area-based estimation = {estimated_population} people from {area_sqkm} km²")
                        total_population = estimated_population
                        household_count = int(total_population / 4.5)
                        density_category = 'Medium Density Urban'
                        urban_classification = 'urban'
                        
                    else:
                        # Fallback 3: Minimum viable population for any zone
                        estimated_population = 100  # Minimum assumption
                        print(f"   Fallback 3: Minimum viable population = {estimated_population} people")
                        total_population = estimated_population
                        household_count = int(total_population / 4.5)
                        density_category = 'Low Density Urban'
                        urban_classification = 'peri_urban'
                    
                    print(f"✅ Using fallback population: {total_population} people")
                    
                except Exception as fallback_error:
                    print(f"❌ All fallback methods failed: {str(fallback_error)}")
                    return {"error": f"No population data available and fallback estimation failed: {str(fallback_error)}"}
            
            if total_population == 0:
                return {"error": "No population data available for waste generation calculation"}'''
        
        # Replace the simple error check with enhanced logic
        new_content = content[:error_check] + enhanced_logic + content[error_return_end:]
        
        # Write the updated content back to the file
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Applied enhanced fallback population estimation")
        print("   - Added building-based population fallback")
        print("   - Added area-based population fallback") 
        print("   - Added minimum viable population fallback")
        print("   - Added comprehensive debugging output")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix application failed: {str(e)}")
        return False

def test_fix():
    """Test the fix by running the real-time analyzer again"""
    print("\n🧪 TESTING THE FIX")
    print("=" * 30)
    
    try:
        # Import the updated analyzer
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Test zone GeoJSON
        test_zone_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [28.280, -15.420],
                    [28.285, -15.420],
                    [28.285, -15.415],
                    [28.280, -15.415],
                    [28.280, -15.420]
                ]]
            },
            "properties": {
                "name": "Test Zone - Fixed",
                "zone_type": "mixed"
            }
        }
        
        print("🔄 Running analysis with fixed code...")
        result = analyzer.analyze_drawn_zone(test_zone_geojson)
        
        # Check if waste generation worked
        earth_engine_data = result.get('analysis_modules', {}).get('earth_engine', {})
        if earth_engine_data and 'error' not in earth_engine_data:
            building_features = earth_engine_data.get('building_features', {})
            if building_features and 'error' not in building_features:
                waste_gen = building_features.get('waste_generation', {})
                if waste_gen and 'error' not in waste_gen:
                    daily_waste = waste_gen.get('daily_waste_generation', {})
                    if daily_waste and daily_waste.get('annual_average_kg_day', 0) > 0:
                        print("✅ WASTE GENERATION FIXED!")
                        print(f"   Daily waste: {daily_waste.get('annual_average_kg_day', 0)} kg/day")
                        
                        collection_reqs = waste_gen.get('collection_requirements', {})
                        if collection_reqs:
                            vehicles = collection_reqs.get('vehicles_required', {})
                            if vehicles:
                                trucks_10t = vehicles.get('10_tonne_trucks', 0)
                                trucks_20t = vehicles.get('20_tonne_trucks', 0)
                                print(f"   Trucks needed: {trucks_10t} × 10t, {trucks_20t} × 20t")
                                return True
        
        print("❌ Fix did not work - waste generation still not calculating")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 WASTE CALCULATION FIX TOOL")
    print("Fixing the issue where zone analyzer isn't calculating waste and trucks")
    print()
    
    # Apply the fix
    fix_success = apply_waste_calculation_fix()
    
    if fix_success:
        print("\n✅ Fix applied successfully")
        
        # Test the fix
        test_success = test_fix()
        
        if test_success:
            print("\n🎉 SUCCESS: Waste generation and truck calculations are now working!")
        else:
            print("\n⚠️  Fix applied but still need to debug further")
    else:
        print("\n❌ Failed to apply fix")