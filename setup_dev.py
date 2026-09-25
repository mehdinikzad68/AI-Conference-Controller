"""
Development Environment Setup Script

Automatically checks and installs missing dependencies, sets up testing environment.
"""

import subprocess
import sys
from pathlib import Path
import importlib.util


def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None


def install_package(package: str) -> bool:
    """Install a package using pip."""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False


def check_and_install_dependencies():
    """Check and install missing dependencies."""
    print("=" * 70)
    print("🔍 Checking Dependencies...")
    print("=" * 70)
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    # Read requirements
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before >= or other operators)
                pkg = line.split('>=')[0].split('==')[0].split('<')[0].strip()
                # Handle conditional requirements
                if ';' in pkg:
                    pkg = pkg.split(';')[0].strip()
                requirements.append((pkg, line))
    
    missing = []
    installed = []
    
    for pkg_name, full_req in requirements:
        # Map package names to import names
        import_name = pkg_name.replace('-', '_').lower()
        
        # Special cases
        import_map = {
            'opencv-python': 'cv2',
            'opencv-python-headless': 'cv2',
            'pyqt6': 'PyQt6',
            'pymupdf': 'fitz',
            'pillow': 'PIL',
            'speechrecognition': 'speech_recognition'
        }
        
        if pkg_name.lower() in import_map:
            import_name = import_map[pkg_name.lower()]
        
        if check_package_installed(import_name):
            installed.append(pkg_name)
            print(f"✅ {pkg_name}")
        else:
            missing.append(full_req)
            print(f"❌ {pkg_name} - MISSING")
    
    print(f"\n📊 Summary: {len(installed)} installed, {len(missing)} missing")
    
    if missing:
        print("\n🔧 Installing missing packages...")
        for req in missing:
            install_package(req)
    
    return len(missing) == 0


def setup_test_environment():
    """Setup testing environment."""
    print("\n" + "=" * 70)
    print("🧪 Setting Up Test Environment...")
    print("=" * 70)
    
    # Install testing packages
    test_packages = [
        "pytest>=7.0.0",
        "pytest-qt>=4.2.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "coverage>=7.0.0"
    ]
    
    for package in test_packages:
        pkg_name = package.split('>=')[0]
        import_name = pkg_name.replace('-', '_')
        
        if not check_package_installed(import_name):
            print(f"Installing {pkg_name}...")
            install_package(package)
        else:
            print(f"✅ {pkg_name} already installed")
    
    print("\n✅ Test environment ready!")


def main():
    """Main setup function."""
    print("\n" + "=" * 70)
    print("🚀 AI-Symp-Controller Development Environment Setup")
    print("=" * 70 + "\n")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("⚠️  Warning: Python 3.11+ recommended")
        print(f"   Current version: {sys.version}")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check and install dependencies
    deps_ok = check_and_install_dependencies()
    
    # Setup test environment
    setup_test_environment()
    
    print("\n" + "=" * 70)
    if deps_ok:
        print("✅ Setup Complete! All dependencies installed.")
    else:
        print("⚠️  Setup complete with some missing dependencies.")
        print("   Some features may not work correctly.")
    print("=" * 70)
    
    print("\n📝 Next Steps:")
    print("   1. Run tests: python tests/run_tests.py")
    print("   2. Run application: python main.py")
    print("   3. View coverage: python tests/run_tests.py --coverage")
    
    return 0 if deps_ok else 1


if __name__ == "__main__":
    sys.exit(main())

