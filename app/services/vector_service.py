from typing import List, Dict, Any
import json
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, text, inspect
from app.models.vector_models import Document
from app.services.gemini_service import GeminiService
import traceback
from app.services.cache_service import cached

class VectorService:
    """Vector database service"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
    
    async def add_document(self, db: Session, content: str, metadata: Dict[str, Any] = None) -> Document:
        """Add document to vector database"""
        try:
            # Generate embedding vector
            embedding = await self.gemini_service.generate_embedding(content)
            
            # Print debug information
            print(f"Adding document: content length={len(content)}, metadata={metadata}")
            print(f"Embedding vector length={len(embedding)}")
            
            # Check database table structure
            inspector = inspect(db.bind)
            table_columns = inspector.get_columns("documents")
            column_names = [col['name'] for col in table_columns]
            print(f"Table structure: {column_names}")
            
            # Create document object based on updated Document model
            # Ensure title is not empty, use default value if content is empty
            if not content.strip():
                title = f"Document #{metadata.get('chunk', 'Unknown')} of {metadata.get('total_chunks', 'Unknown')}" if metadata else "Empty document"
            else:
                # If content is too long, it may need to be truncated
                max_title_length = 255  # Maximum length of String(255)
                title = content[:max_title_length] if len(content) > max_title_length else content
            
            # Merge metadata and embedding
            combined_metadata = metadata.copy() if metadata else {}
            # Add embedding vector to metadata
            combined_metadata["_embedding"] = embedding
            
            # Ensure doc_metadata is a JSON string
            doc_metadata_json = json.dumps(combined_metadata) if combined_metadata else None
            
            # Create document object - don't specify id, let database generate it
            doc = Document(
                title=title,
                doc_metadata=doc_metadata_json
            )
            
            # Save to database
            try:
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
            except Exception as db_error:
                # If error occurs, rollback and retry
                db.rollback()
                print(f"Database operation failed, trying rollback and retry: {db_error}")
                # Try again, this time explicitly specify an id
                import random
                doc.id = random.randint(1, 1000000)  # Generate a random ID
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
                
        except Exception as e:
            print(f"Error adding document to database: {e}")
            # Ensure session is rolled back
            try:
                db.rollback()
            except:
                pass
            raise
    
    @cached(ttl=24*3600)  # Cache for 24 hours
    async def generate_embeddings(self, text, model_name="embedding-001"):
        """
        Generate vector embeddings for text, with cache support
        
        Parameters:
            text: Text content
            model_name: Embedding model name
            
        Returns:
            Vector representation of the text
        """
        return await self.gemini_service.generate_embedding(text)
    
    @cached(ttl=3600)  # Cache for 1 hour
    async def search_similar_chunks(self, db: Session, query: str, limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search for document chunks most similar to the query text, with cache support
        
        Args:
            db: Database session
            query: Query text
            limit: Maximum number of results to return
            source_filter: Optional document source filter
            
        Returns:
            documents: List of similar document chunks
        """
        try:
            # Record search start
            print(f"Starting search for similar documents, query: '{query}'")
            
            # Generate embedding vector for query
            query_embedding = await self.generate_embeddings(query)
            query_dim = len(query_embedding)
            print(f"Query vector dimension: {query_dim}")
            
            # Build query SQL
            sql = """
                SELECT id, title, title as content, doc_metadata
                FROM documents
            """
            
            # Add filter conditions
            params = {}
            where_clauses = []
            
            if source_filter:
                where_clauses.append("doc_metadata::text LIKE :source")
                params["source"] = f"%{source_filter}%"
            
            # For Chinese queries, add additional text matching conditions
            if any('\u4e00' <= c <= '\u9fff' for c in query):
                # This is a Chinese query, add content matching conditions to improve recall
                print("Chinese query detected, adding text matching conditions")
                
                # Split Chinese query into individual characters rather than phrases
                # More effective for Chinese where individual characters have meaning
                chinese_chars = [c for c in query if '\u4e00' <= c <= '\u9fff']
                
                # Only select meaningful characters (avoid filler words like "的", "是", etc.)
                meaningful_chars = []
                common_stopwords = ["的", "是", "了", "在", "和", "与", "或", "什么", "为", "吗"]
                
                for char in chinese_chars:
                    if char not in common_stopwords and len(char.strip()) > 0:
                        meaningful_chars.append(char)
                
                # If we have single characters, add to search conditions
                if meaningful_chars:
                    term_conditions = []
                    for i, char in enumerate(meaningful_chars):
                        param_name = f"term_{i}"
                        term_conditions.append(f"title ILIKE :{param_name}")
                        params[param_name] = f"%{char}%"
                    
                    # Connect term conditions with OR
                    if term_conditions:
                        where_clauses.append(f"({' OR '.join(term_conditions)})")
                else:
                    # If no meaningful characters found, fall back to original logic
                    query_terms = [term for term in query.split() if len(term) > 1]
                    if query_terms:
                        term_conditions = []
                        for i, term in enumerate(query_terms):
                            param_name = f"term_{i}"
                            term_conditions.append(f"title ILIKE :{param_name}")
                            params[param_name] = f"%{term}%"
                        
                        # Connect term conditions with OR
                        if term_conditions:
                            where_clauses.append(f"({' OR '.join(term_conditions)})")
            
            # Assemble WHERE clause
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
                
            # Add limit - increase search range
            sql += " LIMIT 300"  # Increase document retrieval count to improve chances of finding relevant content
            
            print(f"Executing SQL: {sql}")
            print(f"Parameters: {params}")
            
            # Get documents
            result = db.execute(text(sql), params)
            
            # Calculate similarity in Python
            documents = []
            compatible_docs = 0
            incompatible_docs = 0
            processed_docs = 0
            
            for row in result:
                processed_docs += 1
                try:
                    # Extract embedding from doc_metadata
                    # Process doc_metadata, which may be dictionary or JSON string
                    if row.doc_metadata is None:
                        continue
                        
                    metadata = row.doc_metadata
                    # If it's a string, try to parse as JSON
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse metadata for document id={row.id}: {e}")
                            continue
                    # If not a dictionary type, skip
                    if not isinstance(metadata, dict):
                        print(f"Metadata for document id={row.id} is not a valid JSON or dictionary: {type(metadata)}")
                        continue
                        
                    doc_embedding = metadata.get("_embedding")
                    
                    if doc_embedding:
                        doc_dim = len(doc_embedding)
                        
                        # Calculate cosine similarity
                        try:
                            similarity = self.cosine_similarity(query_embedding, doc_embedding)
                            compatible_docs += 1
                            
                            # If Chinese query and title contains query terms, boost similarity score
                            if any('\u4e00' <= c <= '\u9fff' for c in query):
                                title = row.title or ""
                                query_terms = [term for term in query.split() if len(term) > 1]
                                boost = 0
                                for term in query_terms:
                                    if term in title:
                                        boost += 0.05  # Increase score by 0.05 for each matching term
                                
                                if boost > 0:
                                    original_similarity = similarity
                                    similarity = min(1.0, similarity + boost)
                                    print(f"Document id={row.id}, title match boosts similarity: {original_similarity} -> {similarity}")
                                    
                        except Exception as e:
                            print(f"Error processing document id={row.id}: {e}")
                            incompatible_docs += 1
                            continue
                        
                        # Add source file and import time information
                        pdf_filename = metadata.get("pdf_filename", metadata.get("source", "Unknown source"))
                        import_time = metadata.get("import_timestamp", "Unknown time")
                        chunk_info = f"{metadata.get('chunk', '?')}/{metadata.get('total_chunks', '?')}"
                        
                        # Get document content - use content field if available, otherwise use title
                        document_content = row.title
                        
                        # Create document record
                        cleaned_metadata = {k: v for k, v in metadata.items() if not k.startswith('_')}  # Exclude internal fields
                        documents.append({
                            "id": row.id,
                            "content": document_content,  # Use actual content, not just title
                            "title": row.title,
                            "metadata": cleaned_metadata,
                            "similarity": float(similarity),
                            "embedding_dim": doc_dim,
                            "source": pdf_filename,
                            "chunk_info": chunk_info,
                            "import_time": import_time
                        })
                except Exception as e:
                    print(f"Error processing document id={row.id}: {e}")
                    continue
            
            print(f"Processed {processed_docs} documents, with {compatible_docs} compatible documents and {incompatible_docs} incompatible documents")
            
            # Sort by similarity
            documents.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Check if we found sufficiently relevant documents
            if documents and documents[0]["similarity"] < 0.5:
                print(f"Warning: Highest similarity below 0.5: {documents[0]['similarity']}")
                # If highest similarity is less than 0.5, results may not be relevant enough
                
            # Only return top 'limit' results
            top_results = documents[:limit]
            if top_results:
                print(f"Returning {len(top_results)} results, highest similarity: {top_results[0]['similarity']}")
            else:
                print("No similar documents found")
                
            return top_results
        except Exception as e:
            print(f"Error querying similar documents: {e}")
            traceback.print_exc()
            return []
    
    # Add search_similar as an alias for search_similar_chunks to ensure API compatibility
    async def search_similar(self, db: Session, query: str, limit: int = 5, source_filter: str = None) -> List[Dict[str, Any]]:
        """
        Alias method for search_similar_chunks, maintains backward compatibility
        
        Args:
            db: Database session
            query: Query text
            limit: Maximum number of results to return
            source_filter: Optional document source filter
            
        Returns:
            documents: List of similar document chunks
        """
        return await self.search_similar_chunks(db, query, limit, source_filter)
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors, supporting different dimensions"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Check if vector dimensions don't match
        if vec1.shape[0] != vec2.shape[0]:
            print(f"Vector dimensions don't match: {vec1.shape[0]} vs {vec2.shape[0]}")
            
            # Standardize to smaller dimension
            min_dim = min(vec1.shape[0], vec2.shape[0])
            vec1 = vec1[:min_dim]
            vec2 = vec2[:min_dim]
            print(f"Truncated vectors to {min_dim} dimensions")
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        # Avoid division by zero
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0
            
        return dot_product / (norm_vec1 * norm_vec2) 