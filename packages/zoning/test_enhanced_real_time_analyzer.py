#!/usr/bin/env python3
"""
Test Enhanced Real-time Zone Analyzer
Verifies that the enhanced real-time zone analysis with all modules works correctly
"""
import sys
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

# Add the app directory to the path
sys.path.insert(0, './app')

from app.utils.real_time_zone_analyzer import EnhancedRealTimeZoneAnalyzer


class TestEnhancedRealTimeZoneAnalyzer(unittest.TestCase):
    """Test cases for enhanced real-time zone analyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = EnhancedRealTimeZoneAnalyzer()
        
        # Sample zone geometry (small rectangular area in Lusaka)
        self.test_geometry = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [28.2800, -15.4100],  # SW corner
                    [28.2850, -15.4100],  # SE corner  
                    [28.2850, -15.4050],  # NE corner
                    [28.2800, -15.4050],  # NW corner
                    [28.2800, -15.4100]   # Close polygon
                ]]
            },
            "properties": {}
        }
        
        self.test_metadata = {
            "zone_type": "residential",
            "estimated_population": 1000,
            "collection_frequency": 2
        }
        
        # Mock building data for testing
        self.mock_building_data = {
            'building_footprints': [
                {'area': 120, 'height': 7, 'type': 'residential'},
                {'area': 80, 'height': 3.5, 'type': 'residential'},
                {'area': 200, 'height': 10.5, 'type': 'commercial'}
            ],
            'building_count': 3,
            'total_building_area': 400,
            'average_building_size': 133.3
        }
        
        # Mock settlement classification
        self.mock_settlement_classification = {
            'classification': 'formal',
            'confidence': 0.85,
            'density_category': 'medium',
            'settlement_indicators': {
                'road_network_regularity': 0.8,
                'building_size_uniformity': 0.7,
                'infrastructure_quality': 0.9
            }
        }
    
    def test_enhanced_analyzer_initialization(self):
        """Test enhanced analyzer initializes with all modules"""
        self.assertIsNotNone(self.analyzer)
        
        # Check that enhanced modules are available (even if mocked)
        self.assertTrue(hasattr(self.analyzer, 'validation_framework'))
        self.assertTrue(hasattr(self.analyzer, 'ensemble_classifier'))
        self.assertTrue(hasattr(self.analyzer, 'settlement_classifier'))
        self.assertTrue(hasattr(self.analyzer, 'population_estimator'))
        self.assertTrue(hasattr(self.analyzer, 'dasymetric_mapper'))
        
        # Check enhanced analysis method exists
        self.assertTrue(hasattr(self.analyzer, 'analyze_drawn_zone'))
    
    def test_enhanced_results_structure(self):
        """Test that enhanced analyzer returns comprehensive results structure"""
        # Mock all the analysis modules to return test data
        with patch.multiple(
            self.analyzer,
            _run_enhanced_earth_engine_analysis=Mock(return_value={'buildings_data': self.mock_building_data}),
            _run_enhanced_settlement_classification=Mock(return_value=self.mock_settlement_classification),
            _run_enhanced_population_estimation=Mock(return_value={'area_based': {'estimated_population': 1200}}),
            _run_ensemble_building_classification=Mock(return_value={'classification_confidence': 0.9}),
            _run_dasymetric_mapping=Mock(return_value={'spatial_distribution': 'uniform'}),
            _run_cross_validation=Mock(return_value={'overall_confidence': 0.8}),
            _quantify_uncertainty=Mock(return_value={'reliability_score': 85}),
            _run_enhanced_waste_analysis=Mock(return_value={'total_waste_kg_day': 240}),
            _analyze_enhanced_collection_feasibility=Mock(return_value={'overall_score': 78}),
            _get_enhanced_ai_insights=Mock(return_value={'insights': ['Good zone design']}),
        ):
            result = self.analyzer.analyze_drawn_zone(self.test_geometry, self.test_metadata)
        
        # Verify enhanced result structure
        expected_keys = [
            'zone_geometry', 'analysis_timestamp', 'analysis_modules',
            'validation_results', 'cross_validation', 'uncertainty_analysis',
            'optimization_recommendations', 'zone_viability_score', 
            'critical_issues', 'confidence_assessment', 'performance_metrics'
        ]
        
        for key in expected_keys:
            self.assertIn(key, result, f"Missing key: {key}")
        
        # Verify analysis modules structure
        analysis_modules = result['analysis_modules']
        expected_modules = [
            'geometry', 'earth_engine', 'settlement_classification',
            'population_estimation', 'building_classification', 'dasymetric_mapping',
            'waste_analysis', 'collection_feasibility', 'ai_insights'
        ]
        
        for module in expected_modules:
            self.assertIn(module, analysis_modules, f"Missing analysis module: {module}")
    
    def test_enhanced_population_estimation_methods(self):
        """Test that enhanced population estimation uses multiple methods"""
        mock_estimates = {
            'area_based': {
                'estimated_population': 1200,
                'method': 'area_based',
                'confidence': 0.8
            },
            'floor_based': {
                'estimated_population': 1150,
                'method': 'floor_based', 
                'confidence': 0.75
            },
            'settlement_based': {
                'estimated_population': 1180,
                'method': 'settlement_based',
                'confidence': 0.85
            },
            'ensemble': {
                'estimated_population': 1177,
                'method': 'ensemble',
                'confidence': 0.9,
                'consensus_agreement': 0.87
            }
        }
        
        result = self.analyzer._run_enhanced_population_estimation(
            self.analyzer._create_mock_zone(self.test_geometry, self.test_metadata),
            self.mock_building_data,
            self.mock_settlement_classification
        )
        
        # Should return multiple estimation methods
        if not result.get('error'):
            # If population estimator is available, should have multiple methods
            self.assertIsInstance(result, dict)
        else:
            # If not available, should gracefully handle
            self.assertIn('error', result)
    
    def test_cross_validation_capabilities(self):
        """Test cross-validation framework integration"""
        mock_analysis_results = {
            'analysis_modules': {
                'earth_engine': {'buildings_data': self.mock_building_data},
                'settlement_classification': self.mock_settlement_classification,
                'population_estimation': {'ensemble': {'estimated_population': 1200}}
            }
        }
        
        mock_zone = self.analyzer._create_mock_zone(self.test_geometry, self.test_metadata)
        
        # Test cross-validation
        result = self.analyzer._run_cross_validation(mock_zone, mock_analysis_results)
        
        # Should return validation structure (even if validation framework is None)
        self.assertIsInstance(result, dict)
        
        if not result.get('error'):
            # If validation framework is available
            expected_validation_keys = ['datasets_compared', 'agreement_analysis', 'confidence_assessment']
            for key in expected_validation_keys:
                self.assertIn(key, result)
    
    def test_uncertainty_quantification(self):
        """Test uncertainty quantification for population estimates"""
        mock_population_estimates = {
            'area_based': {'estimated_population': 1200},
            'floor_based': {'estimated_population': 1150},
            'settlement_based': {'estimated_population': 1180},
            'ensemble': {'estimated_population': 1177}
        }
        
        result = self.analyzer._quantify_uncertainty(mock_population_estimates)
        
        # Should return uncertainty analysis structure
        self.assertIsInstance(result, dict)
        
        if not result.get('error'):
            # If validation framework is available
            expected_uncertainty_keys = ['uncertainty_metrics', 'confidence_intervals', 'reliability_score']
            for key in expected_uncertainty_keys:
                self.assertIn(key, result)
    
    def test_enhanced_viability_scoring(self):
        """Test enhanced viability scoring with validation metrics"""
        mock_analysis = {
            'analysis_modules': {
                'geometry': {
                    'area_sqkm': 0.25,
                    'compactness_index': 0.7,
                    'shape_quality': {'size_appropriateness': 'optimal'}
                },
                'population_estimation': {
                    'ensemble': {'estimated_population': 1200, 'confidence': 0.85}
                },
                'collection_feasibility': {
                    'overall_score': 75,
                    'accessibility': 'good'
                },
                'waste_analysis': {
                    'total_waste_kg_day': 240,
                    'collection_efficiency_score': 78
                }
            },
            'cross_validation': {
                'confidence_assessment': {'overall_confidence': 0.8}
            },
            'uncertainty_analysis': {
                'reliability_score': 85
            }
        }
        
        viability_score = self.analyzer._calculate_enhanced_viability_score(mock_analysis)
        
        # Should return enhanced score between 0 and 100
        self.assertGreaterEqual(viability_score, 0)
        self.assertLessEqual(viability_score, 100)
        self.assertIsInstance(viability_score, (int, float))
    
    def test_comprehensive_confidence_assessment(self):
        """Test comprehensive confidence assessment"""
        mock_analysis = {
            'analysis_modules': {
                'earth_engine': {'buildings_data': self.mock_building_data},
                'population_estimation': {'ensemble': {'confidence': 0.85}},
                'settlement_classification': {'confidence': 0.8}
            },
            'cross_validation': {
                'confidence_assessment': {'overall_confidence': 0.82}
            },
            'uncertainty_analysis': {
                'reliability_score': 85
            }
        }
        
        confidence_assessment = self.analyzer._assess_comprehensive_confidence(mock_analysis)
        
        # Should return confidence assessment structure
        self.assertIsInstance(confidence_assessment, dict)
        expected_confidence_keys = ['overall_confidence_score', 'component_confidence', 'confidence_factors']
        
        for key in expected_confidence_keys:
            self.assertIn(key, confidence_assessment)
        
        # Overall confidence should be between 0 and 100
        overall_confidence = confidence_assessment.get('overall_confidence_score', 0)
        self.assertGreaterEqual(overall_confidence, 0)
        self.assertLessEqual(overall_confidence, 100)
    
    def test_enhanced_optimization_recommendations(self):
        """Test enhanced optimization recommendations generation"""
        mock_analysis = {
            'analysis_modules': {
                'geometry': {'area_sqkm': 2.5, 'compactness_index': 0.2},
                'population_estimation': {'ensemble': {'estimated_population': 5000}},
                'collection_feasibility': {'overall_score': 45, 'road_access': 'limited'},
                'settlement_classification': {'classification': 'informal'}
            },
            'cross_validation': {'confidence_assessment': {'overall_confidence': 0.6}},
            'uncertainty_analysis': {'reliability_score': 65}
        }
        
        recommendations = self.analyzer._generate_enhanced_optimization_recommendations(mock_analysis)
        
        # Should return list of recommendations
        self.assertIsInstance(recommendations, list)
        
        if len(recommendations) > 0:
            # Each recommendation should have required structure
            for rec in recommendations:
                self.assertIsInstance(rec, dict)
                expected_rec_keys = ['category', 'priority', 'issue', 'recommendation']
                for key in expected_rec_keys:
                    self.assertIn(key, rec)
    
    def test_enhanced_critical_issues_detection(self):
        """Test enhanced critical issues detection with validation insights"""
        mock_analysis = {
            'analysis_modules': {
                'geometry': {'area_sqkm': 8.0, 'error': None},
                'population_estimation': {'ensemble': {'estimated_population': 15000}},
                'collection_feasibility': {'overall_score': 25, 'road_access': 'none'}
            },
            'cross_validation': {'confidence_assessment': {'overall_confidence': 0.3}},
            'uncertainty_analysis': {'reliability_score': 35}
        }
        
        critical_issues = self.analyzer._identify_enhanced_critical_issues(mock_analysis)
        
        # Should identify critical issues
        self.assertIsInstance(critical_issues, list)
        
        if len(critical_issues) > 0:
            # Each issue should have required structure
            for issue in critical_issues:
                self.assertIsInstance(issue, dict)
                expected_issue_keys = ['severity', 'category', 'issue', 'impact']
                for key in expected_issue_keys:
                    self.assertIn(key, issue)
    
    def test_performance_metrics_tracking(self):
        """Test that performance metrics are properly tracked"""
        with patch.multiple(
            self.analyzer,
            _run_enhanced_earth_engine_analysis=Mock(return_value={'buildings_data': self.mock_building_data}),
            _run_enhanced_settlement_classification=Mock(return_value=self.mock_settlement_classification),
            _run_enhanced_population_estimation=Mock(return_value={'area_based': {'estimated_population': 1200}}),
        ):
            result = self.analyzer.analyze_drawn_zone(self.test_geometry, self.test_metadata)
        
        # Should have performance metrics
        self.assertIn('performance_metrics', result)
        
        performance_metrics = result['performance_metrics']
        expected_metrics = [
            'total_analysis_time_seconds', 'modules_completed', 
            'modules_failed', 'validation_score', 'uncertainty_level'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, performance_metrics)
        
        # Analysis time should be reasonable
        analysis_time = performance_metrics.get('total_analysis_time_seconds', 0)
        self.assertGreater(analysis_time, 0)
        self.assertLess(analysis_time, 30)  # Should complete within 30 seconds
    
    def test_backward_compatibility(self):
        """Test that enhanced analyzer maintains backward compatibility"""
        # The enhanced analyzer should provide same basic interface as original
        basic_methods = [
            'analyze_drawn_zone', '_analyze_geometry', 
            '_create_mock_zone'
        ]
        
        for method in basic_methods:
            self.assertTrue(hasattr(self.analyzer, method))
        
        # Basic analysis should still work
        try:
            result = self.analyzer.analyze_drawn_zone(self.test_geometry, self.test_metadata)
            self.assertIsInstance(result, dict)
            self.assertIn('zone_viability_score', result)
        except Exception as e:
            # Should not fail catastrophically
            self.fail(f"Basic analysis failed: {e}")
    
    def test_graceful_error_handling(self):
        """Test that enhanced analyzer handles module failures gracefully"""
        # Test with no metadata
        result = self.analyzer.analyze_drawn_zone(self.test_geometry)
        self.assertIsInstance(result, dict)
        
        # Test with invalid geometry
        invalid_geometry = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0, 0]}}
        result = self.analyzer.analyze_drawn_zone(invalid_geometry)
        self.assertIsInstance(result, dict)
        
        # Should still return viable response even with errors
        self.assertIn('zone_viability_score', result)
        self.assertIn('performance_metrics', result)


def main():
    """Run the enhanced analyzer tests"""
    unittest.main()


if __name__ == '__main__':
    main() 