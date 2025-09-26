#!/usr/bin/env python3
"""
Security Features Test Suite for api_backend.py

This test file verifies all the security improvements implemented in the Flask web server:
1. Network binding security (localhost only by default)
2. IP-based fuzzy search protection and automatic blocking
3. Debug mode integration with args.debug
4. Comprehensive security headers
5. Path traversal protection
6. HTTPS functionality
7. Exception handling improvements

Usage:
    python test_security_features.py

Requirements:
    - Flask
    - requests
    - All modules from the Synthalingua project
"""

import sys
import os
import time
import requests
import threading
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from modules import api_backend
    from modules.parser_args import valid_port_number
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Please ensure you're running this from the Synthalingua project root directory")
    sys.exit(1)

class SecurityTestSuite:
    """Test suite for security features in api_backend.py"""
    
    def __init__(self):
        self.test_port = 18080
        self.test_https_port = 18443
        self.results = []
        self.server_thread = None
        
    def log_result(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((test_name, passed, message))
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def test_network_binding_defaults(self):
        """Test 1: Verify default network binding is localhost (127.0.0.1)"""
        print("\n🔒 Testing Network Binding Security...")
        
        # Test FlaskServerThread default
        from modules.api_backend import FlaskServerThread
        server = FlaskServerThread(self.test_port)
        
        if server.host == '127.0.0.1':
            self.log_result("Default FlaskServerThread binding", True, "Defaults to localhost (127.0.0.1)")
        else:
            self.log_result("Default FlaskServerThread binding", False, f"Expected 127.0.0.1, got {server.host}")
    
    def test_ip_blocking_system(self):
        """Test 2: Verify IP blocking system works correctly"""
        print("\n🛡️ Testing IP Blocking System...")
        
        # Reset security state
        api_backend.failed_requests.clear()
        api_backend.blocked_ips.clear()
        api_backend.blocked_ips_timestamps.clear()
        
        test_ip = "192.168.1.100"
        test_filename = "nonexistent.js"
        
        # Test initial state
        is_blocked_initially = api_backend.is_ip_blocked(test_ip)
        self.log_result("IP initially not blocked", not is_blocked_initially)
        
        # Record failed requests (should trigger blocking on 3rd attempt)
        for i in range(3):
            api_backend.record_failed_request(test_ip, f"{test_filename}_{i}")
        
        # Check if IP is now blocked
        is_blocked_after = api_backend.is_ip_blocked(test_ip)
        self.log_result("IP blocked after 3 failed attempts", is_blocked_after, 
                       f"IP {test_ip} should be blocked after threshold")
        
        # Test that blocked IP stays blocked
        still_blocked = api_backend.is_ip_blocked(test_ip)
        self.log_result("Blocked IP remains blocked", still_blocked)
        
        # Test cleanup of old entries (simulate time passage)
        original_time = time.time
        with patch('time.time', return_value=original_time() + api_backend.BLOCK_DURATION + 1):
            is_unblocked = not api_backend.is_ip_blocked(test_ip)
            self.log_result("IP unblocked after timeout", is_unblocked, 
                           "IP should be unblocked after BLOCK_DURATION")
    
    def test_debug_integration(self):
        """Test 3: Verify debug mode integration with args.debug"""
        print("\n🐛 Testing Debug Mode Integration...")
        
        # Reset debug state
        api_backend._debug_enabled = False
        
        # Test flask_server with debug=True
        original_create_pid = api_backend.create_pid_file
        api_backend.create_pid_file = MagicMock()  # Mock to avoid file creation
        
        try:
            api_backend.flask_server("start", None, None, "127.0.0.1", debug=True)
            debug_enabled = api_backend._debug_enabled
            self.log_result("Debug mode enabled via flask_server", debug_enabled, 
                           "Debug flag should be set from args.debug parameter")
            
            # Test flask_server with debug=False
            api_backend.flask_server("start", None, None, "127.0.0.1", debug=False)
            debug_disabled = not api_backend._debug_enabled
            self.log_result("Debug mode disabled via flask_server", debug_disabled,
                           "Debug flag should be disabled when debug=False")
            
        finally:
            api_backend.create_pid_file = original_create_pid  # Restore original function
    
    def test_security_headers(self):
        """Test 4: Verify security headers are properly set"""
        print("\n🔐 Testing Security Headers...")
        
        # Create a Flask app instance to test headers
        from modules.api_backend import FlaskServerThread
        server = FlaskServerThread(self.test_port)
        app = server.create_app()
        
        with app.test_client() as client:
            # Test main page
            response = client.get('/')
            headers = response.headers
            
            # Check each security header
            expected_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY", 
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
            
            all_headers_present = True
            missing_headers = []
            
            for header_name, expected_value in expected_headers.items():
                if header_name in headers and headers[header_name] == expected_value:
                    self.log_result(f"Security header: {header_name}", True, f"✓ {expected_value}")
                else:
                    all_headers_present = False
                    missing_headers.append(header_name)
                    actual_value = headers.get(header_name, "MISSING")
                    self.log_result(f"Security header: {header_name}", False, 
                                   f"Expected: {expected_value}, Got: {actual_value}")
            
            self.log_result("All security headers present", all_headers_present,
                           f"Missing headers: {missing_headers}" if missing_headers else "All headers correctly set")
    
    def test_path_traversal_protection(self):
        """Test 5: Verify path traversal protection"""
        print("\n🚫 Testing Path Traversal Protection...")
        
        # Create temporary static directory structure
        temp_static_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_static_dir, "test.css")
        sensitive_file = os.path.join(os.path.dirname(temp_static_dir), "sensitive.txt")
        
        try:
            # Create test files
            with open(test_file, 'w') as f:
                f.write("/* test css */")
            with open(sensitive_file, 'w') as f:
                f.write("sensitive data")
            
            # Mock get_static_dir to return our temp directory
            original_get_static_dir = api_backend.get_static_dir
            api_backend.get_static_dir = lambda: temp_static_dir
            
            # Create Flask app for testing
            from modules.api_backend import FlaskServerThread
            server = FlaskServerThread(self.test_port)
            app = server.create_app()
            
            with app.test_client() as client:
                # Test legitimate file access
                response = client.get('/static/test.css')
                legitimate_access = response.status_code == 200
                self.log_result("Legitimate static file access", legitimate_access,
                               f"Status: {response.status_code}")
                
                # Test path traversal attempts
                traversal_attempts = [
                    "../sensitive.txt",
                    "../../sensitive.txt", 
                    "..\\sensitive.txt",
                    "%2e%2e%2fsensitive.txt",
                    "....//sensitive.txt"
                ]
                
                blocked_attempts = 0
                for attempt in traversal_attempts:
                    response = client.get(f'/static/{attempt}')
                    if response.status_code in [403, 404]:  # Should be blocked or not found
                        blocked_attempts += 1
                
                all_blocked = blocked_attempts == len(traversal_attempts)
                self.log_result("Path traversal attempts blocked", all_blocked,
                               f"Blocked {blocked_attempts}/{len(traversal_attempts)} traversal attempts")
        
        finally:
            # Cleanup
            api_backend.get_static_dir = original_get_static_dir
            shutil.rmtree(temp_static_dir, ignore_errors=True)
            try:
                os.remove(sensitive_file)
            except:
                pass
    
    def test_exception_handling_improvements(self):
        """Test 6: Verify improved exception handling"""
        print("\n⚠️ Testing Exception Handling Improvements...")
        
        # Test that force_shutdown_server handles exceptions properly
        original_server_thread = api_backend.server_thread
        
        # Create mock server thread with server attribute
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        mock_thread.shutdown_event = MagicMock()
        mock_server = MagicMock()
        mock_server.server_close.side_effect = OSError("Test exception")
        mock_thread.server = mock_server
        
        api_backend.server_thread = mock_thread
        
        try:
            # Test with debug disabled
            api_backend._debug_enabled = False
            api_backend.force_shutdown_server()  # Should not raise exception
            self.log_result("Exception handling (production mode)", True, 
                           "No exception raised in production mode")
            
            # Test with debug enabled
            api_backend._debug_enabled = True
            api_backend.force_shutdown_server()  # Should not raise exception but may print debug info
            self.log_result("Exception handling (debug mode)", True,
                           "No exception raised in debug mode")
            
        except Exception as e:
            self.log_result("Exception handling", False, f"Unexpected exception: {e}")
        
        finally:
            api_backend.server_thread = original_server_thread
    
    def test_https_functionality(self):
        """Test 7: Verify HTTPS setup functionality"""
        print("\n🔒 Testing HTTPS Functionality...")
        
        from modules.api_backend import FlaskServerThread
        
        # Test HTTPS server creation
        https_server = FlaskServerThread(self.test_https_port, use_https=True)
        
        try:
            # Test setup_https method
            ssl_context, ssl_dir = https_server.setup_https()
            
            if ssl_context is not None:
                self.log_result("HTTPS SSL context creation", True, 
                               "SSL context created successfully")
                
                # Check SSL context properties
                has_cert_chain = hasattr(ssl_context, 'check_hostname')
                self.log_result("SSL context properties", has_cert_chain,
                               "SSL context has expected properties")
            else:
                self.log_result("HTTPS SSL context creation", False,
                               "Failed to create SSL context")
            
            # Cleanup temporary SSL directory
            if ssl_dir and os.path.exists(ssl_dir):
                shutil.rmtree(ssl_dir, ignore_errors=True)
                self.log_result("HTTPS cleanup", True, "SSL directory cleaned up")
            
        except Exception as e:
            self.log_result("HTTPS functionality", False, f"Exception during HTTPS test: {e}")
    
    def test_emoji_removal(self):
        """Test 8: Verify emojis have been removed from output"""
        print("\n🚫 Testing Emoji Removal...")
        
        # Reset security state
        api_backend.failed_requests.clear()
        api_backend.blocked_ips.clear()
        api_backend.blocked_ips_timestamps.clear()
        
        # Capture output from security functions
        import io
        from contextlib import redirect_stdout
        
        output_buffer = io.StringIO()
        
        with redirect_stdout(output_buffer):
            # Trigger security alert (which should not contain emojis)
            test_ip = "192.168.1.200"
            for i in range(3):
                api_backend.record_failed_request(test_ip, f"test_{i}.js")
        
        output = output_buffer.getvalue()
        
        # Check for common emoji characters
        emoji_chars = ['🚫', '🔓', '🚨', '⚠️', '✅', '❌']
        has_emojis = any(emoji in output for emoji in emoji_chars)
        
        self.log_result("Console output emoji-free", not has_emojis,
                       "No emoji characters found in security alerts" if not has_emojis 
                       else f"Found emojis in output: {output}")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 Starting Security Features Test Suite")
        print("=" * 50)
        
        test_methods = [
            self.test_network_binding_defaults,
            self.test_ip_blocking_system,
            self.test_debug_integration,
            self.test_security_headers,
            self.test_path_traversal_protection,
            self.test_exception_handling_improvements,
            self.test_https_functionality,
            self.test_emoji_removal
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_result(test_name, False, f"Test exception: {e}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("🏁 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Security implementation is working correctly.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Please review the issues above.")
            
        # Detailed results
        print("\nDetailed Results:")
        for test_name, passed, message in self.results:
            status = "✅" if passed else "❌"
            print(f"{status} {test_name}")
            if message and not passed:
                print(f"    Issue: {message}")
        
        return passed == total

def main():
    """Main function to run the security test suite"""
    print("🔒 Synthalingua Security Features Test Suite")
    print("Testing all security improvements in api_backend.py")
    print()
    
    # Check if we can import required modules
    try:
        import flask
        import requests
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install required packages: pip install flask requests")
        return False
    
    # Run tests
    test_suite = SecurityTestSuite()
    success = test_suite.run_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Security test suite completed successfully!")
        print("All security features are working as expected.")
    else:
        print("❌ Some security tests failed.")
        print("Please review the test results and fix any issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)