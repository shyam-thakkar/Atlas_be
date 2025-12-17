#!/usr/bin/env python
"""
Test script for paginated chat history API
"""
import requests
import json

def test_paginated_history(session_id):
    """Test the paginated chat history endpoint"""
    
    base_url = f"http://localhost:8000/chat/history/{session_id}/"
    
    print("=" * 70)
    print("Testing Paginated Chat History API")
    print("=" * 70)
    
    # Test 1: Get first page with default page size
    print("\n📄 Test 1: First page (default: 20 messages)")
    print("-" * 70)
    response = requests.get(base_url)
    data = response.json()
    
    if data.get('success'):
        print(f"✓ Success!")
        print(f"  Session: {data['session_id']}")
        print(f"  Messages on this page: {len(data['messages'])}")
        print(f"  Pagination info:")
        print(f"    - Page: {data['pagination']['page']}")
        print(f"    - Page size: {data['pagination']['page_size']}")
        print(f"    - Total messages: {data['pagination']['total_messages']}")
        print(f"    - Total pages: {data['pagination']['total_pages']}")
        print(f"    - Has next: {data['pagination']['has_next']}")
        print(f"    - Has previous: {data['pagination']['has_previous']}")
    else:
        print(f"✗ Error: {data.get('error')}")
        return
    
    total_pages = data['pagination']['total_pages']
    
    # Test 2: Get specific page with custom page size
    if total_pages > 1:
        print("\n📄 Test 2: Second page with 10 messages per page")
        print("-" * 70)
        response = requests.get(f"{base_url}?page=2&page_size=10")
        data = response.json()
        
        if data.get('success'):
            print(f"✓ Success!")
            print(f"  Messages on page 2: {len(data['messages'])}")
            print(f"  Has next: {data['pagination']['has_next']}")
            print(f"  Has previous: {data['pagination']['has_previous']}")
        else:
            print(f"✗ Error: {data.get('error')}")
    
    # Test 3: Get all messages with large page size
    print("\n📄 Test 3: All messages (page_size=100)")
    print("-" * 70)
    response = requests.get(f"{base_url}?page_size=100")
    data = response.json()
    
    if data.get('success'):
        print(f"✓ Success!")
        print(f"  Total messages retrieved: {len(data['messages'])}")
        print(f"  All messages in one page: {not data['pagination']['has_next']}")
    else:
        print(f"✗ Error: {data.get('error')}")
    
    # Test 4: Invalid page
    print("\n📄 Test 4: Invalid page number (page=999)")
    print("-" * 70)
    response = requests.get(f"{base_url}?page=999")
    data = response.json()
    
    if data.get('success'):
        print(f"✓ Success (returns empty messages for out-of-range page)")
        print(f"  Messages: {len(data['messages'])}")
    else:
        print(f"✗ Error: {data.get('error')}")
    
    print("\n" + "=" * 70)
    print("Testing complete!")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_pagination.py <session_id>")
        print("\nExample:")
        print("  python test_pagination.py 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)
    
    session_id = sys.argv[1]
    test_paginated_history(session_id)
