"""Test DeepFace import"""
import sys

print("Testing DeepFace import...")
print("=" * 50)

try:
    print("1. Testing TensorFlow...")
    import tensorflow as tf
    print(f"   [OK] TensorFlow {tf.__version__} imported successfully")
except Exception as e:
    print(f"   [ERROR] TensorFlow import failed: {e}")
    sys.exit(1)

try:
    print("2. Testing DeepFace...")
    from deepface import DeepFace
    print("   [OK] DeepFace imported successfully")
except Exception as e:
    print(f"   [ERROR] DeepFace import failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Testing FER...")
    try:
        from fer import FER
    except ImportError:
        from fer.fer import FER
    print("   [OK] FER imported successfully")
except Exception as e:
    print(f"   [WARNING] FER import failed: {e}")
    print("   (FER is optional)")

print("=" * 50)
print("[SUCCESS] All critical imports successful!")

