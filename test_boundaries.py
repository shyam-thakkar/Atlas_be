#!/usr/bin/env python
"""
Test script to verify the updated RAG service with strict boundaries
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.rag_service import RAGService

def test_queries():
    print("=" * 70)
    print("Testing SHYAM-DEV-1 with Strict Boundaries")
    print("=" * 70)
    
    rag = RAGService()
    
    test_cases = [
        # Valid questions (should answer)
        ("What are your technical skills?", "Should answer with skills"),
        ("Where do you work?", "Should answer with WeServeCodes"),
        ("Tell me about your projects", "Should list projects"),
        
        # Invalid questions (should reject)
        ("What's the weather today?", "Should reject - off topic"),
        ("Tell me a joke", "Should reject - off topic"),
        ("What's 2+2?", "Should reject - off topic"),
    ]
    
    for i, (query, expected) in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {expected}")
        print(f"Query: {query}")
        print("-" * 70)
        
        result = rag.process_query(query, top_k=3)
        
        if result['success']:
            print(f"✓ Response: {result['response'][:200]}...")
            print(f"  Sources: {len(result['sources'])} documents")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")
        
    print(f"\n{'='*70}")
    print("Testing complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_queries()
