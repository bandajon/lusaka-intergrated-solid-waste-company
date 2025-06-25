"""
Settlement Context Classification System
Classifies settlements as formal or informal based on building patterns and features
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SettlementClassifier:
    """
    Settlement context classifier for formal vs informal settlement identification
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the settlement classifier"""
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Classification models
        self.ml_classifier = None
        
        # Feature importance and thresholds
        self.feature_importance = {}
        
        # Model state
        self.is_fitted = False
        self.feature_names = []
        self.settlement_types = ['formal', 'informal']
        
        # Lusaka-specific thresholds (from analysis.md)
        self.lusaka_thresholds = {
            'building_density_high': 150,  # buildings per hectare
            'building_density_medium': 80,
            'building_area_small': 80,     # sqm
            'building_area_large': 200,
            'shape_complexity_high': 1.5,  # perimeter-to-area ratio
            'shape_complexity_low': 1.2,
        }
    
    def extract_settlement_features(self, building_data: pd.DataFrame) -> pd.DataFrame:
        """Extract settlement-level features from building data"""
        logger.info("Extracting settlement-level features...")
        
        if building_data.empty:
            raise ValueError("Building data cannot be empty")
        
        settlement_features = {}
        
        # Building count and density
        building_count = len(building_data)
        settlement_features['building_count'] = building_count
        
        # Building size statistics
        if 'area' in building_data.columns:
            areas = building_data['area']
            settlement_features['mean_building_area'] = areas.mean()
            settlement_features['std_building_area'] = areas.std()
            settlement_features['cv_building_area'] = areas.std() / areas.mean() if areas.mean() > 0 else 0
            settlement_features['small_buildings_ratio'] = (areas < self.lusaka_thresholds['building_area_small']).mean()
            settlement_features['large_buildings_ratio'] = (areas > self.lusaka_thresholds['building_area_large']).mean()
        
        # Building height statistics
        if 'height' in building_data.columns:
            heights = building_data['height']
            settlement_features['mean_building_height'] = heights.mean()
            settlement_features['std_building_height'] = heights.std()
            settlement_features['single_story_ratio'] = (heights < 4.0).mean()  # < 4m = single story
        
        # Shape complexity
        if 'perimeter' in building_data.columns and 'area' in building_data.columns:
            pa_ratios = building_data['perimeter'] / np.sqrt(building_data['area'])
            settlement_features['mean_shape_complexity'] = pa_ratios.mean()
            settlement_features['std_shape_complexity'] = pa_ratios.std()
            settlement_features['high_complexity_ratio'] = (pa_ratios > self.lusaka_thresholds['shape_complexity_high']).mean()
        
        return pd.DataFrame([settlement_features])
    
    def apply_rule_based_classification(self, settlement_features: pd.DataFrame) -> Dict[str, Any]:
        """Apply rule-based classification for formal vs informal settlements"""
        logger.info("Applying rule-based classification...")
        
        if settlement_features.empty:
            return {"error": "No settlement features provided"}
        
        features = settlement_features.iloc[0]
        
        # Initialize scores
        formal_score = 0
        informal_score = 0
        evidence = []
        
        # Rule 1: Building size variation
        cv_area = features.get('cv_building_area', 0)
        if cv_area > 0.8:
            informal_score += 2
            evidence.append(f"High size variation: CV={cv_area:.2f}")
        elif cv_area < 0.4:
            formal_score += 2
            evidence.append(f"Low size variation: CV={cv_area:.2f}")
        
        # Rule 2: Shape complexity
        mean_complexity = features.get('mean_shape_complexity', 0)
        if mean_complexity > self.lusaka_thresholds['shape_complexity_high']:
            informal_score += 2
            evidence.append(f"High shape complexity: {mean_complexity:.2f}")
        elif mean_complexity < self.lusaka_thresholds['shape_complexity_low']:
            formal_score += 1
            evidence.append(f"Low shape complexity: {mean_complexity:.2f}")
        
        # Rule 3: Small buildings ratio
        small_ratio = features.get('small_buildings_ratio', 0)
        if small_ratio > 0.6:
            informal_score += 2
            evidence.append(f"High small buildings ratio: {small_ratio:.2f}")
        elif small_ratio < 0.2:
            formal_score += 1
            evidence.append(f"Low small buildings ratio: {small_ratio:.2f}")
        
        # Final classification
        total_score = formal_score + informal_score
        if total_score == 0:
            classification = 'mixed'
            confidence = 0.5
        else:
            if informal_score > formal_score:
                classification = 'informal'
                confidence = informal_score / total_score
            else:
                classification = 'formal'
                confidence = formal_score / total_score
        
        return {
            'classification': classification,
            'confidence': confidence,
            'formal_score': formal_score,
            'informal_score': informal_score,
            'evidence': evidence,
            'method': 'rule_based'
        }
    
    def train_ml_classifier(self, training_data: pd.DataFrame, target_column: str = 'settlement_type') -> Dict[str, float]:
        """Train machine learning classifier for settlement classification"""
        logger.info("Training ML classifier for settlement classification...")
        
        if target_column not in training_data.columns:
            raise ValueError(f"Target column '{target_column}' not found in training data")
        
        # Prepare features and labels
        X = training_data.drop(columns=[target_column])
        y = training_data[target_column]
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=self.random_state, stratify=y_encoded
        )
        
        # Train Random Forest classifier
        self.ml_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=self.random_state
        )
        
        self.ml_classifier.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.ml_classifier.score(X_train, y_train)
        test_score = self.ml_classifier.score(X_test, y_test)
        
        # Cross-validation
        cv_scores = cross_val_score(self.ml_classifier, X_scaled, y_encoded, cv=5)
        
        # Feature importance
        if hasattr(self.ml_classifier, 'feature_importances_'):
            self.feature_importance = dict(zip(self.feature_names, self.ml_classifier.feature_importances_))
        
        self.is_fitted = True
        
        training_metrics = {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean_accuracy': cv_scores.mean(),
            'cv_std_accuracy': cv_scores.std()
        }
        
        logger.info(f"ML classifier training completed:")
        logger.info(f"Train accuracy: {train_score:.4f}")
        logger.info(f"Test accuracy: {test_score:.4f}")
        logger.info(f"CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        
        return training_metrics
    
    def classify_settlement(self, settlement_features: pd.DataFrame) -> Dict[str, Any]:
        """Classify settlement using both rule-based and ML approaches"""
        # Rule-based classification
        rule_result = self.apply_rule_based_classification(settlement_features)
        
        results = {
            'rule_based_result': rule_result
        }
        
        # ML classification if model is fitted
        if self.is_fitted and not settlement_features.empty:
            try:
                # Prepare features
                X = settlement_features[self.feature_names]
                X_scaled = self.scaler.transform(X)
                
                # Predict
                ml_pred = self.ml_classifier.predict(X_scaled)[0]
                ml_proba = self.ml_classifier.predict_proba(X_scaled)[0]
                
                ml_classification = self.label_encoder.inverse_transform([ml_pred])[0]
                ml_confidence = np.max(ml_proba)
                
                results['ml_result'] = {
                    'classification': ml_classification,
                    'confidence': ml_confidence,
                    'probabilities': dict(zip(self.settlement_types, ml_proba)),
                    'method': 'machine_learning'
                }
                    
            except Exception as e:
                results['ml_error'] = str(e)
        
        return results


def create_synthetic_settlement_dataset(n_settlements: int = 200, random_state: int = 42) -> pd.DataFrame:
    """Create synthetic settlement dataset for testing"""
    np.random.seed(random_state)
    
    data = []
    
    for i in range(n_settlements):
        # Randomly assign settlement type
        is_informal = np.random.choice([True, False], p=[0.4, 0.6])
        
        if is_informal:
            # Informal settlement characteristics
            mean_building_area = np.random.normal(60, 20)           # Small buildings
            cv_building_area = np.random.normal(0.9, 0.2)          # High variation
            mean_shape_complexity = np.random.normal(1.8, 0.3)     # Irregular shapes
            small_buildings_ratio = np.random.normal(0.7, 0.15)    # Many small buildings
            settlement_type = 'informal'
            
        else:
            # Formal settlement characteristics
            mean_building_area = np.random.normal(150, 40)           # Larger buildings
            cv_building_area = np.random.normal(0.4, 0.15)          # Lower variation
            mean_shape_complexity = np.random.normal(1.1, 0.2)      # Regular shapes
            small_buildings_ratio = np.random.normal(0.2, 0.1)      # Few small buildings
            settlement_type = 'formal'
        
        # Ensure positive values and realistic ranges
        mean_building_area = max(30, mean_building_area)
        cv_building_area = max(0.1, min(2.0, cv_building_area))
        mean_shape_complexity = max(0.8, min(3.0, mean_shape_complexity))
        small_buildings_ratio = max(0, min(1, small_buildings_ratio))
        
        data.append({
            'mean_building_area': mean_building_area,
            'cv_building_area': cv_building_area,
            'mean_shape_complexity': mean_shape_complexity,
            'small_buildings_ratio': small_buildings_ratio,
            'settlement_type': settlement_type
        })
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    print("Settlement Classification System Demo")
    print("=" * 50)
    
    # Create synthetic dataset
    print("Creating synthetic settlement dataset...")
    df = create_synthetic_settlement_dataset(n_settlements=300)
    print(f"Dataset created with {len(df)} settlements")
    print(f"Settlement type distribution:\n{df['settlement_type'].value_counts()}")
    
    # Initialize classifier
    classifier = SettlementClassifier(random_state=42)
    
    # Train ML classifier
    print("\nTraining ML classifier...")
    training_metrics = classifier.train_ml_classifier(df, target_column='settlement_type')
    
    # Test classification on sample
    print("\nTesting classification on sample settlements...")
    test_samples = df.sample(5, random_state=42)
    
    for i, (idx, sample) in enumerate(test_samples.iterrows()):
        actual = sample['settlement_type']
        sample_features = sample.drop('settlement_type').to_frame().T
        
        result = classifier.classify_settlement(sample_features)
        
        rule_class = result['rule_based_result']['classification']
        rule_conf = result['rule_based_result']['confidence']
        
        if 'ml_result' in result:
            ml_class = result['ml_result']['classification']
            ml_conf = result['ml_result']['confidence']
            print(f"Sample {i+1}: Actual={actual}, Rule={rule_class}({rule_conf:.3f}), ML={ml_class}({ml_conf:.3f})")
        else:
            print(f"Sample {i+1}: Actual={actual}, Rule={rule_class}({rule_conf:.3f})")
    
    print(f"\nML Classifier Accuracy: {training_metrics['cv_mean_accuracy']:.4f}")
    print("Demo completed successfully!") 