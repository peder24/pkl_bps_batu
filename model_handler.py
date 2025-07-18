import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import warnings
warnings.filterwarnings('ignore')

class ModelHandler:
    def __init__(self):
        self.models = {}
        self.model_paths = {
            'Random_Forest': 'static/models/Random_Forest.pkl',
            'LightGBM': 'static/models/LightGBM.pkl',
            'KNN': 'static/models/KNN.pkl',
            'XGBoost_Advanced': 'static/models/XGBoost_Advanced.pkl'
        }
        self.model_info = {}
        self.load_models()
    
    def load_models(self):
        """Load all available models"""
        print("🔄 Loading models...")
        
        for model_name, path in self.model_paths.items():
            if os.path.exists(path):
                try:
                    # Load the model
                    model = joblib.load(path)
                    
                    # Test prediction to ensure model works
                    test_features = np.array([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]])
                    test_pred = model.predict(test_features)
                    
                    self.models[model_name] = model
                    self.model_info[model_name] = {
                        'loaded': True,
                        'error': None,
                        'type': type(model).__name__,
                        'test_prediction': float(test_pred[0])
                    }
                    print(f"   ✅ {model_name} loaded successfully (test pred: {test_pred[0]:.3f})")
                    
                except Exception as e:
                    print(f"   ❌ Error loading {model_name}: {str(e)}")
                    self.model_info[model_name] = {
                        'loaded': False,
                        'error': str(e),
                        'type': None
                    }
            else:
                print(f"   ⚠️  {model_name} file not found: {path}")
                self.model_info[model_name] = {
                    'loaded': False,
                    'error': f"File not found: {path}",
                    'type': None
                }
        
        # Check if any models were loaded
        if not self.models:
            raise ValueError("No models could be loaded. Please check your model files in static/models/")
    
    def get_available_models(self):
        """Return list of available models"""
        return list(self.models.keys())
    
    def get_model_info(self):
        """Return model information"""
        return self.model_info
    
    def predict(self, model_name, features):
        """Make prediction using specified model"""
        if model_name not in self.models:
            available_models = list(self.models.keys())
            if available_models:
                print(f"⚠️  Model {model_name} not available, using {available_models[0]}")
                model_name = available_models[0]
            else:
                raise ValueError("No models available")
        
        model = self.models[model_name]
        
        try:
            # Ensure features are in correct format
            if isinstance(features, list):
                features = np.array([features])
            elif len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            prediction = model.predict(features)
            print(f"🔮 {model_name} prediction: {prediction[0]:.3f} (features: {features[0]})")
            return prediction
        except Exception as e:
            print(f"❌ Prediction error with {model_name}: {e}")
            print(f"   Features shape: {features.shape}")
            print(f"   Features: {features}")
            raise
    
    def predict_with_confidence(self, model_name, features, confidence_level=0.95):
        """Make prediction with confidence interval - DIPERBAIKI"""
        if model_name not in self.models:
            available_models = list(self.models.keys())
            if available_models:
                model_name = available_models[0]
            else:
                raise ValueError("No models available")
        
        model = self.models[model_name]
        
        try:
            # Ensure features are in correct format
            if isinstance(features, list):
                features = np.array([features])
            elif len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            # Get base prediction
            prediction = model.predict(features)
            
            # Calculate confidence interval based on model type
            if hasattr(model, 'estimators_') and len(model.estimators_) > 1:
                # For ensemble models (Random Forest, etc.)
                predictions = []
                n_estimators = min(50, len(model.estimators_))
                
                for estimator in model.estimators_[:n_estimators]:
                    try:
                        pred = estimator.predict(features)
                        predictions.append(pred[0])
                    except:
                        continue
                
                if predictions:
                    predictions = np.array(predictions)
                    mean_pred = np.mean(predictions)
                    std_pred = np.std(predictions)
                    
                    # Calculate confidence interval
                    z_score = 1.96 if confidence_level == 0.95 else 2.58
                    lower_bound = np.array([mean_pred - z_score * std_pred])
                    upper_bound = np.array([mean_pred + z_score * std_pred])
                    
                    # Use ensemble mean as prediction
                    prediction = np.array([mean_pred])
                else:
                    # Fallback to simple error estimation
                    error_margin = 0.5
                    lower_bound = prediction - error_margin
                    upper_bound = prediction + error_margin
            else:
                # For other models, use simple error estimation
                # Base error margin on model type
                error_margins = {
                    'KNN': 0.8,
                    'LightGBM': 0.6,
                    'XGBoost_Advanced': 0.5,
                    'Random_Forest': 0.5
                }
                
                error_margin = error_margins.get(model_name, 0.5)
                lower_bound = prediction - error_margin
                upper_bound = prediction + error_margin
            
            print(f"🔮 {model_name} prediction: {prediction[0]:.3f} [{lower_bound[0]:.3f}, {upper_bound[0]:.3f}]")
            return prediction, lower_bound, upper_bound
                
        except Exception as e:
            print(f"❌ Confidence prediction error with {model_name}: {e}")
            print(f"   Features shape: {features.shape}")
            print(f"   Features: {features}")
            raise
    
    def evaluate_model(self, model_name, X_test, y_test):
        """Evaluate model performance"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")
        
        try:
            model = self.models[model_name]
            predictions = model.predict(X_test)
            
            mae = mean_absolute_error(y_test, predictions)
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            
            return {
                'mae': mae,
                'rmse': rmse,
                'predictions': predictions.tolist()
            }
        except Exception as e:
            print(f"❌ Evaluation error with {model_name}: {e}")
            raise
    
    def get_model_details(self, model_name):
        """Get detailed information about a specific model"""
        if model_name not in self.models:
            return None
        
        model = self.models[model_name]
        details = {
            'name': model_name,
            'type': type(model).__name__,
            'loaded': True
        }
        
        # Add model-specific details
        if hasattr(model, 'n_estimators'):
            details['n_estimators'] = model.n_estimators
        if hasattr(model, 'max_depth'):
            details['max_depth'] = model.max_depth
        if hasattr(model, 'n_neighbors'):
            details['n_neighbors'] = model.n_neighbors
        if hasattr(model, 'learning_rate'):
            details['learning_rate'] = model.learning_rate
        
        return details