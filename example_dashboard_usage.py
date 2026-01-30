#!/usr/bin/env python3
"""
Example: Using the Claude Code Proxy with Metrics Dashboard

This example demonstrates how to:
1. Send API requests with user and session tracking
2. Access the metrics dashboard
3. Query metrics via API endpoints
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8082"
DASHBOARD_URL = f"{BASE_URL}/metrics"

def example_basic_request():
    """Example 1: Basic API request with metrics"""
    print("\n" + "="*60)
    print("Example 1: Basic API Request with Metrics")
    print("="*60)
    
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    
    print(f"\nUser ID: {user_id}")
    print(f"Session ID: {session_id}")
    
    headers = {
        "X-User-ID": user_id,
        "X-Session-ID": session_id,
    }
    
    payload = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Say hello to the metrics dashboard!"
            }
        ]
    }
    
    print("\nSending request...")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/messages",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✓ Request successful")
            result = response.json()
            print(f"\nResponse summary:")
            print(f"  - Model: {result.get('model')}")
            print(f"  - Stop reason: {result.get('stop_reason')}")
            print(f"  - Content: {result.get('content', [{}])[0].get('text', '')[:50]}...")
            
            return user_id, session_id
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None


def example_query_metrics():
    """Example 2: Query metrics via API"""
    print("\n" + "="*60)
    print("Example 2: Query Metrics via API")
    print("="*60)
    
    # Get summary
    print("\n1. Summary Metrics:")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/summary")
        metrics = response.json()
        
        print(f"   - Total Requests: {metrics['total_requests']}")
        print(f"   - Total Tool Calls: {metrics['total_tool_calls']}")
        print(f"   - Active Users: {metrics['active_users']}")
        print(f"   - Input Tokens: {metrics['total_input_tokens']}")
        print(f"   - Output Tokens: {metrics['total_output_tokens']}")
        print(f"   - Tool Distribution: {metrics['tool_calls_by_name']}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Get users
    print("\n2. User Metrics:")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/users")
        users = response.json()
        
        if users:
            for user in users[:3]:  # Show first 3 users
                print(f"   - {user['user_id'][:20]}")
                print(f"     Requests: {user['total_requests']}")
                print(f"     Tool Calls: {user['total_tool_calls']}")
                print(f"     Last Seen: {user['last_seen']}")
        else:
            print("   No user data yet")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Get recent turns
    print("\n3. Recent Messages:")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/turns?limit=5")
        turns = response.json()
        
        if turns:
            for turn in turns[:3]:  # Show first 3
                print(f"   - Turn ID: {turn['turn_id'][:16]}")
                print(f"     User: {turn['user_id'][:20]}")
                print(f"     Model: {turn['model']}")
                print(f"     Latency: {turn['latency_ms']}ms")
                print(f"     Tokens: {turn['prompt_tokens']} in, {turn['completion_tokens']} out")
        else:
            print("   No messages yet")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Get sessions
    print("\n4. Active Sessions:")
    try:
        response = requests.get(f"{BASE_URL}/metrics/api/sessions?limit=5")
        sessions = response.json()
        
        if sessions:
            for session in sessions[:3]:  # Show first 3
                print(f"   - Session: {session['session_id'][:16]}")
                print(f"     User: {session['user_id'][:20]}")
                print(f"     Turns: {session['turn_count']}")
                print(f"     Tool Calls: {session['total_tool_calls']}")
                print(f"     Avg TC/Turn: {session['avg_tool_calls_per_turn']}")
        else:
            print("   No sessions yet")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_dashboard_access():
    """Example 3: Access the dashboard"""
    print("\n" + "="*60)
    print("Example 3: Dashboard Access")
    print("="*60)
    
    print(f"\nDashboard URL: {DASHBOARD_URL}")
    print("\nDashboard Features:")
    print("  - Real-time metrics summary")
    print("  - Messages tab: View all message exchanges")
    print("  - Sessions tab: View active sessions")
    print("  - Users tab: View user metrics")
    print("  - Tools tab: View tool distribution charts")
    print("\nInteractive Features:")
    print("  - Click on message rows to expand tool calls")
    print("  - Hover over message previews to see full content")
    print("  - Click on sessions to view messages in that session")
    print("  - Auto-refresh every 10 seconds")


def example_batch_requests(user_id: str, session_id: str):
    """Example 4: Send multiple requests from same user/session"""
    print("\n" + "="*60)
    print("Example 4: Batch Requests (Same User/Session)")
    print("="*60)
    
    headers = {
        "X-User-ID": user_id,
        "X-Session-ID": session_id,
    }
    
    messages = [
        "What is Python?",
        "Explain FastAPI",
        "How does async work?",
    ]
    
    print(f"\nSending {len(messages)} messages from same user/session...")
    
    for i, msg in enumerate(messages, 1):
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": msg}]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/v1/messages",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"  {i}. ✓ {msg[:40]}")
            else:
                print(f"  {i}. ✗ {msg[:40]} (status: {response.status_code})")
                
        except Exception as e:
            print(f"  {i}. ✗ {msg[:40]} (error: {e})")
    
    print("\nAll requests from same session are now tracked together!")
    print("Check the dashboard to see the session statistics.")


def main():
    """Main example runner"""
    print("\n" + "="*70)
    print(" Claude Code Proxy with Metrics Dashboard - Examples")
    print("="*70)
    
    print("\nMake sure the application is running:")
    print("  python src/main.py")
    
    # Example 1: Basic request
    user_id, session_id = example_basic_request()
    
    if not user_id:
        print("\n⚠ Could not complete example 1. Make sure the API is running.")
        print("Start the application with: python src/main.py")
        return
    
    # Example 2: Query metrics
    example_query_metrics()
    
    # Example 3: Access dashboard
    example_dashboard_access()
    
    # Example 4: Batch requests (only if example 1 succeeded)
    if user_id and session_id:
        example_batch_requests(user_id, session_id)
    
    print("\n" + "="*70)
    print(" Examples Complete!")
    print("="*70)
    print("\nNext Steps:")
    print(f"1. Open your browser: {DASHBOARD_URL}")
    print("2. Explore the different tabs")
    print("3. Click on rows to see details")
    print("4. Hover over message previews for full content")
    print("5. Check API endpoints for programmatic access")
    print("\nFor more information:")
    print("  - DASHBOARD_QUICKSTART.md - Quick start guide")
    print("  - DASHBOARD.md - Full API documentation")
    print("  - IMPLEMENTATION_SUMMARY.md - Implementation details")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
