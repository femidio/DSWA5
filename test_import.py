# test_import.py
try:
    from app import create_app
    print("create_app imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
