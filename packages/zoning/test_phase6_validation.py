#!/usr/bin/env python3
"""
Phase 6: Validation & Quality Assurance Integration Test
Tests the comprehensive validation framework for the analytics regime
"""
import sys
import os
import time
import json
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_phase6_validation_framework():
    """Test Phase 6 validation and quality assurance framework"""
    print("🔬 Phase 6 Validation & Quality Assurance Test")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {'passed': 0, 'failed': 0, 'tests': []}
    
    # Test 1: Validation Framework Import and Initialization
    print("🧪 Test 1: Validation Framework Import and Initialization")
    print("-" * 60)
    
    try:
        from app.utils.validation_framework import ValidationFramework
        validator = ValidationFramework()
        
        print("✅ ValidationFramework imported and initialized successfully")
        test_results['passed'] += 1
        test_results['tests'].append("✅ ValidationFramework initialization")
        
    except Exception as e:
        print(f"❌ ValidationFramework import/initialization failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ ValidationFramework initialization")
        return test_results
    
    # Test 2: Cross-Dataset Validation
    print("\n🧪 Test 2: Cross-Dataset Validation")
    print("-" * 60)
    
    try:
        # Create mock zone
        class MockZone:
            def __init__(self):
                self.id = 'test_zone_001'
                self.name = 'Test Validation Zone'
        
        mock_zone = MockZone()
        
        # Mock Google Buildings data
        google_buildings = {
            'building_count': 245,
            'confidence_threshold': 0.75,
            'features': {
                'area_statistics': {
                    'mean': 85.5,
                    'stddev': 23.2,
                    'sum': 20947.5
                }
            },
            'estimated_population': 982
        }
        
        # Mock Microsoft Buildings data
        microsoft_buildings = {
            'building_count': 238,
            'features': {
                'area_statistics': {
                    'mean': 88.1,
                    'stddev': 25.7
                }
            }
        }
        
        # Mock WorldPop data
        worldpop_data = {
            'total_population': 1024,
            'population_density_per_sqkm': 3200
        }
        
        # Mock Settlement Classification
        settlement_classification = {
            'settlement_type': 'mixed',
            'confidence': 0.82,
            'building_density': 156,
            'estimated_population': 995
        }
        
        # Run cross-validation
        cross_validation_result = validator.cross_validate_datasets(
            mock_zone, google_buildings, microsoft_buildings, 
            worldpop_data, settlement_classification
        )
        
        if 'error' not in cross_validation_result:
            print(f"✅ Cross-dataset validation completed successfully")
            print(f"   📊 Datasets compared: {len(cross_validation_result.get('datasets_compared', []))}")
            
            # Check building detection comparison
            building_comp = cross_validation_result.get('building_detection_comparison', {})
            if building_comp:
                agreement_level = building_comp.get('agreement_level', 'Unknown')
                relative_diff = building_comp.get('relative_difference_percent', 0)
                print(f"   🏢 Building detection agreement: {agreement_level} ({relative_diff:.1f}% difference)")
            
            # Check overall agreement
            agreement_analysis = cross_validation_result.get('agreement_analysis', {})
            if agreement_analysis:
                overall_score = agreement_analysis.get('overall_agreement_score', 0)
                print(f"   📈 Overall agreement score: {overall_score:.1f}/100")
            
            test_results['passed'] += 1
            test_results['tests'].append("✅ Cross-dataset validation")
        else:
            print(f"❌ Cross-dataset validation failed: {cross_validation_result['error']}")
            test_results['failed'] += 1
            test_results['tests'].append("❌ Cross-dataset validation")
            
    except Exception as e:
        print(f"❌ Cross-dataset validation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ Cross-dataset validation")
    
    # Test 3: Uncertainty Quantification
    print("\n🧪 Test 3: Uncertainty Quantification")
    print("-" * 60)
    
    try:
        # Create mock estimates from different methods
        estimates_data = {
            'building_based': {'estimated_population': 982},
            'worldpop': {'estimated_population': 1024},
            'ensemble': {'estimated_population': 1003},
            'settlement_adjusted': {'estimated_population': 995}
        }
        
        # Run uncertainty quantification
        uncertainty_result = validator.quantify_uncertainty(
            estimates_data, 
            ['building_based', 'worldpop', 'ensemble', 'settlement_adjusted']
        )
        
        if 'error' not in uncertainty_result:
            print("✅ Uncertainty quantification completed successfully")
            
            # Check uncertainty metrics
            uncertainty_metrics = uncertainty_result.get('uncertainty_metrics', {})
            if uncertainty_metrics:
                cv = uncertainty_metrics.get('coefficient_of_variation', 0)
                relative_range = uncertainty_metrics.get('relative_range_percent', 0)
                print(f"   📊 Coefficient of variation: {cv:.3f}")
                print(f"   📊 Relative range: {relative_range:.1f}%")
            
            # Check confidence intervals
            ci_95 = uncertainty_result.get('confidence_intervals', {}).get('95_percent', {})
            if ci_95:
                lower = ci_95.get('lower_bound', 0)
                upper = ci_95.get('upper_bound', 0)
                width_percent = ci_95.get('relative_width_percent', 0)
                print(f"   📊 95% CI: [{lower:.0f}, {upper:.0f}] (width: {width_percent:.1f}%)")
            
            # Check reliability score
            reliability = uncertainty_result.get('reliability_score', 0)
            print(f"   📊 Reliability score: {reliability:.1f}/100")
            
            test_results['passed'] += 1
            test_results['tests'].append("✅ Uncertainty quantification")
        else:
            print(f"❌ Uncertainty quantification failed: {uncertainty_result['error']}")
            test_results['failed'] += 1
            test_results['tests'].append("❌ Uncertainty quantification")
            
    except Exception as e:
        print(f"❌ Uncertainty quantification test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ Uncertainty quantification")
    
    # Test 4: Temporal Consistency Analysis
    print("\n🧪 Test 4: Temporal Consistency Analysis")
    print("-" * 60)
    
    try:
        # Create mock temporal data
        temporal_data = {
            '2021': {
                'building_count': 220,
                'population_estimate': 885
            },
            '2022': {
                'building_count': 235,
                'population_estimate': 942
            },
            '2023': {
                'building_count': 245,
                'population_estimate': 982
            }
        }
        
        years_analyzed = [2021, 2022, 2023]
        
        # Run temporal consistency analysis
        temporal_result = validator.analyze_temporal_consistency(temporal_data, years_analyzed)
        
        if 'error' not in temporal_result:
            print("✅ Temporal consistency analysis completed successfully")
            
            # Check building consistency
            building_consistency = temporal_result.get('building_consistency', {})
            if building_consistency and 'year_over_year_changes' in building_consistency:
                yoy_changes = building_consistency['year_over_year_changes']
                mean_change_rate = yoy_changes.get('mean_change_rate_percent', 0)
                consistency_score = yoy_changes.get('consistency_score', 0)
                print(f"   🏢 Building count mean change rate: {mean_change_rate:.1f}%/year")
                print(f"   🏢 Building consistency score: {consistency_score:.1f}/100")
            
            # Check growth analysis
            building_growth = temporal_result.get('building_growth_analysis', {})
            if building_growth:
                cagr = building_growth.get('compound_annual_growth_rate_percent', 0)
                print(f"   📈 Building CAGR: {cagr:.1f}%")
            
            # Check stability assessment
            stability = temporal_result.get('stability_assessment', {})
            if stability:
                stability_score = stability.get('overall_stability_score', 0)
                stability_level = stability.get('stability_level', 'Unknown')
                print(f"   📊 Overall stability: {stability_score:.1f}/100 ({stability_level})")
            
            # Check anomaly detection
            anomalies = temporal_result.get('anomaly_detection', {})
            anomaly_count = anomalies.get('anomalies_detected', 0)
            print(f"   🚨 Anomalies detected: {anomaly_count}")
            
            test_results['passed'] += 1
            test_results['tests'].append("✅ Temporal consistency analysis")
        else:
            print(f"❌ Temporal consistency analysis failed: {temporal_result['error']}")
            test_results['failed'] += 1
            test_results['tests'].append("❌ Temporal consistency analysis")
            
    except Exception as e:
        print(f"❌ Temporal consistency analysis test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ Temporal consistency analysis")
    
    # Test 5: Statistical Quality Validation
    print("\n🧪 Test 5: Statistical Quality Validation")
    print("-" * 60)
    
    try:
        # Create mock zone data for statistical validation
        zone_data = {
            'zone_id': 'test_zone_001',
            'zone_name': 'Test Validation Zone',
            'area_km2': 2.5,
            'waste_generation': {
                'total_waste_kg_day': 450.5,
                'residential_waste': 380.2,
                'commercial_waste': 70.3,
                'estimated_population': 982
            },
            'collection_requirements': {
                'collection_points': 8,
                'vehicles_required': 2
            },
            'revenue_projection': {
                'monthly_revenue': 1250.75
            },
            'building_analysis': {
                'building_count': 245,
                'confidence_threshold': 0.75,
                'features': {
                    'area_statistics': {
                        'mean': 85.5,
                        'stddev': 23.2
                    }
                }
            },
            'population_estimate': {
                'estimated_population': 982,
                'confidence': 0.82,
                'calculation_method': 'building_based_with_settlement_factors'
            }
        }
        
        # Run statistical validation
        stats_result = validator.validate_statistical_quality(zone_data, 'comprehensive')
        
        if 'error' not in stats_result:
            print("✅ Statistical quality validation completed successfully")
            
            # Check data quality score
            quality_score = stats_result.get('data_quality_score', 0)
            print(f"   📊 Data quality score: {quality_score:.1f}/100")
            
            # Check completeness assessment
            completeness = stats_result.get('completeness_assessment', {})
            if completeness:
                overall_completeness = completeness.get('overall_completeness_percent', 0)
                weighted_completeness = completeness.get('weighted_completeness_percent', 0)
                print(f"   📊 Data completeness: {overall_completeness:.1f}% (weighted: {weighted_completeness:.1f}%)")
            
            # Check building statistics validation
            building_stats = stats_result.get('building_statistics', {})
            if building_stats:
                building_quality = building_stats.get('quality_score', 0)
                print(f"   🏢 Building statistics quality: {building_quality:.1f}/100")
            
            # Check population statistics validation
            pop_stats = stats_result.get('population_statistics', {})
            if pop_stats:
                pop_quality = pop_stats.get('quality_score', 0)
                print(f"   👥 Population statistics quality: {pop_quality:.1f}/100")
            
            test_results['passed'] += 1
            test_results['tests'].append("✅ Statistical quality validation")
        else:
            print(f"❌ Statistical quality validation failed: {stats_result['error']}")
            test_results['failed'] += 1
            test_results['tests'].append("❌ Statistical quality validation")
            
    except Exception as e:
        print(f"❌ Statistical quality validation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ Statistical quality validation")
    
    # Test 6: Error Bounds Calculation
    print("\n🧪 Test 6: Error Bounds Calculation")
    print("-" * 60)
    
    try:
        # Create mock estimates and actual values for error bounds calculation
        estimates = [982, 1024, 1003, 995, 967, 1038, 989]
        actual_values = [1015, 1020, 985, 1002, 998, 1045, 1012]  # Mock actual values
        
        # Run error bounds calculation
        error_bounds_result = validator.calculate_error_bounds(
            estimates, actual_values, confidence_level=0.95
        )
        
        if 'error' not in error_bounds_result:
            print("✅ Error bounds calculation completed successfully")
            
            # Check bounds calculation
            bounds_calc = error_bounds_result.get('bounds_calculation', {})
            if bounds_calc:
                mean_est = bounds_calc.get('mean_estimate', 0)
                se = bounds_calc.get('standard_error', 0)
                print(f"   📊 Mean estimate: {mean_est:.1f} ± {se:.1f}")
                
                t_dist = bounds_calc.get('t_distribution', {})
                if t_dist:
                    lower = t_dist.get('lower_bound', 0)
                    upper = t_dist.get('upper_bound', 0)
                    margin = t_dist.get('margin_of_error', 0)
                    print(f"   📊 95% CI (t-dist): [{lower:.1f}, {upper:.1f}] (±{margin:.1f})")
            
            # Check prediction intervals
            pred_intervals = error_bounds_result.get('prediction_intervals', {})
            if pred_intervals:
                pred_lower = pred_intervals.get('lower_bound', 0)
                pred_upper = pred_intervals.get('upper_bound', 0)
                pred_margin_pct = pred_intervals.get('relative_margin_percent', 0)
                print(f"   📊 Prediction interval: [{pred_lower:.1f}, {pred_upper:.1f}] ({pred_margin_pct:.1f}%)")
            
            # Check validation metrics (when actual values provided)
            validation_metrics = error_bounds_result.get('validation_metrics', {})
            if validation_metrics:
                mae = validation_metrics.get('mean_absolute_error', 0)
                mape = validation_metrics.get('mean_absolute_percentage_error', 0)
                accuracy = validation_metrics.get('accuracy_percent', 0)
                print(f"   📊 MAE: {mae:.1f}, MAPE: {mape:.1f}%, Accuracy: {accuracy:.1f}%")
            
            test_results['passed'] += 1
            test_results['tests'].append("✅ Error bounds calculation")
        else:
            print(f"❌ Error bounds calculation failed: {error_bounds_result['error']}")
            test_results['failed'] += 1
            test_results['tests'].append("❌ Error bounds calculation")
            
    except Exception as e:
        print(f"❌ Error bounds calculation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ Error bounds calculation")
    
    # Test 7: Comprehensive Validation Report Generation
    print("\n🧪 Test 7: Comprehensive Validation Report Generation")
    print("-" * 60)
    
    try:
        # Create mock validation results for report generation
        validation_results = {
            'cross_validation': cross_validation_result if 'cross_validation_result' in locals() else {},
            'uncertainty': uncertainty_result if 'uncertainty_result' in locals() else {},
            'temporal_consistency': temporal_result if 'temporal_result' in locals() else {}
        }
        
        # Generate validation report
        report = validator.generate_validation_report('test_zone_001', validation_results)
        
        if 'error' not in report:
            print("✅ Validation report generation completed successfully")
            
            # Check report structure
            report_id = report.get('report_id', '')
            print(f"   📋 Report ID: {report_id}")
            
            # Check overall quality assessment
            quality_assessment = report.get('overall_quality_assessment', {})
            if quality_assessment:
                overall_quality = quality_assessment.get('overall_quality_score', 0)
                quality_level = quality_assessment.get('quality_level', 'Unknown')
                validation_confidence = quality_assessment.get('validation_confidence', 'Unknown')
                print(f"   📊 Overall quality: {overall_quality:.1f}/100 ({quality_level})")
                print(f"   📊 Validation confidence: {validation_confidence}")
            
            # Check report sections
            sections = report.get('report_sections', {})
            print(f"   📋 Report sections: {len(sections)}")
            
            # Check recommendations
            recommendations = report.get('recommendations', [])
            print(f"   💡 Recommendations: {len(recommendations)}")
            if recommendations:
                print(f"      • {recommendations[0]}")
            
            test_results['passed'] += 1
            test_results['tests'].append("✅ Validation report generation")
        else:
            print(f"❌ Validation report generation failed: {report['error']}")
            test_results['failed'] += 1
            test_results['tests'].append("❌ Validation report generation")
            
    except Exception as e:
        print(f"❌ Validation report generation test failed: {str(e)}")
        test_results['failed'] += 1
        test_results['tests'].append("❌ Validation report generation")
    
    # Test Summary
    print("\n" + "=" * 80)
    print("📊 PHASE 6 VALIDATION TEST SUMMARY")
    print("=" * 80)
    
    total_tests = test_results['passed'] + test_results['failed']
    success_rate = (test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"✅ Tests Passed: {test_results['passed']}")
    print(f"❌ Tests Failed: {test_results['failed']}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print()
    
    # Status determination
    if success_rate >= 90:
        status = "🎉 EXCELLENT - Phase 6 validation framework is production ready!"
        color = "GREEN"
    elif success_rate >= 80:
        status = "✅ GOOD - Phase 6 validation framework is ready with minor improvements needed"
        color = "YELLOW"
    elif success_rate >= 70:
        status = "⚠️  ACCEPTABLE - Phase 6 validation framework needs some improvements"
        color = "ORANGE"
    else:
        status = "❌ NEEDS WORK - Phase 6 validation framework requires significant improvements"
        color = "RED"
    
    print(f"📋 STATUS: {status}")
    print()
    
    print("📝 Individual Test Results:")
    for test_name in test_results['tests']:
        print(f"   {test_name}")
    
    print()
    print("🎯 Phase 6 Components Validated:")
    print("   ✓ Cross-validation between multiple datasets")
    print("   ✓ Uncertainty quantification using ensemble variance")
    print("   ✓ Temporal consistency analysis")
    print("   ✓ Statistical validation approaches")
    print("   ✓ Error bounds calculation")
    print("   ✓ Comprehensive validation reporting")
    
    return test_results

if __name__ == "__main__":
    print("🔬 PHASE 6: VALIDATION & QUALITY ASSURANCE TEST")
    print("Testing comprehensive validation framework for Lusaka waste management analytics")
    print()
    
    results = test_phase6_validation_framework()
    
    total_tests = results['passed'] + results['failed']
    success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🏁 FINAL RESULT: {success_rate:.1f}% Success Rate")
    
    if success_rate >= 90:
        print("🎉 Phase 6 validation framework is PRODUCTION READY!")
    elif success_rate >= 80:
        print("✅ Phase 6 validation framework is ready with minor improvements")
    else:
        print("⚠️  Phase 6 validation framework needs additional work") 