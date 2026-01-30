#!/usr/bin/env python3
"""
Test script to verify the metrics dashboard functionality.
"""
import requests
import time
import uuid
import json

BASE_URL = "http://localhost:8082"

def test_metrics_api():
    """Test the metrics API endpoints."""
    
    print("Testing Metrics Dashboard API...\n")
    
    # Test summary endpoint
    print("1. Testing /metrics/api/summary...")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/summary")
        summary = response.json()
        print(f"   ✓ Summary: {summary}\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    # Test users endpoint
    print("2. Testing /metrics/api/users...")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/users")
        users = response.json()
        print(f"   ✓ Users: {len(users)} users found\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    # Test turns endpoint
    print("3. Testing /metrics/api/turns...")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/turns")
        turns = response.json()
        print(f"   ✓ Turns: {len(turns)} turns found\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    # Test sessions endpoint
    print("4. Testing /metrics/api/sessions...")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/sessions")
        sessions = response.json()
        print(f"   ✓ Sessions: {len(sessions)} sessions found\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    # Test dashboard HTML endpoint
    print("5. Testing /metrics dashboard page...")
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        if response.status_code == 200 and "Claude Code Metrics Dashboard" in response.text:
            print(f"   ✓ Dashboard HTML loaded successfully\n")
        else:
            print(f"   ✗ Dashboard HTML not found\n")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return False
    
    print("✓ All metrics API tests passed!")
    return True

def simulate_api_request():
    """Simulate a sample API request to generate metrics."""
    print("\nSimulating API requests to generate metrics...\n")
    
    headers = {
        "X-User-ID": f"user-{uuid.uuid4().hex[:8]}",
        "X-Session-ID": str(uuid.uuid4()),
    }
    
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Say hello!"
            }
        ]
    }
    
    print("Sending API request...")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=payload,
            headers=headers,
            timeout=30
        )
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Request completed successfully\n")
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}\n")
            print(f"Response: {response.text}\n")
            return False
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Metrics Dashboard Test Suite")
    print("=" * 60 + "\n")
    
    # Try to simulate a request first
    simulate_api_request()
    
    # Wait a moment for metrics to be recorded
    time.sleep(1)
    
    # Test the metrics API
    success = test_metrics_api()
    
    print("=" * 60)
    if success:
        print("✓ All tests completed successfully!")
        print(f"Dashboard available at: {BASE_URL}/metrics")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
