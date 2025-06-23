#!/usr/bin/env python3
"""
Simple test script to verify the Lambda function works locally.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Health Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError as e:
        print(f"Health check failed - Connection error: {e}")
        print("This suggests the container might not be running or may have crashed during startup.")
        return False
    except requests.exceptions.Timeout as e:
        print(f"Health check failed - Timeout: {e}")
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint."""
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False

def test_convert_endpoint():
    """Test the convert endpoint with a sample request."""
    print("\nTesting convert endpoint...")
    try:
        # This will fail because we don't have S3 access, but it should show the service is working
        test_payload = {
            "source": "s3://test-bucket/test-file.pdf"
        }
        response = requests.post(f"{BASE_URL}/convert", json=test_payload)
        print(f"Convert Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        # We expect this to fail with 400 or 500, but not crash
        return response.status_code in [400, 500]
    except Exception as e:
        print(f"Convert endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing MarkItDown Lambda locally...")
    print("Make sure to run 'docker build -t markitdown-lambda .' first")
    print("Then run 'docker run -p 8080:8080 markitdown-lambda' in another terminal")
    print("\nWaiting for you to start the container...")
    input("Press Enter when container is running...")
    
    # Give the container a moment to fully start
    print("\nWaiting 5 seconds for container to fully initialize...")
    time.sleep(5)
    
    health_ok = test_health_check()
    root_ok = test_root_endpoint() if health_ok else False
    convert_ok = test_convert_endpoint() if root_ok else False
    
    print(f"\n--- Test Results ---")
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Root Endpoint: {'✅ PASS' if root_ok else '❌ FAIL'}")
    print(f"Convert Endpoint: {'✅ PASS' if convert_ok else '❌ FAIL'}")
    
    if all([health_ok, root_ok, convert_ok]):
        print("\n🎉 All tests passed! The service should work in Lambda.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")
