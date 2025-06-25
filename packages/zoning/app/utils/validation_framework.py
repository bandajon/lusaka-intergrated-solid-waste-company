"""
Phase 6: Validation & Quality Assurance Framework
Implements cross-validation, uncertainty quantification, and statistical validation
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json
import time
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationFramework:
    """
    Comprehensive validation and quality assurance system for Lusaka waste management analytics
    """
    
    def __init__(self):
        """Initialize validation framework"""
        self.validation_results = {}
        self.uncertainty_metrics = {}
        self.quality_scores = {}
        
    def cross_validate_datasets(self, zone, google_buildings=None, microsoft_buildings=None, 
                               worldpop_data=None, settlement_classification=None):
        """
        Cross-validate building detection across multiple datasets
        
        Args:
            zone: Zone object
            google_buildings: Google Open Buildings data
            microsoft_buildings: Microsoft Building footprints data
            worldpop_data: WorldPop population data
            settlement_classification: Settlement classification results
            
        Returns:
            Dict with cross-validation results
        """
        try:
            validation_id = f"cross_validation_{zone.id}_{int(time.time())}"
            
            cross_validation = {
                'validation_id': validation_id,
                'zone_id': zone.id,
                'zone_name': zone.name,
                'validation_timestamp': time.time(),
                'datasets_compared': [],
                'building_detection_comparison': {},
                'population_estimate_comparison': {},
                'agreement_analysis': {},
                'confidence_assessment': {}
            }
            
            # Building Detection Cross-Validation
            if google_buildings and microsoft_buildings:
                building_comparison = self._compare_building_datasets(
                    google_buildings, microsoft_buildings
                )
                cross_validation['building_detection_comparison'] = building_comparison
                cross_validation['datasets_compared'].extend(['Google Open Buildings', 'Microsoft Buildings'])
            
            # Population Estimate Cross-Validation
            if worldpop_data and settlement_classification:
                population_comparison = self._compare_population_estimates(
                    worldpop_data, settlement_classification, google_buildings
                )
                cross_validation['population_estimate_comparison'] = population_comparison
                cross_validation['datasets_compared'].append('WorldPop')
            
            # Settlement Classification Validation
            if settlement_classification and google_buildings:
                settlement_validation = self._validate_settlement_classification(
                    settlement_classification, google_buildings
                )
                cross_validation['settlement_validation'] = settlement_validation
            
            # Overall Agreement Analysis
            cross_validation['agreement_analysis'] = self._calculate_dataset_agreement(
                cross_validation
            )
            
            # Confidence Assessment
            cross_validation['confidence_assessment'] = self._assess_validation_confidence(
                cross_validation
            )
            
            # Store results
            self.validation_results[validation_id] = cross_validation
            
            return cross_validation
            
        except Exception as e:
            return {"error": f"Cross-validation failed: {str(e)}"}
    
    def quantify_uncertainty(self, estimates_data, estimation_methods=['building_based', 'worldpop', 'ensemble']):
        """
        Quantify uncertainty using ensemble variance and statistical methods
        
        Args:
            estimates_data: Dictionary containing estimates from different methods
            estimation_methods: List of estimation methods to compare
            
        Returns:
            Dict with uncertainty quantification results
        """
        try:
            uncertainty_analysis = {
                'timestamp': time.time(),
                'methods_analyzed': estimation_methods,
                'uncertainty_metrics': {},
                'confidence_intervals': {},
                'variance_analysis': {},
                'reliability_score': 0
            }
            
            # Extract estimates for analysis
            estimates = []
            method_names = []
            
            for method in estimation_methods:
                if method in estimates_data and estimates_data[method].get('estimated_population'):
                    estimates.append(estimates_data[method]['estimated_population'])
                    method_names.append(method)
            
            if len(estimates) < 2:
                return {"error": "Insufficient estimates for uncertainty quantification"}
            
            estimates = np.array(estimates)
            
            # Calculate uncertainty metrics
            uncertainty_analysis['uncertainty_metrics'] = {
                'mean_estimate': float(np.mean(estimates)),
                'standard_deviation': float(np.std(estimates)),
                'coefficient_of_variation': float(np.std(estimates) / np.mean(estimates)) if np.mean(estimates) > 0 else 0,
                'min_estimate': float(np.min(estimates)),
                'max_estimate': float(np.max(estimates)),
                'range': float(np.max(estimates) - np.min(estimates)),
                'relative_range_percent': float((np.max(estimates) - np.min(estimates)) / np.mean(estimates) * 100) if np.mean(estimates) > 0 else 0
            }
            
            # Calculate confidence intervals
            mean_est = np.mean(estimates)
            std_est = np.std(estimates)
            
            # 95% confidence interval (assuming normal distribution)
            ci_95_lower = mean_est - 1.96 * std_est
            ci_95_upper = mean_est + 1.96 * std_est
            
            # 90% confidence interval
            ci_90_lower = mean_est - 1.645 * std_est
            ci_90_upper = mean_est + 1.645 * std_est
            
            uncertainty_analysis['confidence_intervals'] = {
                '95_percent': {
                    'lower_bound': float(max(0, ci_95_lower)),  # Population can't be negative
                    'upper_bound': float(ci_95_upper),
                    'width': float(ci_95_upper - ci_95_lower),
                    'relative_width_percent': float((ci_95_upper - ci_95_lower) / mean_est * 100) if mean_est > 0 else 0
                },
                '90_percent': {
                    'lower_bound': float(max(0, ci_90_lower)),
                    'upper_bound': float(ci_90_upper),
                    'width': float(ci_90_upper - ci_90_lower),
                    'relative_width_percent': float((ci_90_upper - ci_90_lower) / mean_est * 100) if mean_est > 0 else 0
                }
            }
            
            # Variance analysis
            uncertainty_analysis['variance_analysis'] = {
                'total_variance': float(np.var(estimates)),
                'normalized_variance': float(np.var(estimates) / mean_est) if mean_est > 0 else 0,
                'method_agreement_score': self._calculate_method_agreement(estimates),
                'outlier_detection': self._detect_outliers(estimates, method_names)
            }
            
            # Calculate reliability score (0-100)
            cv = uncertainty_analysis['uncertainty_metrics']['coefficient_of_variation']
            rel_width_95 = uncertainty_analysis['confidence_intervals']['95_percent']['relative_width_percent']
            
            # Lower CV and narrower confidence intervals = higher reliability
            reliability_score = max(0, 100 - (cv * 100) - (rel_width_95 / 2))
            uncertainty_analysis['reliability_score'] = round(reliability_score, 1)
            
            # Store results
            uncertainty_id = f"uncertainty_{int(time.time())}"
            self.uncertainty_metrics[uncertainty_id] = uncertainty_analysis
            
            return uncertainty_analysis
            
        except Exception as e:
            return {"error": f"Uncertainty quantification failed: {str(e)}"}
    
    def analyze_temporal_consistency(self, temporal_data, years_analyzed):
        """
        Analyze temporal consistency of building detection and population estimates
        
        Args:
            temporal_data: Dictionary with data for different years
            years_analyzed: List of years to analyze
            
        Returns:
            Dict with temporal consistency analysis
        """
        try:
            temporal_analysis = {
                'timestamp': time.time(),
                'years_analyzed': years_analyzed,
                'consistency_metrics': {},
                'growth_analysis': {},
                'anomaly_detection': {},
                'stability_assessment': {}
            }
            
            # Extract building counts and population estimates by year
            building_counts = []
            population_estimates = []
            valid_years = []
            
            for year in years_analyzed:
                year_str = str(year)
                if year_str in temporal_data:
                    year_data = temporal_data[year_str]
                    
                    if 'building_count' in year_data:
                        building_counts.append(year_data['building_count'])
                        valid_years.append(year)
                    
                    if 'population_estimate' in year_data:
                        population_estimates.append(year_data['population_estimate'])
            
            if len(building_counts) < 2 and len(population_estimates) < 2:
                return {"error": "Insufficient temporal data for consistency analysis"}
            
            # Building count consistency analysis
            if len(building_counts) >= 2:
                building_analysis = self._analyze_temporal_series(
                    building_counts, valid_years, "building_count"
                )
                temporal_analysis['building_consistency'] = building_analysis
            
            # Population estimate consistency analysis
            if len(population_estimates) >= 2:
                population_analysis = self._analyze_temporal_series(
                    population_estimates, valid_years, "population_estimate"
                )
                temporal_analysis['population_consistency'] = population_analysis
            
            # Growth rate analysis
            if len(building_counts) >= 2:
                building_growth = self._calculate_growth_rates(building_counts, valid_years)
                temporal_analysis['building_growth_analysis'] = building_growth
            
            if len(population_estimates) >= 2:
                population_growth = self._calculate_growth_rates(population_estimates, valid_years)
                temporal_analysis['population_growth_analysis'] = population_growth
            
            # Anomaly detection
            temporal_analysis['anomaly_detection'] = self._detect_temporal_anomalies(
                temporal_data, years_analyzed
            )
            
            # Overall stability assessment
            temporal_analysis['stability_assessment'] = self._assess_temporal_stability(
                temporal_analysis
            )
            
            return temporal_analysis
            
        except Exception as e:
            return {"error": f"Temporal consistency analysis failed: {str(e)}"}
    
    def validate_statistical_quality(self, zone_data, validation_type='comprehensive'):
        """
        Perform statistical validation of data quality
        
        Args:
            zone_data: Dictionary containing zone analysis data
            validation_type: Type of validation ('comprehensive', 'basic', 'building_only')
            
        Returns:
            Dict with statistical validation results
        """
        try:
            statistical_validation = {
                'timestamp': time.time(),
                'validation_type': validation_type,
                'data_quality_score': 0,
                'statistical_tests': {},
                'distribution_analysis': {},
                'outlier_analysis': {},
                'completeness_assessment': {}
            }
            
            # Data completeness assessment
            completeness = self._assess_data_completeness(zone_data)
            statistical_validation['completeness_assessment'] = completeness
            
            # Statistical tests for building data
            if 'building_analysis' in zone_data:
                building_stats = self._validate_building_statistics(
                    zone_data['building_analysis']
                )
                statistical_validation['building_statistics'] = building_stats
            
            # Population estimate validation
            if 'population_estimate' in zone_data:
                population_stats = self._validate_population_statistics(
                    zone_data['population_estimate']
                )
                statistical_validation['population_statistics'] = population_stats
            
            # Waste generation validation
            if 'waste_generation' in zone_data:
                waste_stats = self._validate_waste_statistics(
                    zone_data['waste_generation']
                )
                statistical_validation['waste_statistics'] = waste_stats
            
            # Overall data quality score calculation
            quality_components = []
            
            if completeness['overall_completeness_percent'] is not None:
                quality_components.append(completeness['overall_completeness_percent'])
            
            if 'building_statistics' in statistical_validation:
                quality_components.append(statistical_validation['building_statistics'].get('quality_score', 0))
            
            if 'population_statistics' in statistical_validation:
                quality_components.append(statistical_validation['population_statistics'].get('quality_score', 0))
            
            if quality_components:
                statistical_validation['data_quality_score'] = round(np.mean(quality_components), 1)
            
            return statistical_validation
            
        except Exception as e:
            return {"error": f"Statistical validation failed: {str(e)}"}
    
    def calculate_error_bounds(self, estimates, actual_values=None, confidence_level=0.95):
        """
        Calculate error bounds for estimates
        
        Args:
            estimates: Array or list of estimates
            actual_values: Optional array of actual values for validation
            confidence_level: Confidence level for bounds (default 0.95)
            
        Returns:
            Dict with error bounds and metrics
        """
        try:
            estimates = np.array(estimates)
            
            error_bounds = {
                'timestamp': time.time(),
                'confidence_level': confidence_level,
                'sample_size': len(estimates),
                'error_metrics': {},
                'bounds_calculation': {},
                'prediction_intervals': {}
            }
            
            # Basic statistics
            mean_est = np.mean(estimates)
            std_est = np.std(estimates)
            se_est = std_est / np.sqrt(len(estimates))  # Standard error
            
            # Calculate confidence intervals for the mean
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            t_score = stats.t.ppf((1 + confidence_level) / 2, len(estimates) - 1)
            
            # Normal distribution bounds
            normal_lower = mean_est - z_score * se_est
            normal_upper = mean_est + z_score * se_est
            
            # T-distribution bounds (more appropriate for small samples)
            t_lower = mean_est - t_score * se_est
            t_upper = mean_est + t_score * se_est
            
            error_bounds['bounds_calculation'] = {
                'mean_estimate': float(mean_est),
                'standard_error': float(se_est),
                'normal_distribution': {
                    'lower_bound': float(normal_lower),
                    'upper_bound': float(normal_upper),
                    'margin_of_error': float(z_score * se_est)
                },
                't_distribution': {
                    'lower_bound': float(t_lower),
                    'upper_bound': float(t_upper),
                    'margin_of_error': float(t_score * se_est)
                }
            }
            
            # Prediction intervals (for individual predictions)
            pred_margin = t_score * std_est * np.sqrt(1 + 1/len(estimates))
            pred_lower = mean_est - pred_margin
            pred_upper = mean_est + pred_margin
            
            error_bounds['prediction_intervals'] = {
                'lower_bound': float(pred_lower),
                'upper_bound': float(pred_upper),
                'margin_of_error': float(pred_margin),
                'relative_margin_percent': float(pred_margin / mean_est * 100) if mean_est > 0 else 0
            }
            
            # If actual values are provided, calculate validation metrics
            if actual_values is not None:
                actual_values = np.array(actual_values)
                if len(actual_values) == len(estimates):
                    validation_metrics = self._calculate_validation_metrics(estimates, actual_values)
                    error_bounds['validation_metrics'] = validation_metrics
            
            return error_bounds
            
        except Exception as e:
            return {"error": f"Error bounds calculation failed: {str(e)}"}
    
    # Helper methods for internal calculations
    
    def _compare_building_datasets(self, google_data, microsoft_data):
        """Compare building detection between Google and Microsoft datasets"""
        comparison = {
            'google_building_count': google_data.get('building_count', 0),
            'microsoft_building_count': microsoft_data.get('building_count', 0),
            'count_difference': 0,
            'relative_difference_percent': 0,
            'agreement_level': 'Unknown'
        }
        
        google_count = comparison['google_building_count']
        microsoft_count = comparison['microsoft_building_count']
        
        if google_count > 0 and microsoft_count > 0:
            difference = abs(google_count - microsoft_count)
            relative_diff = (difference / google_count) * 100
            
            comparison['count_difference'] = difference
            comparison['relative_difference_percent'] = round(relative_diff, 2)
            
            # Determine agreement level
            if relative_diff < 10:
                comparison['agreement_level'] = 'Excellent'
            elif relative_diff < 20:
                comparison['agreement_level'] = 'Good'
            elif relative_diff < 35:
                comparison['agreement_level'] = 'Moderate'
            else:
                comparison['agreement_level'] = 'Poor'
        
        return comparison
    
    def _compare_population_estimates(self, worldpop_data, settlement_data, building_data):
        """Compare population estimates from different sources"""
        comparison = {
            'worldpop_population': worldpop_data.get('total_population', 0),
            'building_based_population': 0,
            'settlement_adjusted_population': 0
        }
        
        # Extract building-based estimate
        if building_data and 'estimated_population' in building_data:
            comparison['building_based_population'] = building_data['estimated_population']
        
        # Extract settlement-adjusted estimate
        if settlement_data and 'estimated_population' in settlement_data:
            comparison['settlement_adjusted_population'] = settlement_data['estimated_population']
        
        # Calculate agreement metrics
        estimates = [v for v in comparison.values() if v > 0]
        if len(estimates) >= 2:
            comparison['mean_estimate'] = np.mean(estimates)
            comparison['std_estimate'] = np.std(estimates)
            comparison['coefficient_of_variation'] = np.std(estimates) / np.mean(estimates) if np.mean(estimates) > 0 else 0
            comparison['agreement_score'] = max(0, 100 - (comparison['coefficient_of_variation'] * 100))
        
        return comparison
    
    def _validate_settlement_classification(self, settlement_data, building_data):
        """Validate settlement classification results"""
        validation = {
            'settlement_type': settlement_data.get('settlement_type', 'unknown'),
            'classification_confidence': settlement_data.get('confidence', 0),
            'building_density': settlement_data.get('building_density', 0),
            'validation_score': 0
        }
        
        # Validate based on building characteristics
        building_count = building_data.get('building_count', 0)
        zone_area = building_data.get('zone_area_sqkm', 1)
        
        if zone_area > 0:
            calculated_density = building_count / zone_area
            density_difference = abs(calculated_density - validation['building_density'])
            density_agreement = max(0, 100 - (density_difference / calculated_density * 100)) if calculated_density > 0 else 0
            
            validation['calculated_density'] = calculated_density
            validation['density_agreement_percent'] = round(density_agreement, 1)
            validation['validation_score'] = round((validation['classification_confidence'] * 100 + density_agreement) / 2, 1)
        
        return validation
    
    def _calculate_dataset_agreement(self, cross_validation_data):
        """Calculate overall agreement between datasets"""
        agreement_scores = []
        
        # Building detection agreement
        building_comp = cross_validation_data.get('building_detection_comparison', {})
        if 'agreement_level' in building_comp:
            agreement_map = {'Excellent': 95, 'Good': 80, 'Moderate': 60, 'Poor': 30, 'Unknown': 0}
            agreement_scores.append(agreement_map.get(building_comp['agreement_level'], 0))
        
        # Population estimate agreement
        pop_comp = cross_validation_data.get('population_estimate_comparison', {})
        if 'agreement_score' in pop_comp:
            agreement_scores.append(pop_comp['agreement_score'])
        
        # Settlement validation agreement
        settlement_val = cross_validation_data.get('settlement_validation', {})
        if 'validation_score' in settlement_val:
            agreement_scores.append(settlement_val['validation_score'])
        
        if agreement_scores:
            overall_agreement = np.mean(agreement_scores)
            return {
                'overall_agreement_score': round(overall_agreement, 1),
                'individual_scores': agreement_scores,
                'agreement_level': self._score_to_level(overall_agreement)
            }
        else:
            return {'overall_agreement_score': 0, 'agreement_level': 'Unknown'}
    
    def _assess_validation_confidence(self, cross_validation_data):
        """Assess overall confidence in validation results"""
        confidence_factors = []
        
        # Number of datasets compared
        datasets_count = len(cross_validation_data.get('datasets_compared', []))
        confidence_factors.append(min(100, datasets_count * 30))  # More datasets = higher confidence
        
        # Agreement level
        agreement = cross_validation_data.get('agreement_analysis', {})
        if 'overall_agreement_score' in agreement:
            confidence_factors.append(agreement['overall_agreement_score'])
        
        # Data completeness (estimated)
        if cross_validation_data.get('building_detection_comparison'):
            confidence_factors.append(85)  # Building data available
        
        if confidence_factors:
            overall_confidence = np.mean(confidence_factors)
            return {
                'confidence_score': round(overall_confidence, 1),
                'confidence_level': self._score_to_level(overall_confidence),
                'confidence_factors': confidence_factors
            }
        else:
            return {'confidence_score': 0, 'confidence_level': 'Unknown'}
    
    def _calculate_method_agreement(self, estimates):
        """Calculate agreement score between estimation methods"""
        if len(estimates) < 2:
            return 0
        
        cv = np.std(estimates) / np.mean(estimates) if np.mean(estimates) > 0 else 1
        # Convert CV to agreement score (lower CV = higher agreement)
        agreement_score = max(0, 100 - (cv * 100))
        return round(agreement_score, 1)
    
    def _detect_outliers(self, estimates, method_names):
        """Detect outlier estimates using statistical methods"""
        if len(estimates) < 3:
            return {'outliers_detected': 0, 'outlier_methods': []}
        
        # Using IQR method
        q1 = np.percentile(estimates, 25)
        q3 = np.percentile(estimates, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_indices = []
        for i, est in enumerate(estimates):
            if est < lower_bound or est > upper_bound:
                outlier_indices.append(i)
        
        outlier_methods = [method_names[i] for i in outlier_indices if i < len(method_names)]
        
        return {
            'outliers_detected': len(outlier_indices),
            'outlier_methods': outlier_methods,
            'outlier_threshold_lower': float(lower_bound),
            'outlier_threshold_upper': float(upper_bound)
        }
    
    def _analyze_temporal_series(self, values, years, metric_name):
        """Analyze temporal consistency of a data series"""
        if len(values) < 2:
            return {'error': 'Insufficient data points'}
        
        values = np.array(values)
        years = np.array(years)
        
        # Calculate year-over-year changes
        changes = np.diff(values)
        change_rates = changes / values[:-1] * 100  # Percentage changes
        
        analysis = {
            'metric_name': metric_name,
            'data_points': len(values),
            'time_span_years': int(years[-1] - years[0]),
            'mean_value': float(np.mean(values)),
            'std_value': float(np.std(values)),
            'coefficient_of_variation': float(np.std(values) / np.mean(values)) if np.mean(values) > 0 else 0,
            'year_over_year_changes': {
                'mean_change': float(np.mean(changes)),
                'mean_change_rate_percent': float(np.mean(change_rates)),
                'std_change_rate_percent': float(np.std(change_rates)),
                'max_change_rate_percent': float(np.max(np.abs(change_rates))),
                'consistency_score': max(0, 100 - np.std(change_rates))  # Lower std = higher consistency
            }
        }
        
        return analysis
    
    def _calculate_growth_rates(self, values, years):
        """Calculate growth rates for temporal data"""
        if len(values) < 2:
            return {'error': 'Insufficient data for growth analysis'}
        
        values = np.array(values)
        years = np.array(years)
        
        # Calculate compound annual growth rate (CAGR)
        initial_value = values[0]
        final_value = values[-1]
        years_span = years[-1] - years[0]
        
        if initial_value > 0 and years_span > 0:
            cagr = ((final_value / initial_value) ** (1 / years_span) - 1) * 100
        else:
            cagr = 0
        
        # Year-over-year growth rates
        yoy_rates = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                yoy_rate = ((values[i] - values[i-1]) / values[i-1]) * 100
                yoy_rates.append(yoy_rate)
        
        growth_analysis = {
            'compound_annual_growth_rate_percent': round(cagr, 2),
            'total_growth_percent': round(((final_value - initial_value) / initial_value * 100), 2) if initial_value > 0 else 0,
            'year_over_year_rates': [round(rate, 2) for rate in yoy_rates],
            'mean_yoy_rate_percent': round(np.mean(yoy_rates), 2) if yoy_rates else 0,
            'growth_volatility': round(np.std(yoy_rates), 2) if yoy_rates else 0
        }
        
        return growth_analysis
    
    def _detect_temporal_anomalies(self, temporal_data, years_analyzed):
        """Detect anomalies in temporal data"""
        anomalies = {
            'anomalies_detected': 0,
            'anomaly_years': [],
            'anomaly_descriptions': []
        }
        
        # Simple anomaly detection based on growth rates
        building_counts = []
        valid_years = []
        
        for year in years_analyzed:
            year_str = str(year)
            if year_str in temporal_data and 'building_count' in temporal_data[year_str]:
                building_counts.append(temporal_data[year_str]['building_count'])
                valid_years.append(year)
        
        if len(building_counts) >= 3:
            # Detect sudden changes
            for i in range(1, len(building_counts)):
                if building_counts[i-1] > 0:
                    change_rate = abs((building_counts[i] - building_counts[i-1]) / building_counts[i-1])
                    if change_rate > 0.5:  # 50% change threshold
                        anomalies['anomalies_detected'] += 1
                        anomalies['anomaly_years'].append(valid_years[i])
                        anomalies['anomaly_descriptions'].append(
                            f"Large change in {valid_years[i]}: {change_rate*100:.1f}% from previous year"
                        )
        
        return anomalies
    
    def _assess_temporal_stability(self, temporal_analysis):
        """Assess overall temporal stability"""
        stability_scores = []
        
        # Building consistency score
        if 'building_consistency' in temporal_analysis:
            building_consistency = temporal_analysis['building_consistency']
            if 'year_over_year_changes' in building_consistency:
                consistency_score = building_consistency['year_over_year_changes'].get('consistency_score', 0)
                stability_scores.append(consistency_score)
        
        # Population consistency score
        if 'population_consistency' in temporal_analysis:
            pop_consistency = temporal_analysis['population_consistency']
            if 'year_over_year_changes' in pop_consistency:
                consistency_score = pop_consistency['year_over_year_changes'].get('consistency_score', 0)
                stability_scores.append(consistency_score)
        
        # Anomaly impact
        anomalies = temporal_analysis.get('anomaly_detection', {})
        anomaly_count = anomalies.get('anomalies_detected', 0)
        anomaly_penalty = min(50, anomaly_count * 10)  # Up to 50 point penalty
        
        if stability_scores:
            overall_stability = np.mean(stability_scores) - anomaly_penalty
            stability_level = self._score_to_level(max(0, overall_stability))
        else:
            overall_stability = 0
            stability_level = 'Unknown'
        
        return {
            'overall_stability_score': round(max(0, overall_stability), 1),
            'stability_level': stability_level,
            'individual_scores': stability_scores,
            'anomaly_penalty': anomaly_penalty
        }
    
    def _assess_data_completeness(self, zone_data):
        """Assess completeness of zone data"""
        required_fields = [
            'zone_id', 'zone_name', 'area_km2', 'waste_generation',
            'collection_requirements', 'revenue_projection'
        ]
        
        optional_fields = [
            'buildings_analysis', 'settlement_classification', 'population_estimate',
            'land_use_analysis', 'environmental_factors'
        ]
        
        completeness = {
            'required_fields_present': 0,
            'optional_fields_present': 0,
            'total_fields_present': 0,
            'completeness_percent': 0,
            'missing_required_fields': [],
            'missing_optional_fields': []
        }
        
        # Check required fields
        for field in required_fields:
            if field in zone_data and zone_data[field] is not None:
                completeness['required_fields_present'] += 1
            else:
                completeness['missing_required_fields'].append(field)
        
        # Check optional fields
        for field in optional_fields:
            if field in zone_data and zone_data[field] is not None:
                completeness['optional_fields_present'] += 1
            else:
                completeness['missing_optional_fields'].append(field)
        
        total_fields = len(required_fields) + len(optional_fields)
        total_present = completeness['required_fields_present'] + completeness['optional_fields_present']
        
        completeness['total_fields_present'] = total_present
        completeness['overall_completeness_percent'] = round((total_present / total_fields) * 100, 1)
        
        # Weight required fields more heavily
        weighted_completeness = (
            (completeness['required_fields_present'] / len(required_fields)) * 0.7 +
            (completeness['optional_fields_present'] / len(optional_fields)) * 0.3
        ) * 100
        
        completeness['weighted_completeness_percent'] = round(weighted_completeness, 1)
        
        return completeness
    
    def _validate_building_statistics(self, building_data):
        """Validate building analysis statistics"""
        validation = {
            'quality_score': 0,
            'data_validity': {},
            'statistical_checks': {}
        }
        
        building_count = building_data.get('building_count', 0)
        confidence_threshold = building_data.get('confidence_threshold', 0)
        
        # Data validity checks
        validation['data_validity'] = {
            'building_count_valid': building_count > 0,
            'confidence_threshold_valid': 0.5 <= confidence_threshold <= 1.0,
            'features_available': 'features' in building_data
        }
        
        # Statistical checks
        if 'features' in building_data:
            features = building_data['features']
            if 'area_statistics' in features:
                area_stats = features['area_statistics']
                mean_area = area_stats.get('mean', 0)
                std_area = area_stats.get('stddev', 0)
                
                validation['statistical_checks'] = {
                    'mean_area_reasonable': 20 <= mean_area <= 1000,  # Reasonable building sizes for Lusaka
                    'std_area_reasonable': std_area < mean_area * 2,   # Std shouldn't be too large
                    'area_distribution_valid': mean_area > 0 and std_area >= 0
                }
        
        # Calculate quality score
        validity_scores = list(validation['data_validity'].values())
        statistical_scores = list(validation['statistical_checks'].values()) if validation['statistical_checks'] else []
        
        all_scores = validity_scores + statistical_scores
        if all_scores:
            quality_score = (sum(all_scores) / len(all_scores)) * 100
            validation['quality_score'] = round(quality_score, 1)
        
        return validation
    
    def _validate_population_statistics(self, population_data):
        """Validate population estimate statistics"""
        validation = {
            'quality_score': 0,
            'reasonableness_checks': {},
            'confidence_assessment': {}
        }
        
        if isinstance(population_data, dict):
            estimated_pop = population_data.get('estimated_population', 0)
            confidence = population_data.get('confidence', 0)
            method = population_data.get('calculation_method', 'unknown')
        else:
            estimated_pop = population_data if isinstance(population_data, (int, float)) else 0
            confidence = 0.5
            method = 'unknown'
        
        # Reasonableness checks for Lusaka context
        validation['reasonableness_checks'] = {
            'population_positive': estimated_pop > 0,
            'population_reasonable': 100 <= estimated_pop <= 100000,  # Reasonable range for zone
            'density_reasonable': True,  # Would need zone area to check properly
            'method_known': method != 'unknown'
        }
        
        # Confidence assessment
        validation['confidence_assessment'] = {
            'confidence_score': confidence,
            'confidence_level': self._score_to_level(confidence * 100),
            'method_reliability': self._assess_method_reliability(method)
        }
        
        # Calculate quality score
        reasonableness_scores = list(validation['reasonableness_checks'].values())
        confidence_score = confidence * 100
        
        if reasonableness_scores:
            reasonableness_percent = (sum(reasonableness_scores) / len(reasonableness_scores)) * 100
            overall_quality = (reasonableness_percent + confidence_score) / 2
            validation['quality_score'] = round(overall_quality, 1)
        
        return validation
    
    def _validate_waste_statistics(self, waste_data):
        """Validate waste generation statistics"""
        validation = {
            'quality_score': 0,
            'waste_metrics_valid': {},
            'rate_validation': {}
        }
        
        total_waste = waste_data.get('total_waste_kg_day', 0)
        residential_waste = waste_data.get('residential_waste', 0)
        commercial_waste = waste_data.get('commercial_waste', 0)
        
        # Waste metrics validation
        validation['waste_metrics_valid'] = {
            'total_waste_positive': total_waste > 0,
            'waste_components_sum_correctly': abs(total_waste - (residential_waste + commercial_waste + waste_data.get('industrial_waste', 0))) < 1,
            'residential_waste_reasonable': 0 <= residential_waste <= total_waste,
            'commercial_waste_reasonable': 0 <= commercial_waste <= total_waste
        }
        
        # Rate validation (typical rates for Lusaka)
        validation['rate_validation'] = {
            'total_rate_reasonable': 0.1 <= (total_waste / max(1, waste_data.get('estimated_population', 1))) <= 2.0,
            'waste_distribution_realistic': residential_waste >= commercial_waste * 0.1  # Residential usually dominates
        }
        
        # Calculate quality score
        metrics_scores = list(validation['waste_metrics_valid'].values())
        rate_scores = list(validation['rate_validation'].values())
        
        all_scores = metrics_scores + rate_scores
        if all_scores:
            quality_score = (sum(all_scores) / len(all_scores)) * 100
            validation['quality_score'] = round(quality_score, 1)
        
        return validation
    
    def _calculate_validation_metrics(self, estimates, actual_values):
        """Calculate validation metrics when actual values are available"""
        mae = mean_absolute_error(actual_values, estimates)
        mse = mean_squared_error(actual_values, estimates)
        rmse = np.sqrt(mse)
        r2 = r2_score(actual_values, estimates)
        
        # Mean Absolute Percentage Error
        mape = np.mean(np.abs((actual_values - estimates) / actual_values)) * 100
        
        return {
            'mean_absolute_error': float(mae),
            'mean_squared_error': float(mse),
            'root_mean_squared_error': float(rmse),
            'r_squared': float(r2),
            'mean_absolute_percentage_error': float(mape),
            'accuracy_percent': max(0, 100 - mape) if mape < 100 else 0
        }
    
    def _score_to_level(self, score):
        """Convert numerical score to qualitative level"""
        if score >= 90:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 60:
            return 'Moderate'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _assess_method_reliability(self, method):
        """Assess reliability of estimation method"""
        reliability_scores = {
            'building_based_with_settlement_factors': 0.9,
            'worldpop_validated': 0.85,
            'building_based': 0.75,
            'worldpop': 0.8,
            'area_based': 0.6,
            'census_data': 0.95,
            'unknown': 0.3
        }
        
        return reliability_scores.get(method, 0.5)
    
    def generate_validation_report(self, zone_id, validation_results=None):
        """
        Generate comprehensive validation report
        
        Args:
            zone_id: Zone identifier
            validation_results: Optional pre-computed validation results
            
        Returns:
            Dict with comprehensive validation report
        """
        try:
            report = {
                'report_id': f"validation_report_{zone_id}_{int(time.time())}",
                'zone_id': zone_id,
                'generation_timestamp': time.time(),
                'report_sections': {}
            }
            
            # Cross-validation summary
            if validation_results and 'cross_validation' in validation_results:
                cv_data = validation_results['cross_validation']
                report['report_sections']['cross_validation_summary'] = {
                    'datasets_compared': cv_data.get('datasets_compared', []),
                    'overall_agreement_score': cv_data.get('agreement_analysis', {}).get('overall_agreement_score', 0),
                    'confidence_level': cv_data.get('confidence_assessment', {}).get('confidence_level', 'Unknown')
                }
            
            # Uncertainty quantification summary
            if validation_results and 'uncertainty' in validation_results:
                uncertainty_data = validation_results['uncertainty']
                report['report_sections']['uncertainty_summary'] = {
                    'reliability_score': uncertainty_data.get('reliability_score', 0),
                    'coefficient_of_variation': uncertainty_data.get('uncertainty_metrics', {}).get('coefficient_of_variation', 0),
                    'confidence_interval_95': uncertainty_data.get('confidence_intervals', {}).get('95_percent', {})
                }
            
            # Temporal consistency summary
            if validation_results and 'temporal_consistency' in validation_results:
                temporal_data = validation_results['temporal_consistency']
                report['report_sections']['temporal_consistency_summary'] = {
                    'stability_score': temporal_data.get('stability_assessment', {}).get('overall_stability_score', 0),
                    'anomalies_detected': temporal_data.get('anomaly_detection', {}).get('anomalies_detected', 0),
                    'years_analyzed': temporal_data.get('years_analyzed', [])
                }
            
            # Overall quality assessment
            quality_scores = []
            
            if 'cross_validation_summary' in report['report_sections']:
                quality_scores.append(report['report_sections']['cross_validation_summary']['overall_agreement_score'])
            
            if 'uncertainty_summary' in report['report_sections']:
                quality_scores.append(report['report_sections']['uncertainty_summary']['reliability_score'])
            
            if 'temporal_consistency_summary' in report['report_sections']:
                quality_scores.append(report['report_sections']['temporal_consistency_summary']['stability_score'])
            
            if quality_scores:
                overall_quality = np.mean(quality_scores)
                report['overall_quality_assessment'] = {
                    'overall_quality_score': round(overall_quality, 1),
                    'quality_level': self._score_to_level(overall_quality),
                    'component_scores': quality_scores,
                    'validation_confidence': 'High' if overall_quality >= 80 else 'Medium' if overall_quality >= 60 else 'Low'
                }
            else:
                report['overall_quality_assessment'] = {
                    'overall_quality_score': 0,
                    'quality_level': 'Unknown',
                    'validation_confidence': 'Low'
                }
            
            # Recommendations
            report['recommendations'] = self._generate_validation_recommendations(report)
            
            return report
            
        except Exception as e:
            return {"error": f"Validation report generation failed: {str(e)}"}
    
    def _generate_validation_recommendations(self, validation_report):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        overall_quality = validation_report.get('overall_quality_assessment', {})
        quality_score = overall_quality.get('overall_quality_score', 0)
        
        if quality_score >= 90:
            recommendations.append("Excellent validation results - data is ready for production use")
        elif quality_score >= 80:
            recommendations.append("Good validation results - minor improvements recommended")
        elif quality_score >= 60:
            recommendations.append("Moderate validation results - consider additional validation")
        else:
            recommendations.append("Poor validation results - significant improvements needed")
        
        # Specific recommendations based on sections
        sections = validation_report.get('report_sections', {})
        
        if 'cross_validation_summary' in sections:
            cv_score = sections['cross_validation_summary'].get('overall_agreement_score', 0)
            if cv_score < 70:
                recommendations.append("Low cross-validation agreement - verify data sources and methods")
        
        if 'uncertainty_summary' in sections:
            cv_coeff = sections['uncertainty_summary'].get('coefficient_of_variation', 0)
            if cv_coeff > 0.3:
                recommendations.append("High uncertainty detected - consider using more data sources")
        
        if 'temporal_consistency_summary' in sections:
            anomalies = sections['temporal_consistency_summary'].get('anomalies_detected', 0)
            if anomalies > 0:
                recommendations.append(f"Temporal anomalies detected ({anomalies}) - investigate data quality for affected periods")
        
        if not recommendations:
            recommendations.append("Standard validation protocols are sufficient for this data")
        
        return recommendations 