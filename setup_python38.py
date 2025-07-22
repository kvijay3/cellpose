#!/usr/bin/env python3
"""
Setup script for Python 3.8 compatibility
This script helps set up the Cellpose Django API on Python 3.8
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print(f"❌ Python {version.major}.{version.minor} detected. This project requires Python 3.8+")
        return False
    
    if version.minor == 8:
        print(f"✅ Python {version.major}.{version.minor} detected - using Python 3.8 compatible packages")
    else:
        print(f"✅ Python {version.major}.{version.minor} detected - you can use the regular requirements.txt")
    
    return True

def install_requirements():
    """Install requirements with Python 3.8 compatibility"""
    try:
        print("📦 Installing Python 3.8 compatible packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def setup_django():
    """Set up Django database and migrations"""
    try:
        print("🗄️  Setting up Django database...")
        
        # Make migrations
        subprocess.check_call([sys.executable, "manage.py", "makemigrations"])
        print("✅ Migrations created")
        
        # Run migrations
        subprocess.check_call([sys.executable, "manage.py", "migrate"])
        print("✅ Database migrated")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup Django: {e}")
        return False

def create_media_directories():
    """Create necessary media directories"""
    directories = [
        "media",
        "media/input_images",
        "media/results",
        "media/results/masks",
        "media/results/flows", 
        "media/results/segmented",
        "media/results/tif_archive"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Media directories created")

def main():
    """Main setup function"""
    print("🔬 Cellpose Django API Setup (Python 3.8 Compatible)")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n💡 If you're still having issues, try:")
        print("   pip install --upgrade pip")
        print("   pip install -r requirements.txt --no-cache-dir")
        sys.exit(1)
    
    # Create media directories
    create_media_directories()
    
    # Setup Django
    if not setup_django():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 Next steps:")
    print("   1. Start the server: python manage.py runserver")
    print("   2. Test the API: python example_client.py")
    print("   3. Visit admin: http://localhost:8000/admin/")
    print("\n📚 Documentation:")
    print("   - API Tutorial: CELLPOSE_API_TUTORIAL.md")
    print("   - Quick Start: README_API.md")

if __name__ == "__main__":
    main()

