import sys
import site
import os

print(f"Executable: {sys.executable}")
print(f"Prefix: {sys.prefix}")
print(f"Base Prefix: {getattr(sys, 'base_prefix', 'N/A')}")
print(f"User Site: {site.getusersitepackages()}")
print(f"Global Site: {site.getsitepackages()}")
print("\nSys Path:")
for p in sys.path:
    print(f"  {p}")

try:
    import transformers
    print(f"\nTransformers found at: {transformers.__file__}")
except ImportError as e:
    print(f"\nTransformers NOT found: {e}")

try:
    import pydantic_settings
    print(f"Pydantic Settings found: {pydantic_settings.__file__}")
except ImportError:
    print("Pydantic Settings NOT found")
