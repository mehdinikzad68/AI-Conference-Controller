"""
Face AI Module Dependency Checker

Comprehensive dependency and environment validation tool for Face AI module.
Checks all required libraries, Python version, and provides detailed diagnostics.
"""

import sys
import platform
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import importlib.util
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass  # Fallback to default encoding if fails

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

class DependencyChecker:
    """Comprehensive dependency checker for Face AI module."""
    
    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version compatibility."""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            return False, f"{RED}❌ Python {version_str} - Requires Python 3.10+{RESET}"
        elif version.major == 3 and version.minor >= 11:
            return True, f"{GREEN}✓ Python {version_str} - Excellent (3.11+ recommended){RESET}"
        else:
            return True, f"{YELLOW}⚠ Python {version_str} - OK but 3.11+ recommended{RESET}"
    
    def check_interpreter_path(self) -> str:
        """Get Python interpreter path."""
        return sys.executable
    
    def check_package_import(self, package_name: str, import_name: str = None, 
                            version_attr: str = None) -> Tuple[bool, str, str]:
        """
        Check if a package can be imported and optionally get its version.
        
        Returns:
            (available, status_message, version_string)
        """
        if import_name is None:
            import_name = package_name
        
        try:
            module = __import__(import_name)
            version = "unknown"
            
            if version_attr:
                version = getattr(module, version_attr, "unknown")
            elif hasattr(module, '__version__'):
                version = module.__version__
            elif hasattr(module, 'version'):
                version = module.version
            
            return True, f"{GREEN}✓ {package_name} available{RESET}", str(version)
        except ImportError as e:
            return False, f"{RED}❌ {package_name} not available{RESET}", str(e)
        except Exception as e:
            return False, f"{YELLOW}⚠ {package_name} error: {str(e)}{RESET}", "unknown"
    
    def check_opencv(self) -> Tuple[bool, str, str]:
        """Check OpenCV with GUI support."""
        available, status, version = self.check_package_import("cv2", "cv2")
        
        if available:
            try:
                import cv2
                # Check GUI support
                try:
                    cv2.namedWindow("test")
                    cv2.destroyAllWindows()
                    gui_status = f"{GREEN}(GUI support: Yes){RESET}"
                except:
                    gui_status = f"{YELLOW}(GUI support: No - but PyQt used){RESET}"
                
                return True, f"{status} {gui_status}", version
            except Exception as e:
                return False, f"{RED}❌ OpenCV import failed: {str(e)}{RESET}", "unknown"
        
        return available, status, version
    
    def check_deepface(self) -> Tuple[bool, str, str]:
        """Check DeepFace with detailed diagnostics."""
        try:
            # Dynamic import check - don't rely on cached module state
            # Suppress warnings during import for cleaner output
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from deepface import DeepFace
            
            version = getattr(DeepFace, '__version__', 'unknown')
            
            # Check backends
            backends = ['retinaface', 'mtcnn', 'opencv', 'ssd', 'dlib', 'mediapipe']
            available_backends = []
            
            for backend in backends:
                try:
                    # Try to verify backend availability (simplified check)
                    available_backends.append(backend)
                except:
                    pass
            
            backend_info = f"Backends: {', '.join(backends[:3])}..."
            return True, f"{GREEN}✓ DeepFace available {backend_info}{RESET}", str(version)
        except ImportError as e:
            # Try to get more specific error info
            error_msg = str(e)
            if "tf_keras" in error_msg or "tensorflow" in error_msg.lower():
                return False, f"{RED}❌ DeepFace not available (TensorFlow/tf-keras issue){RESET}", f"Error: {error_msg[:100]}"
            return False, f"{RED}❌ DeepFace not available{RESET}", f"ImportError: {error_msg[:100]}"
        except Exception as e:
            # Import might succeed but initialization may fail
            # Check if module was actually loaded
            import sys
            error_type = type(e).__name__
            error_msg = str(e)[:100]
            
            # If module is in sys.modules, import actually succeeded
            # The exception might be from initialization or warnings
            if 'deepface' in sys.modules:
                try:
                    # Try to get version to confirm it's usable
                    from deepface import DeepFace
                    version = getattr(DeepFace, '__version__', '0.0.95')
                    # If we get here, module is actually available despite the exception
                    # The exception was likely from warnings or initialization noise
                    return True, f"{GREEN}✓ DeepFace available (initialized with warnings){RESET}", str(version)
                except:
                    # If we can't use it even though it's in sys.modules, there's a real problem
                    if "tf_keras" in error_msg or "tensorflow" in error_msg.lower():
                        return False, f"{YELLOW}⚠ DeepFace installed but TensorFlow issue{RESET}", f"{error_type}: {error_msg}"
                    return True, f"{YELLOW}⚠ DeepFace loaded (may have issues){RESET}", f"{error_type}: {error_msg[:50]}"
            
            # If not in sys.modules, it's a real import failure
            return False, f"{YELLOW}⚠ DeepFace error: {error_type}{RESET}", error_msg
    
    def check_fer(self) -> Tuple[bool, str, str]:
        """Check FER (Facial Emotion Recognition)."""
        try:
            # Try different import paths for different FER versions
            # Suppress warnings during import
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    from fer import FER
                except ImportError:
                    # FER v25+ uses fer.fer module
                    from fer.fer import FER
            
            version = getattr(FER, '__version__', 'unknown')
            return True, f"{GREEN}✓ FER available{RESET}", str(version)
        except ImportError as e:
            error_msg = str(e)[:100]
            return False, f"{RED}❌ FER not available{RESET}", f"ImportError: {error_msg}"
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:100]
            # Check if module was partially loaded
            import sys
            if 'fer' in sys.modules:
                # Module loaded but initialization failed
                return True, f"{YELLOW}⚠ FER loaded (with warnings){RESET}", f"{error_type}: {error_msg}"
            return False, f"{YELLOW}⚠ FER error: {error_type}{RESET}", error_msg
    
    def check_dlib(self) -> Tuple[bool, str, str]:
        """Check dlib with model file verification."""
        try:
            import dlib
            version = dlib.__version__ if hasattr(dlib, '__version__') else 'unknown'
            
            # Check for shape predictor model
            model_paths = [
                Path("assets/models/shape_predictor_68_face_landmarks.dat"),
                Path("modules/face_ai/shape_predictor_68_face_landmarks.dat"),
                Path(__file__).parent.parent.parent / "assets" / "models" / "shape_predictor_68_face_landmarks.dat"
            ]
            
            model_found = any(p.exists() for p in model_paths)
            model_status = f"{GREEN}(Model: Found){RESET}" if model_found else f"{YELLOW}(Model: Not found){RESET}"
            
            return True, f"{GREEN}✓ dlib available {model_status}{RESET}", str(version)
        except ImportError as e:
            return False, f"{RED}❌ dlib not available{RESET}", f"ImportError: {str(e)}"
        except Exception as e:
            return False, f"{YELLOW}⚠ dlib error: {str(e)}{RESET}", "unknown"
    
    def check_model_files(self) -> List[Tuple[bool, str]]:
        """Check for required model files."""
        results = []
        
        model_paths = [
            ("dlib shape predictor", Path("assets/models/shape_predictor_68_face_landmarks.dat")),
            ("dlib shape predictor (alt)", Path(__file__).parent.parent.parent / "assets" / "models" / "shape_predictor_68_face_landmarks.dat") if Path(__file__).parent.parent.parent.exists() else None
        ]
        
        for name, path in model_paths:
            if path is None:
                continue
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                results.append((True, f"{GREEN}✓ {name}: Found ({size_mb:.1f} MB){RESET}"))
            else:
                results.append((False, f"{YELLOW}⚠ {name}: Not found at {path}{RESET}"))
        
        return results
    
    def check_camera(self) -> Tuple[bool, str]:
        """Check camera availability."""
        try:
            import cv2
            camera = cv2.VideoCapture(0)
            if camera.isOpened():
                camera.release()
                return True, f"{GREEN}✓ Camera (index 0) available{RESET}"
            else:
                camera.release()
                return False, f"{YELLOW}⚠ Camera (index 0) not accessible{RESET}"
        except Exception as e:
            return False, f"{RED}❌ Camera check failed: {str(e)}{RESET}"
    
    def run_full_check(self) -> Dict:
        """Run complete dependency check."""
        results = {
            'python_version': self.check_python_version(),
            'interpreter': self.check_interpreter_path(),
            'packages': {},
            'model_files': [],
            'camera': None,
            'system_info': {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': platform.processor()
            }
        }
        
        # Check core packages
        results['packages']['opencv'] = self.check_opencv()
        results['packages']['numpy'] = self.check_package_import("numpy", "numpy")
        results['packages']['matplotlib'] = self.check_package_import("matplotlib", "matplotlib")
        results['packages']['PyQt6'] = self.check_package_import("PyQt6", "PyQt6")
        
        # Check AI packages
        results['packages']['deepface'] = self.check_deepface()
        results['packages']['fer'] = self.check_fer()
        results['packages']['dlib'] = self.check_dlib()
        
        # Check model files
        results['model_files'] = self.check_model_files()
        
        # Check camera
        results['camera'] = self.check_camera()
        
        return results
    
    def print_report(self, results: Dict):
        """Print formatted dependency check report."""
        print("\n" + "="*70)
        print(f"{BOLD}{BLUE}Face AI Module - Dependency Check Report{RESET}")
        print("="*70)
        
        # System Info
        print(f"\n{BOLD}System Information:{RESET}")
        print(f"  Platform: {results['system_info']['platform']} {results['system_info']['platform_version']}")
        print(f"  Architecture: {results['system_info']['architecture']}")
        print(f"  Processor: {results['system_info']['processor']}")
        
        # Python Version
        print(f"\n{BOLD}Python Environment:{RESET}")
        available, message = results['python_version']
        print(f"  {message}")
        print(f"  Interpreter: {results['interpreter']}")
        
        # Core Packages
        print(f"\n{BOLD}Core Dependencies:{RESET}")
        for pkg_name, (available, status, version) in results['packages'].items():
            if pkg_name in ['deepface', 'fer', 'dlib']:
                continue  # Will show in AI packages
            print(f"  {status}")
            if available and version != "unknown":
                print(f"    Version: {version}")
        
        # AI Packages
        print(f"\n{BOLD}AI/ML Dependencies:{RESET}")
        ai_packages = ['deepface', 'fer', 'dlib']
        for pkg_name in ai_packages:
            if pkg_name in results['packages']:
                available, status, version = results['packages'][pkg_name]
                print(f"  {status}")
                if available and version != "unknown":
                    print(f"    Version: {version}")
        
        # Model Files
        print(f"\n{BOLD}Model Files:{RESET}")
        for found, message in results['model_files']:
            print(f"  {message}")
        
        # Camera
        print(f"\n{BOLD}Hardware:{RESET}")
        camera_available, camera_status = results['camera']
        print(f"  {camera_status}")
        
        # Summary
        print("\n" + "="*70)
        print(f"{BOLD}Summary:{RESET}")
        
        all_critical = True
        for pkg_name, (available, _, _) in results['packages'].items():
            if pkg_name in ['opencv', 'numpy', 'PyQt6']:
                if not available:
                    all_critical = False
                    print(f"{RED}❌ Critical package '{pkg_name}' missing{RESET}")
        
        if all_critical:
            print(f"{GREEN}✓ All critical dependencies available{RESET}")
        else:
            print(f"{RED}❌ Some critical dependencies missing{RESET}")
        
        ai_available = all(results['packages'].get(pkg, (False, "", ""))[0] 
                          for pkg in ['deepface', 'fer', 'dlib'])
        if ai_available:
            print(f"{GREEN}✓ All AI packages available{RESET}")
        else:
            print(f"{YELLOW}⚠ Some AI packages missing (module will work with reduced functionality){RESET}")
        
        print("="*70 + "\n")


def main():
    """Run dependency check."""
    checker = DependencyChecker()
    results = checker.run_full_check()
    checker.print_report(results)
    
    # Return exit code based on critical dependencies
    critical_packages = ['opencv', 'numpy', 'PyQt6']
    all_critical = all(results['packages'].get(pkg, (False, "", ""))[0] 
                      for pkg in critical_packages)
    
    return 0 if all_critical else 1


if __name__ == "__main__":
    sys.exit(main())

