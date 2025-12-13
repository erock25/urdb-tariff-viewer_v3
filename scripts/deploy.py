#!/usr/bin/env python3
"""
URDB Tariff Viewer - Deployment Helper Script

This script helps prepare your app for deployment by:
1. Checking all required files exist
2. Validating dependencies
3. Creating deployment-ready files
4. Providing deployment instructions

Usage:
    python deploy.py
"""

import os
import sys
from pathlib import Path


def check_files():
    """Check if all required files exist"""
    required_files = [
        "streamlit_app.py",
        "requirements.txt",
        "data/tariffs/",
        "data/load_profiles/",
        "urdb_viewer/services/calculation_engine.py",
    ]

    optional_files = ["packages.txt", ".streamlit/config.toml", "README.md"]

    print("🔍 Checking required files...")
    missing_required = []
    missing_optional = []

    for file in required_files:
        if not Path(file).exists():
            missing_required.append(file)

    for file in optional_files:
        if not Path(file).exists():
            missing_optional.append(file)

    if missing_required:
        print("❌ Missing required files:")
        for file in missing_required:
            print(f"   - {file}")
        return False

    if missing_optional:
        print("⚠️  Missing optional files (will be created):")
        for file in missing_optional:
            print(f"   - {file}")

    print("✅ All required files present!")
    return True


def validate_app():
    """Basic validation of the app structure"""
    print("\n🔧 Validating app structure...")

    try:
        # Try importing main dependencies
        import numpy
        import pandas
        import plotly
        import streamlit

        print("✅ Python dependencies available")
    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")

    # Check if app can be imported
    try:
        sys.path.append(".")
        # We can't actually run the app here, but we can check syntax
        with open("streamlit_app.py", "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, "streamlit_app.py", "exec")
        print("✅ App syntax is valid")
    except SyntaxError as e:
        print(f"❌ Syntax error in streamlit_app.py: {e}")
        return False
    except UnicodeDecodeError:
        print(
            "⚠️  Could not validate syntax due to encoding issues, but app should still work"
        )
        print("   This is common with special characters in comments or strings")

    return True


def create_deployment_files():
    """Create any missing deployment files"""
    print("\n📝 Creating deployment files...")

    # Create Procfile for Heroku
    if not Path("Procfile").exists():
        with open("Procfile", "w") as f:
            f.write(
                "web: streamlit run streamlit_app.py --server.port $PORT --server.headless true --server.address 0.0.0.0"
            )
        print("✅ Created Procfile")

    # Create .streamlit directory and config if missing
    if not Path(".streamlit").exists():
        Path(".streamlit").mkdir()
        print("✅ Created .streamlit directory")

    if not Path(".streamlit/config.toml").exists():
        config_content = """[server]
headless = true
port = 8501
address = "localhost"
enableCORS = true
enableXsrfProtection = true

[browser]
gatherUsageStats = false
"""
        with open(".streamlit/config.toml", "w") as f:
            f.write(config_content)
        print("✅ Created .streamlit/config.toml")


def show_deployment_options():
    """Show deployment options and instructions"""
    print("\n🚀 Deployment Options:")
    print("=" * 50)

    print("\n1. 🌟 Streamlit Cloud (Recommended - Easiest)")
    print("   • Free tier available")
    print("   • Optimized for Streamlit")
    print("   • Steps:")
    print("     1. Push code to GitHub")
    print("     2. Go to share.streamlit.io")
    print("     3. Connect GitHub & deploy")

    print("\n2. 🟣 Heroku")
    print("   • Free tier available")
    print("   • More customization")
    print("   • Steps:")
    print("     1. Install Heroku CLI")
    print("     2. heroku create your-app-name")
    print("     3. git push heroku main")

    print("\n3. ☁️  AWS/Google Cloud/Azure")
    print("   • Production ready")
    print("   • Scalable")
    print("   • Paid services")

    print("\n📚 See DEPLOYMENT.md for detailed instructions!")


def main():
    """Main deployment preparation function"""
    print("🚀 URDB Tariff Viewer - Deployment Preparer")
    print("=" * 50)

    # Check files
    if not check_files():
        print("\n❌ Please create missing required files before deploying.")
        return False

    # Validate app
    if not validate_app():
        print("\n❌ Please fix validation errors before deploying.")
        return False

    # Create deployment files
    create_deployment_files()

    # Show success message
    print("\n🎉 Your app is ready for deployment!")
    print("📁 Deployment files created:")
    print("   • Procfile (for Heroku)")
    print("   • .streamlit/config.toml (Streamlit config)")

    # Show deployment options
    show_deployment_options()

    print("\n💡 Next steps:")
    print("   1. Choose a deployment platform")
    print("   2. Follow the instructions in DEPLOYMENT.md")
    print("   3. Test your deployed app")
    print("   4. Share the URL with others!")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
