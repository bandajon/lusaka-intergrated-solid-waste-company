"""
Ensemble Machine Learning Classification for Building Type Classification
Implements Random Forest + SVM ensemble for building classification in Lusaka
Based on Task 10 requirements for 90%+ accuracy building detection
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import (
    cross_val_score, GridSearchCV, RandomizedSearchCV, 
    train_test_split, StratifiedKFold
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, 
    roc_auc_score
)
import joblib
import time
import warnings
from typing import Dict, List, Tuple, Optional, Any
import logging

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsembleBuildingClassifier:
    """
    Ensemble machine learning classifier for building type classification
    Combines Random Forest and SVM classifiers for optimal accuracy
    """
    
    def __init__(self, random_state: int = 42):
        """Initialize the ensemble classifier"""
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Initialize individual classifiers
        self.rf_classifier = None
        self.svm_classifier = None
        self.ensemble_classifier = None
        self.best_params = {}
        
        # Performance metrics
        self.training_scores = {}
        self.validation_scores = {}
        self.feature_importance = {}
        
        # Model state
        self.is_fitted = False
        self.feature_names = []
        self.class_names = []
    
    def prepare_features(self, building_features: pd.DataFrame, target_column: str = 'building_type') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare and preprocess building features for classification
        
        Args:
            building_features: DataFrame with building features
            target_column: Name of the target variable column
            
        Returns:
            Tuple of (features, labels)
        """
        logger.info("Preparing and preprocessing building features...")
        
        # Separate features and target
        if target_column in building_features.columns:
            X = building_features.drop(columns=[target_column])
            y = building_features[target_column]
        else:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame")
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Handle missing values
        X_clean = self._handle_missing_values(X)
        
        # Engineer additional features
        X_engineered = self._engineer_features(X_clean)
        
        # Encode categorical variables
        X_encoded = self._encode_categorical_features(X_engineered)
        
        # Encode target labels
        y_encoded = self.label_encoder.fit_transform(y)
        self.class_names = list(self.label_encoder.classes_)
        
        logger.info(f"Features prepared: {X_encoded.shape[1]} features, {len(np.unique(y_encoded))} classes")
        logger.info(f"Class distribution: {dict(zip(self.class_names, np.bincount(y_encoded)))}")
        
        return X_encoded, y_encoded
    
    def _handle_missing_values(self, X: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset"""
        X_clean = X.copy()
        
        # Fill numeric missing values with median
        numeric_cols = X_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if X_clean[col].isnull().any():
                X_clean[col].fillna(X_clean[col].median(), inplace=True)
        
        # Fill categorical missing values with mode
        categorical_cols = X_clean.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if X_clean[col].isnull().any():
                X_clean[col].fillna(X_clean[col].mode()[0], inplace=True)
        
        return X_clean
    
    def _engineer_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Engineer additional features for better classification"""
        X_eng = X.copy()
        
        # Area-based features
        if 'area' in X_eng.columns:
            X_eng['area_log'] = np.log1p(X_eng['area'])
            X_eng['area_sqrt'] = np.sqrt(X_eng['area'])
        
        # Height-based features
        if 'height' in X_eng.columns:
            X_eng['height_log'] = np.log1p(X_eng['height'])
            # Estimated floors (2.5m per floor)
            X_eng['estimated_floors'] = np.ceil(X_eng['height'] / 2.5).clip(lower=1)
        
        # Shape complexity features
        if 'perimeter' in X_eng.columns and 'area' in X_eng.columns:
            # Perimeter to area ratio (shape complexity)
            X_eng['perimeter_area_ratio'] = X_eng['perimeter'] / np.sqrt(X_eng['area'])
            # Compactness index
            X_eng['compactness'] = (4 * np.pi * X_eng['area']) / (X_eng['perimeter'] ** 2)
        
        # Density features
        if 'building_density' in X_eng.columns:
            X_eng['density_log'] = np.log1p(X_eng['building_density'])
            # Density categories
            X_eng['density_category'] = pd.cut(
                X_eng['building_density'], 
                bins=[0, 10, 25, 50, np.inf], 
                labels=['low', 'medium', 'high', 'very_high']
            )
        
        # Size categories
        if 'area' in X_eng.columns:
            X_eng['size_category'] = pd.cut(
                X_eng['area'],
                bins=[0, 50, 150, 500, np.inf],
                labels=['small', 'medium', 'large', 'very_large']
            )
        
        return X_eng
    
    def _encode_categorical_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features using appropriate methods"""
        X_encoded = X.copy()
        
        # Get categorical columns
        categorical_cols = X_encoded.select_dtypes(include=['object', 'category']).columns
        
        for col in categorical_cols:
            # Use one-hot encoding for low cardinality categories
            unique_vals = X_encoded[col].nunique()
            if unique_vals <= 10:
                dummies = pd.get_dummies(X_encoded[col], prefix=col)
                X_encoded = pd.concat([X_encoded.drop(columns=[col]), dummies], axis=1)
            else:
                # Use label encoding for high cardinality
                le = LabelEncoder()
                X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
        
        return X_encoded
    
    def train_ensemble(self, X: np.ndarray, y: np.ndarray, 
                      tune_hyperparameters: bool = True) -> Dict[str, float]:
        """
        Train the ensemble classifier
        
        Args:
            X: Feature matrix
            y: Target labels
            tune_hyperparameters: Whether to perform hyperparameter tuning
            
        Returns:
            Dictionary with training scores
        """
        logger.info("Training ensemble classifier...")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create classifiers with default parameters
        self.rf_classifier = RandomForestClassifier(
            n_estimators=200,  # More than required 150
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            bootstrap=True,
            oob_score=True,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        self.svm_classifier = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            random_state=self.random_state
        )
        
        # Train individual classifiers
        logger.info("Training Random Forest classifier...")
        start_time = time.time()
        self.rf_classifier.fit(X, y)
        rf_time = time.time() - start_time
        
        logger.info("Training SVM classifier...")
        start_time = time.time()
        self.svm_classifier.fit(X_scaled, y)
        svm_time = time.time() - start_time
        
        # Create ensemble using soft voting
        self.ensemble_classifier = VotingClassifier(
            estimators=[
                ('rf', self.rf_classifier),
                ('svm', self.svm_classifier)
            ],
            voting='soft'
        )
        
        # Train ensemble
        logger.info("Training ensemble classifier...")
        start_time = time.time()
        self.ensemble_classifier.fit(X, y)
        ensemble_time = time.time() - start_time
        
        # Calculate training scores
        self.training_scores = {
            'rf_accuracy': self.rf_classifier.score(X, y),
            'svm_accuracy': self.svm_classifier.score(X_scaled, y),
            'ensemble_accuracy': self.ensemble_classifier.score(X, y),
            'rf_oob_score': getattr(self.rf_classifier, 'oob_score_', None),
            'training_time': {
                'rf': rf_time,
                'svm': svm_time,
                'ensemble': ensemble_time
            }
        }
        
        # Get feature importance from Random Forest
        if hasattr(self.rf_classifier, 'feature_importances_'):
            self.feature_importance = dict(zip(
                self.feature_names[:len(self.rf_classifier.feature_importances_)],
                self.rf_classifier.feature_importances_
            ))
        
        self.is_fitted = True
        
        logger.info(f"Training completed!")
        logger.info(f"RF Accuracy: {self.training_scores['rf_accuracy']:.4f}")
        logger.info(f"SVM Accuracy: {self.training_scores['svm_accuracy']:.4f}")
        logger.info(f"Ensemble Accuracy: {self.training_scores['ensemble_accuracy']:.4f}")
        
        return self.training_scores
    
    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Make predictions with confidence scores
        
        Args:
            X: Feature matrix
            
        Returns:
            Tuple of (predictions, probabilities, confidence_scores)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        # Get ensemble predictions and probabilities
        predictions = self.ensemble_classifier.predict(X)
        probabilities = self.ensemble_classifier.predict_proba(X)
        
        # Confidence is the maximum probability
        confidence_scores = np.max(probabilities, axis=1)
        
        return predictions, probabilities, confidence_scores


def create_synthetic_building_dataset(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """
    Create a synthetic building dataset for testing the ensemble classifier
    
    Args:
        n_samples: Number of samples to generate
        random_state: Random state for reproducibility
        
    Returns:
        DataFrame with synthetic building features and labels
    """
    np.random.seed(random_state)
    
    # Building types: 0=residential, 1=commercial, 2=industrial
    building_types = np.random.choice([0, 1, 2], size=n_samples, p=[0.6, 0.3, 0.1])
    
    data = []
    
    for i in range(n_samples):
        building_type = building_types[i]
        
        if building_type == 0:  # Residential
            area = np.random.lognormal(4.0, 0.5)  # ~50-200 sqm
            height = np.random.normal(5.0, 2.0)   # ~3-8m
            perimeter_area_ratio = np.random.normal(0.8, 0.2)
            building_density = np.random.poisson(15)
            
        elif building_type == 1:  # Commercial
            area = np.random.lognormal(5.5, 0.8)  # ~200-1000 sqm
            height = np.random.normal(8.0, 3.0)   # ~5-15m
            perimeter_area_ratio = np.random.normal(0.6, 0.15)
            building_density = np.random.poisson(25)
            
        else:  # Industrial
            area = np.random.lognormal(6.5, 1.0)  # ~500-5000 sqm
            height = np.random.normal(12.0, 4.0)  # ~8-20m
            perimeter_area_ratio = np.random.normal(0.5, 0.1)
            building_density = np.random.poisson(5)
        
        # Ensure positive values
        area = max(20, area)
        height = max(2.5, height)
        perimeter_area_ratio = max(0.2, perimeter_area_ratio)
        building_density = max(1, building_density)
        
        # Calculate derived features
        perimeter = perimeter_area_ratio * np.sqrt(area)
        compactness = (4 * np.pi * area) / (perimeter ** 2)
        
        data.append({
            'area': area,
            'height': height,
            'perimeter': perimeter,
            'perimeter_area_ratio': perimeter_area_ratio,
            'compactness': compactness,
            'building_density': building_density,
            'building_type': building_type
        })
    
    return pd.DataFrame(data)


# Alias for backward compatibility
EnsembleWasteClassifier = EnsembleBuildingClassifier


if __name__ == "__main__":
    print("Building Type Ensemble Classifier Demo")
    print("=" * 50)
    
    # Create synthetic dataset
    print("Creating synthetic building dataset...")
    df = create_synthetic_building_dataset(n_samples=2000)
    print(f"Dataset created with {len(df)} samples")
    print(f"Class distribution:\n{df['building_type'].value_counts()}")
    
    # Initialize classifier
    classifier = EnsembleBuildingClassifier(random_state=42)
    
    # Prepare features
    X, y = classifier.prepare_features(df, target_column='building_type')
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nTrain set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train ensemble
    print("\nTraining ensemble classifier...")
    training_scores = classifier.train_ensemble(X_train, y_train)
    
    print(f"\nFinal Ensemble Accuracy: {training_scores['ensemble_accuracy']:.4f}")
    print("Demo completed successfully!") 