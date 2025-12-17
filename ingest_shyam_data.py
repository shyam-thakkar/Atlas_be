"""
Ingestion Script for Shyam Thakkar's Portfolio Data
Run this script to populate the RAG database with Shyam's information
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.models import Document
from chat.rag_service import RAGService
from chat.shyam_portfolio_data import SHYAM_PORTFOLIO_DATA


def ingest_shyam_data():
    """
    Ingest Shyam Thakkar's portfolio data into the RAG system
    """
    print("=" * 70)
    print("Shyam Thakkar's Portfolio Data Ingestion")
    print("=" * 70)
    
    rag_service = RAGService()
    
    # Check if data already exists
    existing_count = Document.objects.count()
    if existing_count > 0:
        print(f"\n⚠️  Warning: Database already contains {existing_count} documents.")
        response = input("Do you want to clear existing data and start fresh? (yes/no): ")
        if response.lower() == 'yes':
            Document.objects.all().delete()
            print("✓ Cleared existing documents")
        else:
            print("Keeping existing documents and adding new ones...")
    
    print(f"\n📊 Ingesting {len(SHYAM_PORTFOLIO_DATA)} documents...")
    print("-" * 70)
    
    success_count = 0
    failed_count = 0
    
    for i, doc_data in enumerate(SHYAM_PORTFOLIO_DATA, 1):
        try:
            # Use RAG service to add document (includes embedding generation)
            doc = rag_service.add_document(
                text=doc_data['text'],
                category=doc_data['category'],
                title=doc_data['title'],
                source=doc_data['source']
            )
            
            print(f"✓ [{i}/{len(SHYAM_PORTFOLIO_DATA)}] Added: {doc_data['category']} - {doc_data['title']}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ [{i}/{len(SHYAM_PORTFOLIO_DATA)}] Failed: {doc_data['title']} - Error: {str(e)}")
            failed_count += 1
    
    print("-" * 70)
    print(f"\n✅ Ingestion Complete!")
    print(f"   Successfully added: {success_count} documents")
    if failed_count > 0:
        print(f"   Failed: {failed_count} documents")
    
    # Show statistics
    print("\n📈 Database Statistics:")
    from django.db.models import Count
    categories = Document.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for cat in categories:
        print(f"   - {cat['category']}: {cat['count']} documents")
    
    print(f"\n   Total documents: {Document.objects.count()}")
    
    print("\n" + "=" * 70)
    print("🎉 Your RAG chatbot is now ready to answer questions about Shyam!")
    print("=" * 70)
    
    # Test query
    print("\n🧪 Testing with a sample query...")
    try:
        result = rag_service.process_query(
            query="What are Shyam's technical skills?",
            top_k=3,
            save_history=False
        )
        print(f"\nSample Response:\n{result['response'][:300]}...")
        print(f"\nSources used: {len(result['sources'])} documents")
    except Exception as e:
        print(f"Test query failed: {str(e)}")


if __name__ == "__main__":
    try:
        ingest_shyam_data()
    except KeyboardInterrupt:
        print("\n\nIngestion cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during ingestion: {str(e)}")
        import traceback
        traceback.print_exc()
