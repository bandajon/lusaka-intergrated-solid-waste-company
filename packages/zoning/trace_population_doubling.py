#!/usr/bin/env python3
"""
Trace the exact source of population doubling issue
Follow the population calculation step-by-step
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def trace_population_calculation():
    """Trace population calculation step by step to find doubling"""
    print("🔍 TRACING POPULATION CALCULATION DOUBLING")
    print("=" * 60)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        # Use a smaller, more controlled test area
        test_geometry = {
            "type": "Polygon", 
            "coordinates": [[
                [28.2700, -15.4100],  # Small test area
                [28.2750, -15.4100],
                [28.2750, -15.4050],
                [28.2700, -15.4050],
                [28.2700, -15.4100]
            ]]
        }
        
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        print("🎯 Step 1: Create Mock Zone")
        mock_zone = analyzer._create_mock_zone(test_geometry)
        print(f"   Area: {mock_zone.area_sqm/1000000:.4f} km²")
        print(f"   Initial estimated_population: {getattr(mock_zone, 'estimated_population', 'None')}")
        
        print("\n🌍 Step 2: Earth Engine Analysis")
        if analyzer.earth_engine:
            try:
                # Manually call Earth Engine analysis
                ee_result = analyzer.earth_engine.analyze_zone_comprehensive(test_geometry)
                
                if ee_result and not ee_result.get('error'):
                    buildings_data = ee_result.get('buildings_data', {})
                    
                    if buildings_data and not buildings_data.get('error'):
                        building_count = len(buildings_data.get('building_footprints', []))
                        print(f"   ✅ Earth Engine buildings detected: {building_count}")
                        
                        # Check worldpop data
                        worldpop_data = ee_result.get('worldpop_population', {})
                        if worldpop_data and not worldpop_data.get('error'):
                            worldpop_pop = worldpop_data.get('estimated_population', 0)
                            print(f"   📊 WorldPop population: {worldpop_pop}")
                        
                        # Check GHSL data
                        ghsl_data = ee_result.get('ghsl_population', {})
                        if ghsl_data and not ghsl_data.get('error'):
                            ghsl_pop = ghsl_data.get('estimated_population', 0)
                            print(f"   📊 GHSL population: {ghsl_pop}")
                    else:
                        print(f"   ❌ Buildings error: {buildings_data.get('error', 'Unknown')}")
                        building_count = 0
                else:
                    print(f"   ❌ Earth Engine error: {ee_result.get('error', 'Unknown')}")
                    building_count = 0
                    
            except Exception as e:
                print(f"   ❌ Earth Engine failed: {str(e)}")
                building_count = 0
        else:
            print("   ❌ Earth Engine not available")
            building_count = 0
        
        print("\n👥 Step 3: Population Estimation")
        if analyzer.population_estimator and building_count > 0:
            try:
                # Create simple building data
                import pandas as pd
                buildings_df = pd.DataFrame([
                    {'area': 100, 'building_type': 'residential', 'settlement_type': 'formal'}
                    for _ in range(building_count)
                ])
                
                print(f"   Input: {len(buildings_df)} buildings for analysis")
                
                # Test each estimation method separately
                area_result = analyzer.population_estimator.estimate_population_area_based(buildings_df)
                print(f"   Area-based estimate: {area_result.get('total_population', 0)}")
                
                floor_result = analyzer.population_estimator.estimate_population_floor_based(buildings_df)
                print(f"   Floor-based estimate: {floor_result.get('total_population', 0)}")
                
                settlement_result = analyzer.population_estimator.estimate_population_settlement_based(
                    buildings_df, zone_area_sqm=mock_zone.area_sqm
                )
                print(f"   Settlement-based estimate: {settlement_result.get('total_population', 0)}")
                
                # Test ensemble method
                ensemble_result = analyzer.population_estimator.estimate_population_ensemble(
                    buildings_df, zone_area_sqm=mock_zone.area_sqm
                )
                print(f"   Ensemble estimate: {ensemble_result.get('total_population', 0)}")
                
                # Check if ensemble is causing doubling
                manual_ensemble = (
                    area_result.get('total_population', 0) * 0.4 +
                    floor_result.get('total_population', 0) * 0.3 +
                    settlement_result.get('total_population', 0) * 0.3
                )
                print(f"   Manual ensemble calc: {manual_ensemble:.0f}")
                
                if ensemble_result.get('total_population', 0) != manual_ensemble:
                    print("   ⚠️  MISMATCH: Ensemble method may have issue!")
                
            except Exception as e:
                print(f"   ❌ Population estimation failed: {str(e)}")
        
        print("\n⚡ Step 4: Full Real-Time Analysis")
        try:
            # Run the full analysis and trace population flow
            results = analyzer.analyze_drawn_zone(test_geometry)
            
            # Check mock zone population after analysis
            print(f"   Mock zone final estimated_population: {getattr(mock_zone, 'estimated_population', 'None')}")
            
            # Extract population from results
            population_data = results.get('analysis_modules', {}).get('population_estimation', {})
            if population_data:
                consensus = population_data.get('consensus_estimate', 0)
                print(f"   Analysis consensus estimate: {consensus}")
                
                # Check individual methods in results
                methods = population_data.get('estimation_methods', {})
                for method_name, method_data in methods.items():
                    if isinstance(method_data, dict) and 'estimated_population' in method_data:
                        pop = method_data['estimated_population']
                        print(f"   {method_name}: {pop}")
            
            # Check waste analysis - this might be where doubling shows up
            waste_data = results.get('analysis_modules', {}).get('comprehensive_waste_generation', {})
            if waste_data and not waste_data.get('error'):
                daily_waste = waste_data.get('daily_waste_kg', 0)
                population_used = waste_data.get('population_used', 0)
                print(f"   Waste analysis population: {population_used}")
                print(f"   Daily waste: {daily_waste} kg")
                
                # Check if waste calculation is doubling population
                expected_waste = population_used * 0.5  # Standard 0.5 kg/person/day
                if abs(daily_waste - expected_waste) > 10:  # Allow 10kg difference
                    print(f"   ⚠️  WASTE CALC ISSUE: Expected {expected_waste}, got {daily_waste}")
            
        except Exception as e:
            print(f"   ❌ Full analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n🎯 SUMMARY")
        print("=" * 30)
        print("Check for these potential doubling sources:")
        print("1. Earth Engine building detection duplication")
        print("2. Population estimation ensemble method error")
        print("3. Multiple population sources being added instead of replaced")
        print("4. Waste generation calculation using wrong population")
        
    except Exception as e:
        print(f"❌ Trace failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_population_calculation()