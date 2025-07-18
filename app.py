"""
IPH Dashboard - Main Application (Simplified for existing models)
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import socket
import threading
import webbrowser
import time
import sys
import traceback

from model_handler import ModelHandler
from data_processor import DataProcessor

# Configure Flask
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

app.config['DEBUG'] = False

# Global variables
model_handler = None
data_processor = None
initialization_error = None

def initialize_components():
    """Initialize application components"""
    global model_handler, data_processor, initialization_error
    
    print("🔄 Initializing application components...")
    
    try:
        # Initialize data processor first
        print("📊 Loading data processor...")
        data_processor = DataProcessor('data_iph_modeling.csv')
        print("✅ Data processor initialized")
        
        # Initialize model handler
        print("🤖 Loading model handler...")
        model_handler = ModelHandler()
        print("✅ Model handler initialized")
        
        # Test basic functionality
        print("🧪 Testing basic functionality...")
        
        # Test data loading
        historical_data = data_processor.get_historical_data()
        print(f"   📈 Historical data: {len(historical_data)} records")
        
        # Test model availability
        available_models = model_handler.get_available_models()
        print(f"   🤖 Available models: {available_models}")
        
        # Test feature extraction
        latest_features = data_processor.get_latest_features()
        print(f"   🎯 Latest features shape: {latest_features.shape}")
        
        # Test prediction
        if available_models:
            test_model = available_models[0]
            prediction, lower, upper = model_handler.predict_with_confidence(test_model, latest_features)
            print(f"   🔮 Test prediction with {test_model}: {prediction[0]:.3f}")
        
        return True
        
    except Exception as e:
        initialization_error = f"Initialization error: {str(e)}"
        print(f"❌ {initialization_error}")
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return False

def find_free_port():
    """Find a free port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def check_initialization():
    """Check if components are properly initialized"""
    if initialization_error:
        return jsonify({
            'error': 'System not properly initialized',
            'details': initialization_error
        }), 503
    return None

@app.route('/')
def dashboard():
    """Main dashboard page"""
    if initialization_error:
        return render_template('error.html', error=initialization_error)
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    """Get available models"""
    print("📡 API: /api/models called")
    
    error_response = check_initialization()
    if error_response:
        return error_response
    
    try:
        models = model_handler.get_available_models()
        print(f"✅ API: Returning {len(models)} models: {models}")
        
        return jsonify({
            'models': models,
            'default': models[0] if models else None,
            'count': len(models)
        })
    except Exception as e:
        print(f"❌ API: Error in get_models: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast/<model_name>')
def get_forecast(model_name):
    """Get forecast data"""
    print(f"📡 API: /api/forecast/{model_name} called")
    
    error_response = check_initialization()
    if error_response:
        return error_response
    
    try:
        # Get parameters
        months = request.args.get('months', type=int)
        print(f"📊 Parameters: model={model_name}, months={months}")
        
        # Get historical data
        historical_data = data_processor.get_historical_data(months)
        print(f"   ✅ Got {len(historical_data)} historical records")
        
        # Get latest features
        latest_features = data_processor.get_latest_features()
        print(f"   ✅ Features shape: {latest_features.shape}")
        
        # Check if model exists
        available_models = model_handler.get_available_models()
        if model_name not in available_models:
            print(f"❌ Model {model_name} not found in {available_models}")
            return jsonify({'error': f'Model {model_name} not available'}), 400
        
        # Make prediction
        prediction, lower_bound, upper_bound = model_handler.predict_with_confidence(
            model_name, latest_features
        )
        print(f"   ✅ Prediction: {prediction[0]:.3f}")
        
        # Generate forecast features
        forecast_features = data_processor.generate_forecast_features(n_steps=4)
        
        # Generate multi-step forecast
        forecast_data = []
        last_date = historical_data['Tanggal'].max()
        
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
        for _, row in historical_data.iterrows():
            historical_json.append({
                'date': row['Tanggal'].strftime('%Y-%m-%d'),
                'value': float(row['Indikator_Harga'])
            })
        
        # Prepare response
        mae_values = {
            'Random_Forest': 0.85,
            'LightGBM': 0.92,
            'KNN': 1.15,
            'XGBoost_Advanced': 0.88
        }
        
        response_data = {
            'historical': historical_json,
            'forecast': forecast_data,
            'model_info': {
                'name': model_name,
                'mae': mae_values.get(model_name, 1.0),
                'next_week_prediction': float(prediction[0])
            }
        }
        
        print(f"✅ API: Forecast response prepared successfully")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ API: Error in get_forecast: {str(e)}")
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Forecast error: {str(e)}'}), 500

@app.route('/api/kpi')
def get_kpi():
    """Get KPI data"""
    print("📡 API: /api/kpi called")
    
    error_response = check_initialization()
    if error_response:
        return error_response
    
    try:
        historical_data = data_processor.get_historical_data()
        latest_features = data_processor.get_latest_features()
        
        # Get prediction from available model
        available_models = model_handler.get_available_models()
        if available_models:
            default_model = available_models[0]
            prediction, _, _ = model_handler.predict_with_confidence(default_model, latest_features)
            next_week_pred = float(prediction[0])
        else:
            next_week_pred = 0.0
        
        # Calculate KPIs
        if len(historical_data) >= 2:
            latest_value = historical_data['Indikator_Harga'].iloc[-1]
            previous_value = historical_data['Indikator_Harga'].iloc[-2]
            change = latest_value - previous_value
        else:
            latest_value = 0.0
            change = 0.0
        
        kpi_data = {
            'next_week_prediction': next_week_pred,
            'model_accuracy': 0.85,
            'last_change': float(latest_value),
            'change_from_previous': float(change),
            'last_update': historical_data['Tanggal'].max().strftime('%d %B %Y'),
            'total_data_points': len(historical_data)
        }
        
        print(f"✅ API: KPI data prepared")
        return jsonify(kpi_data)
        
    except Exception as e:
        print(f"❌ API: Error in get_kpi: {str(e)}")
        return jsonify({'error': f'KPI error: {str(e)}'}), 500

@app.route('/api/what-if', methods=['POST'])
def what_if_analysis():
    """What-if analysis"""
    print("📡 API: /api/what-if called")
    
    error_response = check_initialization()
    if error_response:
        return error_response
    
    try:
        data = request.json
        current_iph = data.get('current_iph', 0)
        model_name = data.get('model', None)
        
        print(f"📊 What-if parameters: iph={current_iph}, model={model_name}")
        
        # Get historical data
        historical_data = data_processor.get_historical_data()
        recent_values = historical_data['Indikator_Harga'].tail(6).tolist()
        recent_values.append(current_iph)
        
        # Calculate features
        lag_1 = recent_values[-2]
        lag_2 = recent_values[-3]
        lag_3 = recent_values[-4]
        lag_4 = recent_values[-5]
        ma_3 = np.mean(recent_values[-3:])
        ma_7 = np.mean(recent_values[-7:])
        
        what_if_features = np.array([[lag_1, lag_2, lag_3, lag_4, ma_3, ma_7]])
        
        # Make prediction
        available_models = model_handler.get_available_models()
        if not model_name or model_name not in available_models:
            model_name = available_models[0] if available_models else None
            
        if not model_name:
            return jsonify({'error': 'No models available'}), 500
        
        prediction, lower_bound, upper_bound = model_handler.predict_with_confidence(
            model_name, what_if_features
        )
        
        result = {
            'prediction': float(prediction[0]),
            'lower_bound': float(lower_bound[0]),
            'upper_bound': float(upper_bound[0]),
            'scenario': f"Jika IPH minggu ini {current_iph}%",
            'model_used': model_name
        }
        
        print(f"✅ API: What-if result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ API: Error in what_if_analysis: {str(e)}")
        return jsonify({'error': f'What-if analysis error: {str(e)}'}), 500

@app.route('/api/download-data')
def download_data():
    """Download data"""
    print("📡 API: /api/download-data called")
    
    error_response = check_initialization()
    if error_response:
        return error_response
    
    try:
        historical_data = data_processor.get_historical_data()
        csv_data = historical_data.to_csv(index=False)
        
        result = {
            'csv_data': csv_data,
            'filename': f'data_iph_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'total_records': len(historical_data)
        }
        
        print(f"✅ API: Download data prepared: {result['total_records']} records")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ API: Error in download_data: {str(e)}")
        return jsonify({'error': f'Download error: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check"""
    print("📡 API: /api/health called")
    
    if initialization_error:
        return jsonify({
            'status': 'error',
            'error': initialization_error,
            'timestamp': datetime.now().isoformat()
        }), 503
    
    try:
        health_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'models_loaded': len(model_handler.get_available_models()),
            'data_points': len(data_processor.get_historical_data()),
            'available_models': model_handler.get_available_models(),
            'data_summary': data_processor.get_data_summary()
        }
        
        print(f"✅ API: Health check: {health_info}")
        return jsonify(health_info)
        
    except Exception as e:
        print(f"❌ API: Error in health_check: {str(e)}")
        return jsonify({'error': str(e)}), 500

def open_browser(port):
    """Open browser after delay"""
    time.sleep(2)
    webbrowser.open(f'http://localhost:{port}')

def run_app():
    """Run the Flask application"""
    print("🚀 IPH Dashboard - Starting Application")
    print("=" * 60)
    
    # Initialize components
    if not initialize_components():
        print("\n❌ Failed to initialize components")
        print("💡 Check the error messages above for details")
        print("📁 Make sure your model files are in static/models/")
        print("📊 Make sure data_iph_modeling.csv exists")
        
        response = input("\nStart server anyway to see error page? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Find free port
    port = find_free_port()
    
    # Display startup info
    if not initialization_error:
        data_summary = data_processor.get_data_summary()
        print(f"📊 Models loaded: {model_handler.get_available_models()}")
        print(f"📈 Data points: {data_summary.get('total_records', 0)}")
        if 'date_range' in data_summary:
            print(f"📅 Date range: {data_summary['date_range']['start']} to {data_summary['date_range']['end']}")
    
    print(f"🌐 Dashboard URL: http://localhost:{port}")
    print(f"💚 Health Check: http://localhost:{port}/api/health")
    
    print("\n" + "="*60)
    print("✅ Server starting...")
    print("🌐 Browser akan terbuka otomatis...")
    print("📝 Check console for detailed API logs")
    print("⏹️  Tekan Ctrl+C untuk menghentikan")
    print("="*60)
    
    # Open browser
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Start Flask app
    try:
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Dashboard dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    run_app()