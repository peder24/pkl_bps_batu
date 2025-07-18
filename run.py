"""
Simple launcher for IPH Dashboard
"""

import subprocess
import sys
import os

def main():
    """Main launcher function"""
    print("🚀 IPH Dashboard Launcher")
    print("=" * 40)
    
    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("❌ app.py not found!")
        return
    
    # Check if required files exist
    required_files = ['model_handler.py', 'data_processor.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return
    
    print("✅ All required files found")
    print("🌟 Starting dashboard...")
    print("=" * 40)
    
    try:
        # Run the app
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()