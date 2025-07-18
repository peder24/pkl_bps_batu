"""
Insight Analyzer untuk Dashboard IPH
Menganalisis performa model dan memberikan insight dinamis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import statistics
import traceback

class InsightAnalyzer:
    def __init__(self, data_processor, model_handler):
        self.data_processor = data_processor
        self.model_handler = model_handler
        self.model_performance = {}
        self.trend_analysis = {}
        self.volatility_analysis = {}
        print("✅ InsightAnalyzer initialized successfully")
        
    def analyze_model_performance(self, model_name, historical_data, forecast_data):
        """Analisis performa model secara komprehensif"""
        try:
            print(f"🔍 Analyzing performance for {model_name}")
            
            # Validasi input
            if len(historical_data) < 10:
                print(f"⚠️ Insufficient historical data: {len(historical_data)}")
                return None
            
            if len(forecast_data) < 1:
                print(f"⚠️ No forecast data provided")
                return None
            
            # Hitung metrik performa
            latest_features = self.data_processor.get_latest_features()
            prediction, lower_bound, upper_bound = self.model_handler.predict_with_confidence(
                model_name, latest_features
            )
            
            # Analisis trend dari data historis
            recent_values = historical_data['Indikator_Harga'].tail(10).tolist()
            trend_direction = self.calculate_trend_direction(recent_values)
            trend_strength = self.calculate_trend_strength(recent_values)
            
            # Analisis volatilitas
            volatility = float(np.std(recent_values))
            volatility_level = self.classify_volatility(volatility)
            
            # Analisis forecast
            forecast_values = [float(item['prediction']) for item in forecast_data]
            forecast_trend = self.calculate_trend_direction(forecast_values)
            forecast_volatility = float(np.std(forecast_values))
            
            # Confidence interval analysis
            confidence_width = float(upper_bound[0] - lower_bound[0])
            confidence_level = self.classify_confidence(confidence_width)
            
            # Recent accuracy estimation
            recent_accuracy = self.estimate_recent_accuracy(model_name, historical_data)
            
            performance = {
                'model_name': model_name,
                'prediction': float(prediction[0]),
                'confidence_interval': [float(lower_bound[0]), float(upper_bound[0])],
                'confidence_width': confidence_width,
                'confidence_level': confidence_level,
                'trend': {
                    'direction': trend_direction,
                    'strength': trend_strength,
                    'forecast_direction': forecast_trend
                },
                'volatility': {
                    'value': volatility,
                    'level': volatility_level,
                    'forecast_volatility': forecast_volatility
                },
                'recent_accuracy': recent_accuracy
            }
            
            print(f"✅ Performance analysis completed for {model_name}")
            return performance
            
        except Exception as e:
            print(f"❌ Error analyzing {model_name}: {str(e)}")
            return None
    
    def calculate_trend_direction(self, values):
        """Hitung arah trend"""
        try:
            if len(values) < 2:
                return 'stabil'
            
            # Linear regression sederhana
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.1:
                return 'naik'
            elif slope < -0.1:
                return 'turun'
            else:
                return 'stabil'
        except Exception as e:
            print(f"⚠️ Error calculating trend direction: {e}")
            return 'stabil'
    
    def calculate_trend_strength(self, values):
        """Hitung kekuatan trend"""
        try:
            if len(values) < 2:
                return 'lemah'
            
            x = np.arange(len(values))
            slope = abs(np.polyfit(x, values, 1)[0])
            
            if slope > 0.5:
                return 'kuat'
            elif slope > 0.2:
                return 'sedang'
            else:
                return 'lemah'
        except Exception as e:
            print(f"⚠️ Error calculating trend strength: {e}")
            return 'lemah'
    
    def classify_volatility(self, volatility):
        """Klasifikasi tingkat volatilitas"""
        try:
            if volatility < 0.5:
                return 'rendah'
            elif volatility < 1.5:
                return 'sedang'
            else:
                return 'tinggi'
        except Exception as e:
            print(f"⚠️ Error classifying volatility: {e}")
            return 'sedang'
    
    def classify_confidence(self, width):
        """Klasifikasi tingkat confidence"""
        try:
            if width < 1.0:
                return 'tinggi'
            elif width < 2.0:
                return 'sedang'
            else:
                return 'rendah'
        except Exception as e:
            print(f"⚠️ Error classifying confidence: {e}")
            return 'sedang'
    
    def estimate_recent_accuracy(self, model_name, historical_data):
        """Estimasi akurasi recent berdasarkan pola historis"""
        try:
            model_accuracy = {
                'Random_Forest': 0.85,
                'LightGBM': 0.92,
                'KNN': 1.15,
                'XGBoost_Advanced': 0.88
            }
            
            base_mae = model_accuracy.get(model_name, 1.0)
            
            # Adjust based on recent volatility
            recent_values = historical_data['Indikator_Harga'].tail(10).tolist()
            recent_volatility = np.std(recent_values)
            
            if recent_volatility > 2.0:
                adjusted_mae = base_mae * 1.3
            elif recent_volatility < 0.5:
                adjusted_mae = base_mae * 0.8
            else:
                adjusted_mae = base_mae
            
            return float(adjusted_mae)
            
        except Exception as e:
            print(f"⚠️ Error estimating accuracy: {e}")
            return 1.0
    
    def generate_model_insights(self, model_performance):
        """Generate insight dinamis untuk model"""
        try:
            print(f"💡 Generating insights for {model_performance['model_name']}")
            
            insights = []
            
            model_name = model_performance['model_name']
            prediction = model_performance['prediction']
            confidence = model_performance['confidence_level']
            trend = model_performance['trend']
            volatility = model_performance['volatility']
            accuracy = model_performance['recent_accuracy']
            
            # Insight prediksi
            if prediction > 2:
                insights.append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'Prediksi Inflasi Tinggi',
                    'message': f'Model {model_name} memprediksi kenaikan IPH sebesar {prediction:.2f}%, menunjukkan tekanan inflasi yang perlu diwaspadai.'
                })
            elif prediction < -2:
                insights.append({
                    'type': 'info',
                    'icon': '📉',
                    'title': 'Prediksi Deflasi',
                    'message': f'Model {model_name} memprediksi penurunan IPH sebesar {abs(prediction):.2f}%, mengindikasikan potensi deflasi.'
                })
            else:
                insights.append({
                    'type': 'success',
                    'icon': '✅',
                    'title': 'Prediksi Stabil',
                    'message': f'Model {model_name} memprediksi IPH relatif stabil dengan perubahan {prediction:.2f}%.'
                })
            
            # Insight confidence
            if confidence == 'tinggi':
                insights.append({
                    'type': 'success',
                    'icon': '🎯',
                    'title': 'Confidence Tinggi',
                    'message': f'Model {model_name} menunjukkan confidence tinggi dengan interval prediksi yang sempit.'
                })
            elif confidence == 'rendah':
                insights.append({
                    'type': 'warning',
                    'icon': '⚡',
                    'title': 'Confidence Rendah',
                    'message': f'Model {model_name} menunjukkan confidence rendah dengan interval prediksi yang lebar.'
                })
            
            # Insight volatilitas
            if volatility['level'] == 'tinggi':
                insights.append({
                    'type': 'warning',
                    'icon': '🌪️',
                    'title': 'Volatilitas Tinggi',
                    'message': f'Volatilitas tinggi ({volatility["value"]:.2f}) menunjukkan ketidakstabilan harga.'
                })
            elif volatility['level'] == 'rendah':
                insights.append({
                    'type': 'success',
                    'icon': '🎯',
                    'title': 'Volatilitas Rendah',
                    'message': f'Volatilitas rendah ({volatility["value"]:.2f}) menunjukkan stabilitas harga.'
                })
            
            print(f"✅ Generated {len(insights)} insights for {model_name}")
            return insights
            
        except Exception as e:
            print(f"❌ Error generating insights: {str(e)}")
            return [{
                'type': 'error',
                'icon': '⚠️',
                'title': 'Error Generating Insights',
                'message': f'Terjadi error saat menganalisis: {str(e)}'
            }]
    
    def generate_market_insights(self, historical_data, forecast_data):
        """Generate insight pasar secara keseluruhan"""
        try:
            print("📊 Generating market insights")
            
            insights = []
            
            # Validasi input
            if len(historical_data) < 20:
                return [{
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'Data Terbatas',
                    'message': 'Data historis terbatas untuk analisis pasar yang komprehensif.'
                }]
            
            # Analisis trend jangka panjang
            all_values = historical_data['Indikator_Harga'].tolist()
            long_term_trend = self.calculate_trend_direction(all_values[-20:])
            
            # Analisis volatilitas pasar
            market_volatility = np.std(all_values[-12:])
            
            # Market trend insight
            if long_term_trend == 'naik':
                insights.append({
                    'type': 'warning',
                    'icon': '📈',
                    'title': 'Trend Jangka Panjang Naik',
                    'message': f'Pasar menunjukkan trend kenaikan dalam 20 minggu terakhir.'
                })
            elif long_term_trend == 'turun':
                insights.append({
                    'type': 'info',
                    'icon': '📉',
                    'title': 'Trend Jangka Panjang Turun',
                    'message': f'Pasar menunjukkan trend penurunan dalam 20 minggu terakhir.'
                })
            
            # Market volatility insight
            if market_volatility > 2.0:
                insights.append({
                    'type': 'warning',
                    'icon': '⚡',
                    'title': 'Pasar Volatil',
                    'message': f'Volatilitas pasar tinggi ({market_volatility:.2f}) menunjukkan ketidakpastian.'
                })
            elif market_volatility < 0.5:
                insights.append({
                    'type': 'success',
                    'icon': '🎯',
                    'title': 'Pasar Stabil',
                    'message': f'Volatilitas pasar rendah ({market_volatility:.2f}) menunjukkan stabilitas harga.'
                })
            
            print(f"✅ Generated {len(insights)} market insights")
            return insights
            
        except Exception as e:
            print(f"❌ Error generating market insights: {str(e)}")
            return [{
                'type': 'error',
                'icon': '⚠️',
                'title': 'Error Market Analysis',
                'message': f'Terjadi error saat menganalisis pasar: {str(e)}'
            }]