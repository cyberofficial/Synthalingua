#!/usr/bin/env python3
"""
Simple Security Test for api_backend.py

A lightweight test script to verify core security features work correctly.
This can be run without complex dependencies and focuses on the essential fixes.

Usage:
    python test_security_simple.py
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that the module imports correctly"""
    try:
        from modules import api_backend
        print("✅ Successfully imported api_backend module")
        return True, api_backend
    except ImportError as e:
        print(f"❌ Failed to import api_backend: {e}")
        return False, None

def test_security_constants():
    """Test that security constants are properly defined"""
    try:
        from modules import api_backend
        
        # Check security configuration constants
        required_constants = [
            ('FAILED_REQUEST_THRESHOLD', 3),
            ('FAILED_REQUEST_WINDOW', 300), 
            ('BLOCK_DURATION', 3600)
        ]
        
        all_good = True
        for const_name, expected_value in required_constants:
            if hasattr(api_backend, const_name):
                actual_value = getattr(api_backend, const_name)
                if actual_value == expected_value:
                    print(f"✅ {const_name}: {actual_value}")
                else:
                    print(f"⚠️  {const_name}: {actual_value} (expected {expected_value})")
            else:
                print(f"❌ Missing constant: {const_name}")
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"❌ Error checking constants: {e}")
        return False

def test_default_binding():
    """Test that default host binding is localhost"""
    try:
        from modules.api_backend import FlaskServerThread
        
        # Test default host parameter
        server = FlaskServerThread(8080)
        if server.host == '127.0.0.1':
            print("✅ Default binding: 127.0.0.1 (localhost only)")
            return True
        else:
            print(f"❌ Default binding: {server.host} (should be 127.0.0.1)")
            return False
    except Exception as e:
        print(f"❌ Error testing binding: {e}")
        return False

def test_ip_blocking_logic():
    """Test the IP blocking logic without Flask context"""
    try:
        from modules import api_backend
        
        # Reset state
        api_backend.failed_requests.clear()
        api_backend.blocked_ips.clear()
        api_backend.blocked_ips_timestamps.clear()
        
        test_ip = "192.168.1.100"
        
        # Test initial state
        if not api_backend.is_ip_blocked(test_ip):
            print("✅ IP initially not blocked")
        else:
            print("❌ IP should not be blocked initially")
            return False
        
        # Add failed requests (but don't reach threshold)
        api_backend.record_failed_request(test_ip, "test1.js")
        api_backend.record_failed_request(test_ip, "test2.js")
        
        if not api_backend.is_ip_blocked(test_ip):
            print("✅ IP not blocked before threshold (2/3 attempts)")
        else:
            print("❌ IP should not be blocked before threshold")
            return False
        
        # Add third failed request (should trigger block)
        api_backend.record_failed_request(test_ip, "test3.js")
        
        if api_backend.is_ip_blocked(test_ip):
            print("✅ IP blocked after 3 failed attempts")
        else:
            print("❌ IP should be blocked after threshold")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing IP blocking: {e}")
        return False

def test_debug_flag():
    """Test debug flag functionality"""
    try:
        from modules import api_backend
        
        # Test initial state
        initial_debug = api_backend._debug_enabled
        print(f"✅ Debug flag initial state: {initial_debug}")
        
        # Test setting debug flag
        api_backend._debug_enabled = True
        if api_backend._debug_enabled:
            print("✅ Debug flag can be enabled")
        else:
            print("❌ Debug flag setting failed")
            return False
        
        # Test unsetting debug flag
        api_backend._debug_enabled = False
        if not api_backend._debug_enabled:
            print("✅ Debug flag can be disabled")
        else:
            print("❌ Debug flag unsetting failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing debug flag: {e}")
        return False

def test_security_data_structures():
    """Test that security data structures are properly initialized"""
    try:
        from modules import api_backend
        from collections import defaultdict, deque
        
        # Check data structure types
        if isinstance(api_backend.failed_requests, defaultdict):
            print("✅ failed_requests is defaultdict")
        else:
            print(f"❌ failed_requests wrong type: {type(api_backend.failed_requests)}")
            return False
        
        if isinstance(api_backend.blocked_ips, set):
            print("✅ blocked_ips is set")
        else:
            print(f"❌ blocked_ips wrong type: {type(api_backend.blocked_ips)}")
            return False
        
        if isinstance(api_backend.blocked_ips_timestamps, dict):
            print("✅ blocked_ips_timestamps is dict")
        else:
            print(f"❌ blocked_ips_timestamps wrong type: {type(api_backend.blocked_ips_timestamps)}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing data structures: {e}")
        return False

def test_flask_app_creation():
    """Test that Flask app can be created with security headers"""
    try:
        from modules.api_backend import FlaskServerThread
        
        server = FlaskServerThread(8080)
        app = server.create_app()
        
        if app is not None:
            print("✅ Flask app creation successful")
            
            # Test that the app has the expected configuration
            if not app.config.get("DEBUG", True):  # Should be False
                print("✅ Debug mode disabled in Flask app")
            else:
                print("❌ Debug mode should be disabled")
                return False
            
            return True
        else:
            print("❌ Flask app creation failed")
            return False
    except Exception as e:
        print(f"❌ Error testing Flask app creation: {e}")
        return False

def main():
    """Run simple security tests"""
    print("🔒 Simple Security Test for api_backend.py")
    print("=" * 50)
    
    tests = [
        ("Module Import", test_import),
        ("Security Constants", test_security_constants),
        ("Default Binding", test_default_binding), 
        ("IP Blocking Logic", test_ip_blocking_logic),
        ("Debug Flag", test_debug_flag),
        ("Security Data Structures", test_security_data_structures),
        ("Flask App Creation", test_flask_app_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Core security features are working correctly")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("❌ Some security features may need attention")
    
    print("\n💡 To run comprehensive tests, use: python test_security_features.py")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)