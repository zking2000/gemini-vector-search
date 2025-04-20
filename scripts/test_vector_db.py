import os
import sys
import json
import asyncio
from pathlib import Path
from sqlalchemy import text

# Add project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.db.database import get_db
from app.services.vector_service import VectorService
from app.models.vector_models import Document

# Load environment variables
load_dotenv()

async def test_vector_operations():
    """Test basic vector database operations, including document addition and similarity search"""
    print("Starting vector database operation test...")
    
    vector_service = VectorService()
    
    # Test documents
    test_documents = [
        {
            "content": "Artificial intelligence is a branch of computer science that aims to create systems capable of performing tasks that typically require human intelligence.",
            "metadata": {"source": "AI Introduction", "category": "Technology"}
        },
        {
            "content": "Machine learning is a subset of artificial intelligence that uses statistical techniques to enable computer systems to learn from data without being explicitly programmed.",
            "metadata": {"source": "ML Introduction", "category": "Technology"}
        },
        {
            "content": "Deep learning is a machine learning method that uses multi-layer neural networks to simulate the human brain's learning process.",
            "metadata": {"source": "DL Introduction", "category": "Technology"}
        },
        {
            "content": "Natural language processing is a branch of artificial intelligence that focuses on enabling computers to understand, interpret, and generate human language.",
            "metadata": {"source": "NLP Introduction", "category": "Technology"}
        },
        {
            "content": "Computer vision is an interdisciplinary field that focuses on enabling computers to gain high-level understanding from digital images or videos.",
            "metadata": {"source": "CV Introduction", "category": "Technology"}
        }
    ]
    
    # Get database session
    db = next(get_db())

    try:
        # Add test documents
        print("\nAdding test documents to vector database...")
        doc_ids = []
        for doc in test_documents:
            document = await vector_service.add_document(
                db=db, 
                content=doc["content"], 
                metadata=doc["metadata"]
            )
            doc_ids.append(document.id)
            print(f"Added document ID: {document.id}, Content: {doc['content'][:50]}...")
        
        # Perform similarity search
        print("\nPerforming similarity search...")
        query = "neural networks and deep learning"
        results = await vector_service.search_similar(db=db, query=query, limit=3)
        
        print(f"\nQuery: '{query}'")
        print(f"Found {len(results)} similar documents:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Document ID: {result['id']}")
            print(f"   Title/Content: {result['title']}")
            if result['title'] != result['content']:
                print(f"   Content: {result['content']}")
            print(f"   Metadata: {result['metadata']}")
            print(f"   Similarity: {result['similarity']:.4f}")
        
        print("\nQuerying original documents in database...");
        # Query document information stored in the database
        result_ids = [result['id'] for result in results]
        for doc_id in result_ids:
            try:
                # Use SQL directly to avoid ORM model field mismatch issues
                query = f"SELECT id, title, doc_metadata FROM documents WHERE id = {doc_id}"
                doc_row = db.execute(text(query)).fetchone()
                if doc_row:
                    print(f"\nDocument ID: {doc_row.id}")
                    print(f"   Title: {doc_row.title}")
                    # Try to parse metadata
                    try:
                        metadata = json.loads(doc_row.doc_metadata) if isinstance(doc_row.doc_metadata, str) else doc_row.doc_metadata
                        # Don't display embedding vector to simplify output
                        if '_embedding' in metadata:
                            embedding_length = len(metadata['_embedding'])
                            metadata['_embedding'] = f"[Vector, Dimension: {embedding_length}]"
                        print(f"   Metadata: {metadata}")
                    except Exception as e:
                        print(f"   Metadata parsing error: {e}")
            except Exception as e:
                print(f"Error querying document {doc_id}: {e}")
        
        print("\nVector database test completed!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Run asynchronous test function
    asyncio.run(test_vector_operations()) 