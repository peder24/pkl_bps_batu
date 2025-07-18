"""
IPH Dashboard - Frontend Server
"""

from flask import Flask, render_template
import socket
import threading
import webbrowser
import time

# Create Flask frontend app
frontend_app = Flask(__name__, 
                    static_folder='static',
                    static_url_path='/static',
                    template_folder='templates')

def find_free_port():
    """Find a free port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

@frontend_app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@frontend_app.route('/admin')
def admin():
    """Admin page"""
    return render_template('admin.html')

def open_browser(port):
    """Open browser after delay"""
    time.sleep(3)
    webbrowser.open(f'http://localhost:{port}')

def run_frontend_server():
    """Run the frontend server"""
    print("🌐 IPH Dashboard - Frontend Server")
    print("=" * 50)
    
    port = find_free_port()
    
    print(f"🌐 Dashboard URL: http://localhost:{port}")
    print("📡 API Server should be running on: http://localhost:5001")
    print("\n💡 Make sure to start api_server.py first!")
    print("⏹️  Tekan Ctrl+C untuk menghentikan")
    print("=" * 50)
    
    # Open browser
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    try:
        frontend_app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Frontend Server dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ Frontend Server error: {e}")

if __name__ == '__main__':
    run_frontend_server()