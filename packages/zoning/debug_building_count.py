#!/usr/bin/env python3
"""
Debug script to investigate building count doubling issue
Analyze where the building detection might be duplicating results
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_building_detection():
    """Debug the building detection process to find where doubling occurs"""
    print("🔍 DEBUGGING BUILDING COUNT DOUBLING ISSUE")
    print("=" * 60)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        # Test with a similar area to what the user drew
        test_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [28.2600, -15.4200],  # Approximate area from screenshot
                [28.2900, -15.4200],
                [28.2900, -15.3900],
                [28.2600, -15.3900],
                [28.2600, -15.4200]
            ]]
        }
        
        print(f"🏗️ Testing building detection for zone area...")
        print(f"   Zone coordinates: {test_geometry['coordinates'][0][:2]}...")
        
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Step 1: Create mock zone 
        mock_zone = analyzer._create_mock_zone(test_geometry)
        print(f"   Zone area: {mock_zone.area_sqm/1000000:.3f} km²")
        
        # Step 2: Check Earth Engine building detection
        print("\n🌍 Earth Engine Building Detection:")
        if analyzer.earth_engine:
            try:
                # Test Earth Engine building detection directly
                buildings_result = analyzer.earth_engine.get_buildings_in_zone(test_geometry)
                
                if buildings_result and not buildings_result.get('error'):
                    building_footprints = buildings_result.get('building_footprints', [])
                    total_buildings = len(building_footprints)
                    
                    print(f"   ✅ Earth Engine buildings detected: {total_buildings}")
                    
                    # Check for duplicates in building data
                    if building_footprints:
                        print("   🔍 Analyzing building data structure...")
                        
                        # Check if buildings have unique identifiers
                        unique_areas = set()
                        unique_coords = set()
                        duplicates_by_area = 0
                        duplicates_by_coords = 0
                        
                        for i, building in enumerate(building_footprints[:10]):  # Check first 10
                            area = building.get('area', 0)
                            coords = str(building.get('coordinates', []))
                            
                            if area in unique_areas:
                                duplicates_by_area += 1
                            if coords in unique_coords:
                                duplicates_by_coords += 1
                                
                            unique_areas.add(area)
                            unique_coords.add(coords)
                            
                            if i < 3:  # Show first 3 buildings
                                print(f"     Building {i+1}: Area={area:.1f}m², Coords={len(building.get('coordinates', []))} points")
                        
                        print(f"   📊 Duplicate analysis (first 10 buildings):")
                        print(f"     Duplicates by area: {duplicates_by_area}")
                        print(f"     Duplicates by coordinates: {duplicates_by_coords}")
                        print(f"     Unique areas: {len(unique_areas)}")
                        
                else:
                    print(f"   ❌ Earth Engine error: {buildings_result.get('error', 'Unknown')}")
                    total_buildings = 0
                    
            except Exception as e:
                print(f"   ❌ Earth Engine failed: {str(e)}")
                total_buildings = 0
        else:
            print("   ❌ Earth Engine not available")
            total_buildings = 0
        
        # Step 3: Check population estimation multipliers
        print("\n👥 Population Estimation:")
        if total_buildings > 0:
            # Check different estimation methods
            area_km2 = mock_zone.area_sqm / 1000000
            
            # Method 1: Building-based estimate
            building_based_pop = total_buildings * 4.2  # Average household size
            print(f"   Building-based: {total_buildings} buildings × 4.2 people = {building_based_pop:.0f} people")
            
            # Method 2: Density-based estimate  
            density_based_pop = area_km2 * 2500  # Lusaka average density
            print(f"   Density-based: {area_km2:.3f} km² × 2500 people/km² = {density_based_pop:.0f} people")
            
            # Method 3: Check if there's double counting
            if analyzer.population_estimator:
                try:
                    # Create buildings DataFrame for testing
                    import pandas as pd
                    buildings_df = pd.DataFrame([
                        {'area': 100, 'building_type': 'residential'} 
                        for _ in range(total_buildings)
                    ])
                    
                    pop_estimate = analyzer.population_estimator.estimate_population_buildings(
                        buildings_df, zone_area_sqm=mock_zone.area_sqm
                    )
                    
                    if pop_estimate and not pop_estimate.get('error'):
                        estimated_pop = pop_estimate.get('estimated_population', 0)
                        print(f"   PopulationEstimator: {estimated_pop:.0f} people")
                        
                        # Check if this is causing the doubling
                        ratio = estimated_pop / building_based_pop if building_based_pop > 0 else 0
                        print(f"   Ratio vs building-based: {ratio:.2f}x")
                        
                        if ratio > 1.8:  # Close to 2x
                            print("   ⚠️  POTENTIAL ISSUE: PopulationEstimator may be doubling!")
                        
                except Exception as e:
                    print(f"   ❌ PopulationEstimator failed: {str(e)}")
        
        # Step 4: Check real-time analysis results
        print("\n⚡ Real-Time Analysis Results:")
        try:
            results = analyzer.analyze_drawn_zone(test_geometry)
            
            # Extract building and population data from results
            earth_engine_data = results.get('analysis_modules', {}).get('earth_engine', {})
            population_data = results.get('analysis_modules', {}).get('population_estimation', {})
            
            if earth_engine_data:
                buildings_data = earth_engine_data.get('buildings_data', {})
                if buildings_data and not buildings_data.get('error'):
                    analysis_building_count = len(buildings_data.get('building_footprints', []))
                    print(f"   Analysis building count: {analysis_building_count}")
                    
                    if analysis_building_count != total_buildings:
                        print(f"   ⚠️  MISMATCH: Direct EE={total_buildings}, Analysis={analysis_building_count}")
            
            if population_data:
                consensus_pop = population_data.get('consensus_estimate', 0)
                ghsl_pop = population_data.get('estimation_methods', {}).get('ghsl_population', {}).get('estimated_population', 0)
                
                print(f"   Consensus population: {consensus_pop}")
                print(f"   GHSL population: {ghsl_pop}")
                
                # Check for doubling patterns
                if consensus_pop > 0 and ghsl_pop > 0:
                    ratio = consensus_pop / ghsl_pop
                    print(f"   Consensus/GHSL ratio: {ratio:.2f}x")
                    
        except Exception as e:
            print(f"   ❌ Real-time analysis failed: {str(e)}")
        
        return {
            'total_buildings': total_buildings,
            'area_km2': area_km2,
            'building_based_pop': building_based_pop if total_buildings > 0 else 0,
            'density_based_pop': density_based_pop
        }
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_building_detection()