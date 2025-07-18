"""
IPH Dashboard - API Server dengan Insight Analysis - DIPERBAIKI
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
try:
    from model_handler import ModelHandler
    from data_processor import DataProcessor
    from insight_analyzer import InsightAnalyzer
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

# Create Flask API app
api_app = Flask(__name__)
CORS(api_app, origins=["http://localhost:*", "http://127.0.0.1:*"])

# Global variables
model_handler = None
data_processor = None
insight_analyzer = None
api_status = {
    'initialized': False,
    'error': None,
    'models_loaded': 0,
    'data_points': 0
}

def initialize_api():
    """Initialize API components"""
    global model_handler, data_processor, insight_analyzer, api_status
    
    logger.info("🔄 Initializing API components...")
    
    try:
        # Initialize data processor
        logger.info("📊 Loading data processor...")
        data_processor = DataProcessor('data_iph_modeling.csv')
        data_summary = data_processor.get_data_summary()
        logger.info(f"✅ Data processor initialized: {data_summary['total_records']} records")
        
        # Initialize model handler
        logger.info("🤖 Loading model handler...")
        model_handler = ModelHandler()
        available_models = model_handler.get_available_models()
        logger.info(f"✅ Model handler initialized: {len(available_models)} models")
        
        # Initialize insight analyzer
        logger.info("🧠 Loading insight analyzer...")
        insight_analyzer = InsightAnalyzer(data_processor, model_handler)
        logger.info("✅ Insight analyzer initialized")
        
        # Test functionality
        logger.info("🧪 Testing API functionality...")
        
        # Test data
        all_data = data_processor.get_all_data()
        logger.info(f"   📈 ALL data: {len(all_data)} records")
        
        # Test features
        latest_features = data_processor.get_latest_features()
        logger.info(f"   🎯 Latest features: {latest_features[0]}")
        
        # Test prediction
        if available_models:
            test_model = available_models[0]
            prediction, lower, upper = model_handler.predict_with_confidence(test_model, latest_features)
            logger.info(f"   🔮 Test prediction with {test_model}: {prediction[0]:.3f}")
        
        # Update status
        api_status.update({
            'initialized': True,
            'error': None,
            'models_loaded': len(available_models),
            'data_points': len(all_data)
        })
        
        logger.info("✅ API initialization completed successfully")
        return True
        
    except Exception as e:
        error_msg = f"API initialization failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        
        api_status.update({
            'initialized': False,
            'error': error_msg,
            'models_loaded': 0,
            'data_points': 0
        })
        return False

def require_initialization(f):
    """Decorator to check if API is initialized"""
    def decorated_function(*args, **kwargs):
        if not api_status['initialized']:
            return jsonify({
                'error': 'API not initialized',
                'details': api_status['error'],
                'status': api_status
            }), 503
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# API Routes
@api_app.route('/api/status')
def get_status():
    """Get API status"""
    logger.info("📡 API: /api/status called")
    return jsonify({
        'status': 'running',
        'initialized': api_status['initialized'],
        'error': api_status['error'],
        'models_loaded': api_status['models_loaded'],
        'data_points': api_status['data_points'],
        'timestamp': datetime.now().isoformat()
    })

@api_app.route('/api/models')
@require_initialization
def get_models():
    """Get available models with performance insights"""
    logger.info("📡 API: /api/models called")
    
    try:
        models = model_handler.get_available_models()
        model_info = model_handler.get_model_info()
        
        logger.info(f"✅ API: Returning {len(models)} models")
        
        return jsonify({
            'success': True,
            'models': models,
            'default': models[0] if models else None,
            'count': len(models),
            'model_info': model_info
        })
        
    except Exception as e:
        logger.error(f"❌ API: Error in get_models: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_app.route('/api/forecast/<model_name>')
@require_initialization
def get_forecast(model_name):
    """Get forecast data with insights - DIPERBAIKI"""
    logger.info(f"📡 API: /api/forecast/{model_name} called")
    
    try:
        # Get parameters
        months = request.args.get('months', type=int)
        logger.info(f"📊 Parameters: model={model_name}, months={months}")
        
        # Validate model
        available_models = model_handler.get_available_models()
        if model_name not in available_models:
            logger.error(f"❌ Model {model_name} not found in {available_models}")
            return jsonify({
                'success': False,
                'error': f'Model {model_name} not available',
                'available_models': available_models
            }), 400
        
        # Get data
        all_data = data_processor.get_all_data()
        logger.info(f"   ✅ Using ALL data for prediction: {len(all_data)} records")
        
        # For display chart, bisa filter
        if months:
            display_data = data_processor.get_historical_data(months)
        else:
            display_data = all_data
        
        logger.info(f"   📊 Display data: {len(display_data)} records")
        
        # Get features dan prediksi
        latest_features = data_processor.get_latest_features()
        logger.info(f"   🎯 Latest features: {latest_features[0]}")
        
        prediction, lower_bound, upper_bound = model_handler.predict_with_confidence(
            model_name, latest_features
        )
        logger.info(f"   🔮 Prediction: {prediction[0]:.3f}")
        
        # Generate forecast
        forecast_features = data_processor.generate_forecast_features(n_steps=4)
        forecast_data = []
        last_date = all_data['Tanggal'].max()
        
        for i in range(4):
            forecast_date = last_date + timedelta(weeks=i+1)
            step_features = forecast_features[i:i+1]
            
            step_pred, step_lower, step_upper = model_handler.predict_with_confidence(
                model_name, step_features
            )
            
            forecast_data.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'prediction': float(step_pred[0]),
                'lower_bound': float(step_lower[0]),
                'upper_bound': float(step_upper[0])
            })
        
        # Prepare historical data
        historical_json = []
        for _, row in display_data.iterrows():
            historical_json.append({
                'date': row['Tanggal'].strftime('%Y-%m-%d'),
                'value': float(row['Indikator_Harga'])
            })
        
        # PERBAIKAN: Generate insights dengan error handling
        model_insights = []
        market_insights = []
        
        try:
            logger.info(f"   🧠 Generating insights for {model_name}...")
            
            # Analyze performance
            performance = insight_analyzer.analyze_model_performance(
                model_name, all_data, forecast_data
            )
            
            if performance:
                logger.info(f"   ✅ Performance analysis completed")
                
                # Generate model insights
                model_insights = insight_analyzer.generate_model_insights(performance)
                logger.info(f"   💡 Generated {len(model_insights)} model insights")
                
                # Generate market insights
                market_insights = insight_analyzer.generate_market_insights(all_data, forecast_data)
                logger.info(f"   📊 Generated {len(market_insights)} market insights")
            else:
                logger.warning(f"   ⚠️ No performance data for {model_name}")
                model_insights = [{
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': 'Analisis Tidak Tersedia',
                    'message': 'Tidak dapat menganalisis performa model saat ini.'
                }]
                market_insights = []
            
        except Exception as insight_error:
            logger.error(f"   ❌ Error generating insights: {str(insight_error)}")
            
            # Fallback insights
            model_insights = [{
                'type': 'info',
                'icon': '📊',
                'title': 'Model Aktif',
                'message': f'Model {model_name} sedang digunakan untuk prediksi.'
            }]
            market_insights = [{
                'type': 'info',
                'icon': '📈',
                'title': 'Data Tersedia',
                'message': f'Menggunakan {len(all_data)} data historis untuk analisis.'
            }]
        
        # Model accuracy values
        mae_values = {
            'Random_Forest': 0.85,
            'LightGBM': 0.92,
            'KNN': 1.15,
            'XGBoost_Advanced': 0.88
        }
        
        # PERBAIKAN: Pastikan insights selalu ada
        insights_data = {
            'model_insights': model_insights,
            'market_insights': market_insights
        }
        
        response_data = {
            'success': True,
            'historical': historical_json,
            'forecast': forecast_data,
            'model_info': {
                'name': model_name,
                'mae': mae_values.get(model_name, 1.0),
                'next_week_prediction': float(prediction[0])
            },
            'insights': insights_data,  # PERBAIKAN: Selalu include insights
            'metadata': {
                'historical_points': len(historical_json),
                'forecast_points': len(forecast_data),
                'last_historical_date': last_date.strftime('%Y-%m-%d'),
                'forecast_start_date': forecast_data[0]['date'] if forecast_data else None,
                'features_used': latest_features[0].tolist(),
                'total_data_points': len(all_data)
            }
        }
        
        logger.info(f"✅ API: Forecast response with insights prepared successfully")
        logger.info(f"   📊 Model insights: {len(model_insights)}")
        logger.info(f"   📈 Market insights: {len(market_insights)}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ API: Error in get_forecast: {str(e)}")
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Forecast error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@api_app.route('/api/kpi')
@require_initialization
def get_kpi():
    """Get KPI data with insights"""
    logger.info("📡 API: /api/kpi called")
    
    try:
        all_data = data_processor.get_all_data()
        latest_features = data_processor.get_latest_features()
        
        # Get prediction from first available model
        available_models = model_handler.get_available_models()
        if available_models:
            default_model = available_models[0]
            prediction, _, _ = model_handler.predict_with_confidence(default_model, latest_features)
            next_week_pred = float(prediction[0])
        else:
            next_week_pred = 0.0
        
        # Calculate KPIs
        if len(all_data) >= 2:
            latest_value = all_data['Indikator_Harga'].iloc[-1]
            previous_value = all_data['Indikator_Harga'].iloc[-2]
            change = latest_value - previous_value
        else:
            latest_value = 0.0
            change = 0.0
        
        kpi_data = {
            'success': True,
            'next_week_prediction': next_week_pred,
            'model_accuracy': 0.85,
            'last_change': float(latest_value),
            'change_from_previous': float(change),
            'last_update': all_data['Tanggal'].max().strftime('%d %B %Y'),
            'total_data_points': len(all_data),
            'default_model': default_model if available_models else None,
            'features_used': latest_features[0].tolist()
        }
        
        logger.info(f"✅ API: KPI data prepared - prediction: {next_week_pred:.3f}")
        return jsonify(kpi_data)
        
    except Exception as e:
        logger.error(f"❌ API: Error in get_kpi: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'KPI error: {str(e)}'
        }), 500

@api_app.route('/api/what-if', methods=['POST'])
@require_initialization
def what_if_analysis():
    """What-if analysis with insights"""
    logger.info("📡 API: /api/what-if called")
    
    try:
        data = request.json
        current_iph = data.get('current_iph', 0)
        model_name = data.get('model', None)
        
        logger.info(f"📊 What-if parameters: iph={current_iph}, model={model_name}")
        
        # Validate model
        available_models = model_handler.get_available_models()
        if not model_name or model_name not in available_models:
            model_name = available_models[0] if available_models else None
            
        if not model_name:
            return jsonify({
                'success': False,
                'error': 'No models available'
            }), 500
        
        # Get context
        all_data = data_processor.get_all_data()
        recent_values = all_data['Indikator_Harga'].tail(6).tolist()
        recent_values.append(current_iph)
        
        # Calculate features
        lag_1 = recent_values[-2]
        lag_2 = recent_values[-3]
        lag_3 = recent_values[-4]
        lag_4 = recent_values[-5]
        ma_3 = np.mean(recent_values[-3:])
        ma_7 = np.mean(recent_values[-7:])
        
        what_if_features = np.array([[lag_1, lag_2, lag_3, lag_4, ma_3, ma_7]])
        logger.info(f"🎯 What-if features: {what_if_features[0]}")
        
        # Make prediction
        prediction, lower_bound, upper_bound = model_handler.predict_with_confidence(
            model_name, what_if_features
        )
        
        result = {
            'success': True,
            'prediction': float(prediction[0]),
            'lower_bound': float(lower_bound[0]),
            'upper_bound': float(upper_bound[0]),
            'scenario': f"Jika IPH minggu ini {current_iph}%",
            'model_used': model_name,
            'input_features': what_if_features[0].tolist(),
            'recent_context': recent_values[-7:]
        }
        
        logger.info(f"✅ API: What-if result: prediction={prediction[0]:.3f}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ API: Error in what_if_analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'What-if analysis error: {str(e)}'
        }), 500

@api_app.route('/api/download-data')
@require_initialization
def download_data():
    """Download data"""
    logger.info("📡 API: /api/download-data called")
    
    try:
        all_data = data_processor.get_all_data()
        csv_data = all_data.to_csv(index=False)
        
        result = {
            'success': True,
            'csv_data': csv_data,
            'filename': f'data_iph_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'total_records': len(all_data)
        }
        
        logger.info(f"✅ API: Download data prepared: {result['total_records']} records")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ API: Error in download_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Download error: {str(e)}'
        }), 500

@api_app.route('/api/health')
def health_check():
    """Comprehensive health check"""
    logger.info("📡 API: /api/health called")
    
    health_info = {
        'status': 'healthy' if api_status['initialized'] else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'api_status': api_status
    }
    
    if api_status['initialized']:
        try:
            all_data = data_processor.get_all_data()
            health_info.update({
                'models_loaded': len(model_handler.get_available_models()),
                'data_points': len(all_data),
                'available_models': model_handler.get_available_models(),
                'data_summary': data_processor.get_data_summary(),
                'insight_analyzer': 'active' if insight_analyzer else 'inactive'
            })
        except Exception as e:
            health_info.update({
                'status': 'degraded',
                'error': str(e)
            })
    
    status_code = 200 if health_info['status'] == 'healthy' else 503
    logger.info(f"✅ API: Health check: {health_info['status']}")
    return jsonify(health_info), status_code

@api_app.route('/api/debug/insights')
@require_initialization
def debug_insights():
    """Debug endpoint untuk testing insights"""
    logger.info("📡 API: /api/debug/insights called")
    
    try:
        all_data = data_processor.get_all_data()
        available_models = model_handler.get_available_models()
        
        if not available_models:
            return jsonify({
                'success': False,
                'error': 'No models available'
            }), 500
        
        test_model = available_models[0]
        logger.info(f"🧪 Testing insights with model: {test_model}")
        
        # Generate test forecast
        forecast_features = data_processor.generate_forecast_features(n_steps=4)
        forecast_data = []
        
        for i in range(4):
            step_features = forecast_features[i:i+1]
            step_pred, step_lower, step_upper = model_handler.predict_with_confidence(
                test_model, step_features
            )
            forecast_data.append({
                'prediction': float(step_pred[0]),
                'lower_bound': float(step_lower[0]),
                'upper_bound': float(step_upper[0])
            })
        
        logger.info(f"✅ Generated {len(forecast_data)} forecast points")
        
        # Test insight generation
        logger.info("🧠 Testing insight generation...")
        performance = insight_analyzer.analyze_model_performance(
            test_model, all_data, forecast_data
        )
        
        model_insights = []
        market_insights = []
        
        if performance:
            logger.info("✅ Performance analysis completed")
            model_insights = insight_analyzer.generate_model_insights(performance)
            market_insights = insight_analyzer.generate_market_insights(all_data, forecast_data)
            logger.info(f"✅ Generated {len(model_insights)} model insights")
            logger.info(f"✅ Generated {len(market_insights)} market insights")
        else:
            logger.warning("⚠️ No performance data generated")
            model_insights = [{
                'type': 'error',
                'icon': '⚠️',
                'title': 'No Performance Data',
                'message': 'Could not generate performance analysis'
            }]
            market_insights = []
        
        debug_data = {
            'success': True,
            'test_model': test_model,
            'performance': performance,
            'model_insights': model_insights,
            'market_insights': market_insights,
            'forecast_data': forecast_data,
            'insight_analyzer_status': 'active' if insight_analyzer else 'inactive',
            'data_points': len(all_data),
            'available_models': available_models
        }
        
        logger.info(f"✅ API: Debug insights completed successfully")
        return jsonify(debug_data)
        
    except Exception as e:
        logger.error(f"❌ API: Error in debug_insights: {str(e)}")
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@api_app.route('/api/test/insights')
@require_initialization
def test_insights():
    """Simple test for insights"""
    logger.info("📡 API: /api/test/insights called")
    
    try:
        # Create simple test data
        test_insights = {
            'model_insights': [
                {
                    'type': 'success',
                    'icon': '✅',
                    'title': 'Test Model Insight',
                    'message': 'This is a test insight to verify the system is working.'
                }
            ],
            'market_insights': [
                {
                    'type': 'info',
                    'icon': '📊',
                    'title': 'Test Market Insight',
                    'message': 'This is a test market insight.'
                }
            ]
        }
        
        logger.info("✅ API: Test insights generated successfully")
        return jsonify({
            'success': True,
            'insights': test_insights,
            'message': 'Test insights generated successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ API: Error in test_insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def run_api_server():
    """Run the API server"""
    print("🚀 IPH Dashboard - API Server with Insights (FIXED)")
    print("=" * 50)
    
    # Initialize API
    if initialize_api():
        print("✅ API initialized successfully")
        print(f"📊 Models loaded: {api_status['models_loaded']}")
        print(f"📈 Data points: {api_status['data_points']}")
        print("🧠 Insight analyzer: Active")
    else:
        print("❌ API initialization failed")
        print(f"🔍 Error: {api_status['error']}")
        print("⚠️  Starting server anyway for debugging...")
    
    print("\n🌐 API Endpoints:")
    print("   GET  /api/status      - API status")
    print("   GET  /api/health      - Health check")
    print("   GET  /api/models      - Available models")
    print("   GET  /api/kpi         - KPI data")
    print("   GET  /api/forecast/<model> - Forecast data with insights")
    print("   POST /api/what-if     - What-if analysis")
    print("   GET  /api/download-data - Download data")
    print("   GET  /api/debug/insights - Debug insights")
    print("   GET  /api/test/insights - Test insights")
    
    print(f"\n🔗 API Base URL: http://localhost:5001")
    print("🧪 Test insights: http://localhost:5001/api/test/insights")
    print("🔍 Debug insights: http://localhost:5001/api/debug/insights")
    print("📝 Check console for detailed API logs")
    print("⏹️  Tekan Ctrl+C untuk menghentikan")
    print("=" * 50)
    
    try:
        api_app.run(
            host='127.0.0.1',
            port=5001,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 API Server dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ API Server error: {e}")

if __name__ == '__main__':
    run_api_server()