"""
IPH Dashboard Launcher - Runs both API and Frontend servers
"""

import subprocess
import sys
import os
import time
import threading

def run_api_server():
    """Run the API server"""
    print("🔄 Starting API Server...")
    try:
        subprocess.run([sys.executable, 'api_server.py'], check=True)
    except KeyboardInterrupt:
        print("👋 API Server stopped")
    except Exception as e:
        print(f"❌ API Server error: {e}")

def run_frontend_server():
    """Run the frontend server"""
    print("🔄 Starting Frontend Server...")
    time.sleep(2)  # Wait for API server to start
    try:
        subprocess.run([sys.executable, 'frontend_server.py'], check=True)
    except KeyboardInterrupt:
        print("👋 Frontend Server stopped")
    except Exception as e:
        print(f"❌ Frontend Server error: {e}")

def main():
    """Main launcher function"""
    print("🚀 IPH Dashboard - Separated Architecture")
    print("=" * 60)
    
    # Check required files
    required_files = [
        'api_server.py',
        'frontend_server.py',
        'model_handler.py',
        'data_processor.py',
        'data_iph_modeling.csv'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return
    
    # Check model directory
    if not os.path.exists('static/models'):
        print("❌ Model directory 'static/models' not found!")
        print("💡 Create the directory and place your .pkl model files there")
        return
    
    print("✅ All required files found")
    print("🎯 Starting both servers...")
    print("=" * 60)
    
    try:
        # Start API server in a separate thread
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        api_thread.start()
        
        # Start frontend server in main thread
        run_frontend_server()
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()