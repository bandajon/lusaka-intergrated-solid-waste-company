#!/usr/bin/env python3
"""
Test Real-time Zone Analyzer
Verifies that the real-time zone analysis integration works correctly
"""
import sys
import json
import unittest
from unittest.mock import Mock, patch
from flask import Flask

# Add the app directory to the path
sys.path.insert(0, './app')

from app.utils.real_time_zone_analyzer import RealTimeZoneAnalyzer


class TestRealTimeZoneAnalyzer(unittest.TestCase):
    """Test cases for real-time zone analyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = RealTimeZoneAnalyzer()
        
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
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly"""
        self.assertIsNotNone(self.analyzer)
        self.assertTrue(hasattr(self.analyzer, 'analyze_drawn_zone'))
        self.assertTrue(hasattr(self.analyzer, '_analyze_geometry'))
    
    def test_geometry_analysis(self):
        """Test basic geometry analysis"""
        result = self.analyzer._analyze_geometry(self.test_geometry)
        
        # Should have basic geometry metrics
        self.assertIn('area_sqkm', result)
        self.assertIn('perimeter_km', result)
        self.assertIn('shape_quality', result)
        
        # Area should be reasonable for the test geometry
        self.assertGreater(result['area_sqkm'], 0)
        self.assertLess(result['area_sqkm'], 1)  # Should be less than 1 km²
    
    def test_zone_viability_scoring(self):
        """Test zone viability scoring"""
        # Mock the analysis modules to return test data
        mock_analysis = {
            'geometry': {
                'area_sqkm': 0.25,
                'compactness_index': 0.7,
                'shape_quality': {'size_appropriateness': 'optimal'}
            },
            'population': {
                'consensus': 1200,
                'confidence': 85
            },
            'collection_feasibility': {
                'overall_score': 75,
                'accessibility': 'good'
            },
            'ai_insights': {
                'waste_generation_risk': 'medium',
                'collection_challenges': []
            }
        }
        
        viability_score = self.analyzer._calculate_viability_score(mock_analysis)
        
        # Should return a score between 0 and 100
        self.assertGreaterEqual(viability_score, 0)
        self.assertLessEqual(viability_score, 100)
        
        # With good inputs, should be a decent score
        self.assertGreater(viability_score, 50)
    
    def test_optimization_recommendations(self):
        """Test optimization recommendations generation"""
        mock_analysis = {
            'geometry': {
                'area_sqkm': 2.5,  # Large area
                'compactness_index': 0.2,  # Poor compactness
            },
            'population': {
                'consensus': 5000,  # High population
            },
            'collection_feasibility': {
                'overall_score': 45,  # Poor feasibility
                'road_access': 'limited'
            }
        }
        
        recommendations = self.analyzer._generate_optimization_recommendations(mock_analysis)
        
        # Should have recommendations
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should identify the area issue
        area_recommendation_found = any(
            'large' in rec.get('issue', '').lower() or 
            'split' in rec.get('recommendation', '').lower()
            for rec in recommendations
        )
        self.assertTrue(area_recommendation_found)
    
    def test_critical_issues_detection(self):
        """Test critical issues detection"""
        mock_analysis = {
            'geometry': {
                'area_sqkm': 8.0,  # Very large
                'error': None
            },
            'population': {
                'consensus': 15000,  # Very high population
            },
            'collection_feasibility': {
                'overall_score': 25,  # Very poor feasibility
                'road_access': 'none'
            }
        }
        
        critical_issues = self.analyzer._identify_critical_issues(mock_analysis)
        
        # Should identify critical issues
        self.assertIsInstance(critical_issues, list)
        self.assertGreater(len(critical_issues), 0)
        
        # Should flag the very large area
        large_area_issue_found = any(
            'large' in issue.get('issue', '').lower()
            for issue in critical_issues
        )
        self.assertTrue(large_area_issue_found)
    
    @patch('app.utils.real_time_zone_analyzer.WasteAnalyzer')
    @patch('app.utils.real_time_zone_analyzer.EarthEngineAnalyzer')
    @patch('app.utils.real_time_zone_analyzer.AIWasteAnalyzer')
    def test_full_analysis_flow(self, mock_ai, mock_ee, mock_waste):
        """Test the complete analysis workflow"""
        # Mock the analyzer responses
        mock_waste_instance = Mock()
        mock_waste_instance.analyze_zone.return_value = {
            'estimated_population': 1200,
            'waste_generation_tons_month': 24
        }
        mock_waste.return_value = mock_waste_instance
        
        mock_ee_instance = Mock()
        mock_ee_instance.analyze_zone.return_value = {
            'building_count': 45,
            'settlement_type': 'formal',
            'population_estimate': 1150
        }
        mock_ee.return_value = mock_ee_instance
        
        mock_ai_instance = Mock()
        mock_ai_instance.analyze_zone_with_context.return_value = {
            'insights': ['Good road access', 'Regular settlement pattern'],
            'recommendations': ['Standard collection frequency adequate'],
            'risk_factors': []
        }
        mock_ai.return_value = mock_ai_instance
        
        # Run the analysis
        result = self.analyzer.analyze_drawn_zone(self.test_geometry, self.test_metadata)
        
        # Verify structure
        self.assertIn('zone_viability_score', result)
        self.assertIn('analysis_modules', result)
        self.assertIn('optimization_recommendations', result)
        self.assertIn('critical_issues', result)
        self.assertIn('performance_metrics', result)
        
        # Verify score is calculated
        self.assertIsInstance(result['zone_viability_score'], (int, float))
    
    def test_geometry_validation(self):
        """Test geometry validation"""
        # Test invalid geometry
        invalid_geometry = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [28.2800, -15.4100],  # Only two points - invalid polygon
                    [28.2850, -15.4100]
                ]]
            }
        }
        
        result = self.analyzer._analyze_geometry(invalid_geometry)
        self.assertIn('error', result)
        
        # Test valid geometry
        result = self.analyzer._analyze_geometry(self.test_geometry)
        self.assertNotIn('error', result)
    
    def test_performance_metrics(self):
        """Test that performance metrics are collected"""
        # Mock a quick analysis
        with patch.object(self.analyzer, '_run_analysis_modules') as mock_modules:
            mock_modules.return_value = {
                'geometry': {'area_sqkm': 0.25},
                'population': {'consensus': 1000},
                'collection_feasibility': {'overall_score': 70}
            }
            
            result = self.analyzer.analyze_drawn_zone(self.test_geometry, self.test_metadata)
            
            # Should have performance metrics
            self.assertIn('performance_metrics', result)
            metrics = result['performance_metrics']
            self.assertIn('total_analysis_time_seconds', metrics)
            self.assertIn('modules_completed', metrics)
            self.assertIn('modules_failed', metrics)


def main():
    """Run the tests"""
    print("🧪 Testing Real-time Zone Analyzer...")
    print("=" * 50)
    
    # Run the tests
    unittest.main(verbosity=2, buffer=True)


if __name__ == '__main__':
    main() 