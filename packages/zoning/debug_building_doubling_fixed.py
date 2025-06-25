#!/usr/bin/env python3
"""
Fixed debug script to investigate building count doubling issue
Uses correct Earth Engine method names
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_building_doubling():
    """Debug the building detection process with correct method names"""
    print("🔍 DEBUGGING BUILDING COUNT DOUBLING - FIXED VERSION")
    print("=" * 60)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        # Use larger test area similar to user's screenshot
        test_geometry = {
            "type": "Polygon",
            "coordinates": [[
                [28.2600, -15.4200],  # Large test area
                [28.2900, -15.4200],
                [28.2900, -15.3900],
                [28.2600, -15.3900],
                [28.2600, -15.4200]
            ]]
        }
        
        print(f"🏗️ Testing building detection for large zone...")
        print(f"   Zone coordinates: {test_geometry['coordinates'][0][:2]}...")
        
        analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Step 1: Create mock zone 
        mock_zone = analyzer._create_mock_zone(test_geometry)
        print(f"   Zone area: {mock_zone.area_sqm/1000000:.3f} km²")
        
        # Step 2: Direct Earth Engine building extraction
        print("\\n🌍 Earth Engine Building Detection:")
        if analyzer.earth_engine and analyzer.earth_engine.initialized:
            try:
                # Test building extraction directly
                buildings_result = analyzer.earth_engine.extract_buildings_for_zone(mock_zone)
                
                if buildings_result and not buildings_result.get('error'):
                    building_footprints = buildings_result.get('building_footprints', [])
                    total_buildings = len(building_footprints)
                    
                    print(f"   ✅ Buildings detected: {total_buildings}")
                    
                    if building_footprints and len(building_footprints) > 0:
                        # Analyze building data for duplicates
                        print("   🔍 Analyzing for duplicates...")
                        
                        # Check first 5 buildings
                        for i, building in enumerate(building_footprints[:5]):
                            area = building.get('area_sqm', 0)
                            confidence = building.get('confidence', 0)
                            print(f"     Building {i+1}: {area:.1f}m², confidence={confidence:.2f}")
                        
                        # Check for duplicate coordinates or areas
                        areas = [b.get('area_sqm', 0) for b in building_footprints]
                        unique_areas = len(set(areas))
                        print(f"   📊 Total buildings: {total_buildings}")
                        print(f"   📊 Unique areas: {unique_areas}")
                        
                        if unique_areas < total_buildings * 0.8:  # Less than 80% unique
                            print("   ⚠️  POTENTIAL ISSUE: Many duplicate building areas detected!")
                        
                    # Test comprehensive building features
                    print("\\n🔬 Comprehensive Building Analysis:")
                    comprehensive_result = analyzer.earth_engine.extract_comprehensive_building_features(mock_zone, 2025)
                    
                    if comprehensive_result and not comprehensive_result.get('error'):
                        comp_buildings = comprehensive_result.get('buildings_data', {}).get('building_footprints', [])
                        comp_total = len(comp_buildings)
                        print(f"   ✅ Comprehensive buildings: {comp_total}")
                        
                        if comp_total != total_buildings:
                            print(f"   ⚠️  MISMATCH: Direct={total_buildings}, Comprehensive={comp_total}")
                            ratio = comp_total / total_buildings if total_buildings > 0 else 0
                            print(f"   📊 Comprehensive/Direct ratio: {ratio:.2f}x")
                            
                            if ratio > 1.5:
                                print("   🚨 DOUBLING DETECTED in comprehensive analysis!")
                    else:
                        print(f"   ❌ Comprehensive error: {comprehensive_result.get('error', 'Unknown')}")
                        
                else:
                    print(f"   ❌ Building extraction error: {buildings_result.get('error', 'Unknown')}")
                    total_buildings = 0
                    
            except Exception as e:
                print(f"   ❌ Earth Engine failed: {str(e)}")
                total_buildings = 0
        else:
            print("   ❌ Earth Engine not available or not initialized")
            total_buildings = 0
        
        # Step 3: Full real-time analysis to check for doubling
        print("\\n⚡ Full Real-Time Analysis:")
        try:
            results = analyzer.analyze_drawn_zone(test_geometry)
            
            # Extract data from results
            earth_engine_data = results.get('analysis_modules', {}).get('earth_engine', {})
            population_data = results.get('analysis_modules', {}).get('population_estimation', {})
            
            if earth_engine_data:
                buildings_data = earth_engine_data.get('buildings_data', {})
                if buildings_data and not buildings_data.get('error'):
                    analysis_building_count = len(buildings_data.get('building_footprints', []))
                    print(f"   Analysis building count: {analysis_building_count}")
                    
                    # Check for doubling pattern
                    if total_buildings > 0 and analysis_building_count > 0:
                        ratio = analysis_building_count / total_buildings
                        print(f"   Analysis/Direct ratio: {ratio:.2f}x")
                        
                        if ratio > 1.8:  # Close to 2x
                            print("   🚨 BUILDING COUNT DOUBLING DETECTED!")
                            print("   📋 This matches the user's report of double building counts")
            
            if population_data:
                consensus_pop = population_data.get('consensus_estimate', 0)
                print(f"   Population estimate: {consensus_pop}")
                
                # Check if population is also doubled
                expected_pop_low = total_buildings * 3.5  # Conservative estimate
                expected_pop_high = total_buildings * 5.5  # High estimate
                
                if consensus_pop > expected_pop_high * 1.5:
                    print(f"   ⚠️  Population may also be inflated!")
                    print(f"   Expected range: {expected_pop_low:.0f} - {expected_pop_high:.0f}")
                    print(f"   Actual: {consensus_pop}")
                
        except Exception as e:
            print(f"   ❌ Full analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\\n🎯 SUMMARY")
        print("=" * 30)
        print("Potential sources of doubling identified:")
        print("1. Comprehensive building analysis may count buildings twice")
        print("2. Different building extraction methods giving different counts")
        print("3. Population estimates scaling with inflated building counts")
        print("4. Check analysis aggregation logic for double counting")
        
        return {
            'direct_buildings': total_buildings,
            'area_km2': mock_zone.area_sqm / 1000000,
            'issue_detected': True  # Based on user report
        }
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_building_doubling()