#!/usr/bin/env python3
"""
Final debug script to trace the exact source of population doubling
Focus on the interaction between GHSL data and population estimator ensemble
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def trace_doubling_source():
    """Trace the exact source of population doubling with detailed logging"""
    print("🔍 TRACING POPULATION DOUBLING - FINAL DEBUG")
    print("=" * 60)
    
    try:
        from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer
        
        # Use the same test area as debug scripts
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
        
        print(f"🎯 Testing large zone for doubling pattern...")
        
        analyzer = EnhancedRealTimeZoneAnalyzer()
        mock_zone = analyzer._create_mock_zone(test_geometry)
        
        print(f"   Zone area: {mock_zone.area_sqm/1000000:.3f} km²")
        print(f"   Initial estimated_population: {getattr(mock_zone, 'estimated_population', 'None')}")
        
        # Step 1: Direct Earth Engine analysis
        print("\\n🌍 STEP 1: Earth Engine Analysis")
        if analyzer.earth_engine and analyzer.earth_engine.initialized:
            try:
                # First try comprehensive building features (this includes GHSL)
                comprehensive_result = analyzer.earth_engine.extract_comprehensive_building_features(mock_zone, 2025)
                
                if comprehensive_result and not comprehensive_result.get('error'):
                    # Extract GHSL population data
                    ghsl_data = comprehensive_result.get('ghsl_population', {})
                    if ghsl_data and not ghsl_data.get('error'):
                        ghsl_population = ghsl_data.get('estimated_population', 0)
                        print(f"   ✅ GHSL Population from comprehensive: {ghsl_population}")
                    else:
                        ghsl_population = 0
                        print(f"   ❌ GHSL error: {ghsl_data.get('error', 'No data')}")
                    
                    # Extract building data
                    buildings_data = comprehensive_result.get('buildings_data', {})
                    if buildings_data and not buildings_data.get('error'):
                        building_footprints = buildings_data.get('building_footprints', [])
                        building_count = len(building_footprints)
                        print(f"   ✅ Buildings detected: {building_count}")
                    else:
                        building_count = 0
                        print(f"   ❌ Buildings error: {buildings_data.get('error', 'No data')}")
                else:
                    print(f"   ❌ Comprehensive analysis failed: {comprehensive_result.get('error', 'Unknown')}")
                    ghsl_population = 0
                    building_count = 0
            
            except Exception as e:
                print(f"   ❌ Earth Engine analysis failed: {str(e)}")
                ghsl_population = 0
                building_count = 0
        else:
            print("   ❌ Earth Engine not available")
            ghsl_population = 0
            building_count = 0
        
        # Step 2: Population Estimator Analysis 
        print("\\n👥 STEP 2: Population Estimator Analysis")
        if analyzer.population_estimator and building_count > 0:
            try:
                # Create buildings DataFrame for testing
                import pandas as pd
                buildings_df = pd.DataFrame([
                    {'area': 100, 'building_type': 'residential', 'settlement_type': 'formal'}
                    for _ in range(building_count)
                ])
                
                print(f"   Input: {len(buildings_df)} buildings")
                
                # Test ensemble method
                ensemble_result = analyzer.population_estimator.estimate_population_ensemble(
                    buildings_df, zone_area_sqm=mock_zone.area_sqm
                )
                
                if ensemble_result and not ensemble_result.get('error'):
                    ensemble_population = ensemble_result.get('total_population', 0)
                    print(f"   ✅ Ensemble population: {ensemble_population}")
                    
                    # Show individual method contributions
                    method_estimates = ensemble_result.get('method_estimates', {})
                    for method, estimate in method_estimates.items():
                        print(f"     {method}: {estimate:.0f}")
                    
                    # Check if ensemble is realistic
                    buildings_based_estimate = building_count * 4.2  # Simple estimate
                    ratio = ensemble_population / buildings_based_estimate if buildings_based_estimate > 0 else 0
                    print(f"   📊 Ensemble vs Simple ratio: {ratio:.2f}x")
                    
                else:
                    ensemble_population = 0
                    print(f"   ❌ Ensemble failed: {ensemble_result.get('error', 'Unknown')}")
            
            except Exception as e:
                print(f"   ❌ Population estimator failed: {str(e)}")
                ensemble_population = 0
        else:
            ensemble_population = 0
            print("   ❌ Population estimator not available or no buildings")
        
        # Step 3: Full Analysis - Check How They Combine
        print("\\n⚡ STEP 3: Full Real-Time Analysis")
        try:
            results = analyzer.analyze_drawn_zone(test_geometry)
            
            # Extract Earth Engine results
            earth_engine_data = results.get('analysis_modules', {}).get('earth_engine', {})
            if earth_engine_data:
                ee_population = earth_engine_data.get('estimated_population', 0)
                ee_source = earth_engine_data.get('population_source', 'Unknown')
                print(f"   Earth Engine population: {ee_population} (source: {ee_source})")
            
            # Extract Population Estimation results
            population_data = results.get('analysis_modules', {}).get('population_estimation', {})
            if population_data:
                consensus_pop = population_data.get('consensus_estimate', 0)
                print(f"   Population estimation consensus: {consensus_pop}")
                
                # Show individual method results
                methods = population_data.get('estimation_methods', {})
                for method_name, method_data in methods.items():
                    if isinstance(method_data, dict):
                        pop_estimate = method_data.get('estimated_population', method_data.get('total_population', 0))
                        print(f"     {method_name}: {pop_estimate}")
            
            # Check if final population is double
            final_population = getattr(mock_zone, 'estimated_population', 0)
            print(f"   Final mock_zone population: {final_population}")
            
            # Analysis for doubling pattern
            print("\\n🔍 DOUBLING ANALYSIS:")
            sources = []
            if ghsl_population > 0:
                sources.append(('GHSL', ghsl_population))
            if ensemble_population > 0:
                sources.append(('Ensemble', ensemble_population))
            if ee_population > 0:
                sources.append(('Earth Engine', ee_population))
            if consensus_pop > 0:
                sources.append(('Consensus', consensus_pop))
            
            for source_name, pop_value in sources:
                print(f"   {source_name}: {pop_value}")
            
            # Check for doubling pattern
            if len(sources) >= 2:
                ratios = []
                for i, (name1, pop1) in enumerate(sources):
                    for j, (name2, pop2) in enumerate(sources[i+1:], i+1):
                        if pop2 > 0:
                            ratio = pop1 / pop2
                            ratios.append((name1, name2, ratio))
                            print(f"   {name1}/{name2} ratio: {ratio:.2f}x")
                
                # Check if any ratio is close to 2 (indicating doubling)
                for name1, name2, ratio in ratios:
                    if 1.8 <= ratio <= 2.2:
                        print(f"   🚨 DOUBLING DETECTED: {name1} is ~2x {name2}!")
                        print(f"      This suggests {name1} may be incorrectly calculated or combined")
            
        except Exception as e:
            print(f"   ❌ Full analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\\n🎯 CONCLUSION")
        print("=" * 30)
        print("Based on this analysis:")
        print("1. Check if GHSL and Ensemble estimates are being ADDED instead of using one")
        print("2. Verify that the 'consensus_estimate' properly selects the best source")
        print("3. Ensure Earth Engine population and PopulationEstimator don't both contribute")
        print("4. The user's manual count suggests the actual value should be ~half current estimate")
        
        return {
            'ghsl_population': ghsl_population,
            'ensemble_population': ensemble_population,
            'building_count': building_count,
            'area_km2': mock_zone.area_sqm / 1000000,
            'issue_likely': True
        }
        
    except Exception as e:
        print(f"❌ Trace failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    trace_doubling_source()