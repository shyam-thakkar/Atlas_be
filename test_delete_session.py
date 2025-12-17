#!/usr/bin/env python
"""
Test script for delete session API
"""
import requests
import json

def test_delete_session(session_id):
    """Test the delete session endpoint"""
    
    url = f"http://localhost:8000/chat/session/{session_id}/"
    
    print("=" * 70)
    print("Testing Delete Session API")
    print("=" * 70)
    
    # Test 1: Check if session exists (get history)
    print(f"\n📋 Step 1: Checking session {session_id}")
    print("-" * 70)
    history_response = requests.get(f"http://localhost:8000/chat/history/{session_id}/")
    
    if history_response.status_code == 200:
        data = history_response.json()
        message_count = data['pagination']['total_messages']
        print(f"✓ Session found")
        print(f"  Messages: {message_count}")
        print(f"  Created: {data.get('created_at')}")
    else:
        print(f"✗ Session not found (status: {history_response.status_code})")
        return
    
    # Test 2: Delete the session
    print(f"\n🗑️  Step 2: Deleting session")
    print("-" * 70)
    delete_response = requests.delete(url)
    
    if delete_response.status_code == 200:
        data = delete_response.json()
        print(f"✓ Delete successful!")
        print(f"  Message: {data.get('message')}")
        print(f"  Deleted messages: {data.get('deleted_messages')}")
        print(f"  Session ID: {data.get('session_id')}")
    else:
        print(f"✗ Delete failed (status: {delete_response.status_code})")
        print(f"  Response: {delete_response.text}")
        return
    
    # Test 3: Verify session is deleted
    print(f"\n✅ Step 3: Verifying deletion")
    print("-" * 70)
    verify_response = requests.get(f"http://localhost:8000/chat/history/{session_id}/")
    
    if verify_response.status_code == 404:
        print(f"✓ Session successfully deleted (404 Not Found)")
    else:
        print(f"✗ Unexpected: Session still exists (status: {verify_response.status_code})")
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_delete_session.py <session_id>")
        print("\nExample:")
        print("  python test_delete_session.py 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)
    
    session_id = sys.argv[1]
    test_delete_session(session_id)
