import os
import json
import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

load_dotenv()

# Configure Google Cloud
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = "us-central1"  # Can be adjusted as needed
API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Google AI
if API_KEY:
    genai.configure(api_key=API_KEY)

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=REGION)

class GeminiService:
    """Gemini model service wrapper"""
    
    # Topic configurations - moved from hardcoded values to class configuration
    TOPIC_CONFIGS = {
        "taoism": {
            "keywords": ["道教", "老子", "道德经", "太上老君", "张道陵"],
            "guidance": """The reference materials contain information about Taoism. Please read carefully and extract relevant content to answer the question.
Note the historical development of Taoism, key figures (such as Laozi, Zhang Daoling, etc.), and core concepts (such as Dao, De, Wu Wei, etc.).
If the question is about the founder of Taoism, pay special attention to content about Laozi, Zhang Daoling, and the Five Pecks of Rice Taoism."""
        },
        "buddhism": {
            "keywords": ["佛教", "释迦牟尼", "佛陀", "菩萨", "禅宗"],
            "guidance": """The reference materials contain information about Buddhism. Please read carefully and extract relevant content to answer the question.
Note the historical development of Buddhism, key figures (such as Shakyamuni, Bodhisattvas, etc.), and core concepts (such as the Four Noble Truths, the Eightfold Path, etc.).
If the question is about the founder of Buddhism, pay special attention to content about Buddha Shakyamuni (Siddhartha Gautama)."""
        }
    }
    
    # Special terms for relevance detection
    RELEVANCE_TERMS = {
        "religion": ["道教", "老子", "佛教", "释迦牟尼"]
    }
    
    def __init__(self):
        self.model_id = "gemini-2.5-pro-exp-03-25"
        self.embedding_model_name = "models/gemini-embedding-exp-03-07"  # Updated to correct model name format
        # Add simple embedding cache to avoid repeated calculations
        self.embedding_cache = {}
        # Add completion cache
        self._completion_cache = {}
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        import time
        import random
        import hashlib
        
        # If text is empty, return zero vector
        if not text.strip():
            return [0.0] * 768  # Maintain consistent 768 dimensions
            
        # Use text hash as cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Maximum retry attempts
        max_retries = 3
        # Initial wait time (seconds)
        base_wait_time = 2
        
        for retry in range(max_retries + 1):
            try:
                # Use correct embedding model API call
                result = genai.embed_content(
                    model="models/gemini-embedding-exp-03-07",
                    content=text,
                    task_type="SEMANTIC_SIMILARITY"
                )
                
                # Correctly extract embedding vector
                embedding = None
                
                # Google AI API return structure might be a dictionary, need to extract correctly
                if isinstance(result, dict):
                    if 'embedding' in result:
                        embedding = result['embedding']
                    elif 'embeddings' in result:
                        embedding = result['embeddings'][0]
                    elif 'values' in result:
                        embedding = result['values']
                    else:
                        # Check nested structure
                        print(f"Embedding result structure: {result.keys()}")
                else:
                    # Try using attribute access
                    try:
                        embedding = result.embedding
                    except AttributeError:
                        try:
                            embedding = result.embeddings[0]
                        except (AttributeError, IndexError):
                            print(f"Embedding result type: {type(result)}")
                
                if embedding:
                    # Ensure consistent dimensions - truncate or pad to 768 dimensions
                    embedding_length = len(embedding)
                    if embedding_length != 768:
                        print(f"Embedding vector dimension is not 768 ({embedding_length}), adjusting")
                        if embedding_length > 768:
                            # Truncate to 768 dimensions
                            embedding = embedding[:768]
                        else:
                            # Pad to 768 dimensions
                            embedding = embedding + [0.0] * (768 - embedding_length)
                    
                    # Save to cache
                    self.embedding_cache[cache_key] = embedding
                    return embedding
                
            except Exception as e:
                error_message = str(e)
                print(f"Error generating embedding vector: {error_message}")
                
                # Check if quota limit error
                if "429" in error_message or "Resource has been exhausted" in error_message:
                    if retry < max_retries:
                        # Calculate wait time (exponential backoff)
                        wait_time = base_wait_time * (2 ** retry) + random.uniform(0, 1)
                        print(f"API quota limit, waiting {wait_time:.2f} seconds before retry ({retry+1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("Maximum retry attempts reached, using random vector")
                
                # For other errors or after failed retries, use random vector
                break
                
        # All retries failed, return random vector - use fixed 768 dimensions
        print("Using random vector as embedding")
        random_embedding = list(np.random.rand(768))  # Always return 768-dimensional random vector
        
        # Save random vector to cache to avoid generating different random vectors for the same text
        self.embedding_cache[cache_key] = random_embedding
        return random_embedding
        
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 5) -> List[List[float]]:
        """Batch generate embedding vectors for texts, reducing API call frequency"""
        results = []
        # Split input into multiple batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            print(f"Processing embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}, size: {len(batch)}")
            
            # Process each text in the batch in parallel
            import asyncio
            embeddings = await asyncio.gather(*[self.generate_embedding(text) for text in batch])
            results.extend(embeddings)
            
            # Add brief delay between batches to avoid exceeding API limits
            if i + batch_size < len(texts):
                await asyncio.sleep(1)
                
        return results
        
    async def generate_completion(self, prompt: str, context: Optional[str] = None, complexity: str = "normal", use_cache: bool = True) -> str:
        """Generate text completion using Gemini with optimized settings
        
        Args:
            prompt: The prompt text
            context: Optional context to prepend to the prompt
            complexity: Task complexity level ('simple', 'normal', 'complex')
            use_cache: Whether to use cache for the completion
            
        Returns:
            Generated text completion
        """
        # Prepare full prompt with context
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        # Use cache if enabled
        if use_cache:
            import hashlib
            cache_key = hashlib.md5((full_prompt + complexity).encode()).hexdigest()
            if cache_key in self._completion_cache:
                print(f"Using cached completion for prompt: {prompt[:50]}...")
                return self._completion_cache[cache_key]
        
        # Select model based on task complexity
        model_name = self.model_id
        use_thinking_budget = False
        
        # Use more advanced models for complex tasks if available
        if complexity == "complex" and "2.0" in self.model_id:
            try:
                # Try to use Gemini 2.5 for complex tasks if available
                model_name = "gemini-2.5-flash-preview-04-17"
                use_thinking_budget = True
            except Exception:
                model_name = self.model_id
        
        # Initialize model
        model = genai.GenerativeModel(model_name)
        
        # Set generation configuration
        generation_config = {}
        
        # Apply thinking budget for supported models
        if use_thinking_budget:
            thinking_budget = 0
            if complexity == "simple":
                thinking_budget = 0  # No thinking for simple tasks
            elif complexity == "normal":
                thinking_budget = 1024  # Moderate thinking for normal tasks
            elif complexity == "complex":
                thinking_budget = 8192  # Deep thinking for complex tasks
            
            generation_config = {
                "thinking_config": {"thinking_budget": thinking_budget}
            }
        
        # Generate response with error handling
        try:
            # Apply generation config if provided
            if generation_config:
                response = model.generate_content(full_prompt, generation_config=generation_config)
            else:
                response = model.generate_content(full_prompt)
            
            result = response.text
            
            # Cache the result if caching is enabled
            if use_cache:
                if not hasattr(self, '_completion_cache'):
                    self._completion_cache = {}
                self._completion_cache[cache_key] = result
                
            return result
            
        except Exception as e:
            print(f"Error generating completion with {model_name}: {e}")
            
            # Fallback to basic model if advanced model fails
            if model_name != self.model_id:
                print(f"Falling back to default model {self.model_id}")
                try:
                    fallback_model = genai.GenerativeModel(self.model_id)
                    fallback_response = fallback_model.generate_content(full_prompt)
                    return fallback_response.text
                except Exception as fallback_error:
                    print(f"Fallback also failed: {fallback_error}")
            
            # If all fails, return error message or empty string
            return f"Error generating completion: {str(e)}"
        
        # All model calls have failed, try a fallback approach or return error message
        fallback_text = "I'm sorry, but I couldn't generate a response at this time. Please try again later."
        
        if use_cache:
            # Cache the completion result
            self._completion_cache[cache_key] = fallback_text
            
        return fallback_text
        
    def _identify_topic(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Identify query topic and return relevant guidance
        
        Args:
            query: The user query
            
        Returns:
            Tuple containing:
                - is_match: Whether a topic was matched
                - topic_name: Name of matched topic or None
                - guidance: Topic-specific guidance or None
        """
        for topic_name, config in self.TOPIC_CONFIGS.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword in query:
                    return True, topic_name, config.get("guidance", "")
        
        return False, None, None
        
    async def prepare_context(self, query: str, similar_docs: List[Dict[str, Any]]) -> str:
        """Prepare prompt context containing relevant documents"""
        # Detect if it's a Chinese query
        is_chinese_query = any('\u4e00' <= c <= '\u9fff' for c in query)
        
        if is_chinese_query:
            context = "Below are document contents relevant to your query:\n\n"
            
            # Use the topic identification method instead of hardcoded checks
            is_topic_match, topic_name, topic_guidance = self._identify_topic(query)
            if is_topic_match and topic_guidance:
                context += f"{topic_guidance}\n\n"
        else:
            context = "Below is information relevant to your query:\n\n"
        
        # Sort by similarity to ensure most relevant documents come first
        sorted_docs = sorted(similar_docs, key=lambda x: x.get("similarity", 0), reverse=True)
        
        # Analyze document content to detect if there's particularly relevant content
        has_highly_relevant = False
        for doc in sorted_docs:
            similarity = doc.get("similarity", 0)
            content = doc.get("content", "")
            
            # Use the configured relevance terms instead of hardcoded values
            all_relevance_terms = []
            for term_list in self.RELEVANCE_TERMS.values():
                all_relevance_terms.extend(term_list)
                
            if similarity > 0.7 or any(term in content for term in all_relevance_terms if term in query):
                has_highly_relevant = True
                break
        
        # Add document content to context
        for i, doc in enumerate(sorted_docs):
            # Get document metadata, especially source information
            metadata = doc.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            doc_id = doc.get("id", "")
            # Get source, try multiple possible fields
            source = (
                metadata.get("source", "") or 
                doc.get("source", "") or 
                metadata.get("pdf_filename", "") or 
                metadata.get("filename", "")
            )
            
            if not source and doc_id:
                source = f"Document ID: {doc_id}"
            elif not source:
                source = f"Document Fragment #{i+1}"
                
            # Get chunk information
            chunk_info = ""
            if "chunk" in metadata and "total_chunks" in metadata:
                chunk_info = f"(Chunk {metadata['chunk']}/{metadata['total_chunks']})"
            
            # Get similarity
            similarity = doc.get("similarity", 0)
            similarity_info = f"Similarity: {similarity:.2f}" if similarity else ""
            
            # Add complete document content with better formatting
            content = doc.get("content", "").strip()
            if content:
                document_header = f"Document {i+1} {chunk_info} {similarity_info}:"
                if is_chinese_query:
                    # Add more concise separation for Chinese content, avoid using too many "=" symbols
                    context += f"{document_header}\n---\n{content}\n---\n\n"
                else:
                    context += f"{document_header}\n{content}\n\n"
        
        # Add specific instructions for Chinese queries
        if is_chinese_query:
            if has_highly_relevant:
                # Has highly relevant content
                context += """Please answer the following question based on the document content above. Please pay special attention to:
1. Extract the information most relevant to the question from the documents
2. Organize information to form logical and structured answers
3. If information in the documents is insufficient or contradictory, clearly indicate this
4. Explain professional concepts in a way users can understand
5. First identify the core of the question, then look for answers from the documents in a targeted manner"""
            else:
                # No highly relevant content
                context += """Please answer the following question based on the document content above. If there is not enough information in the documents, please clearly indicate this:
1. Prioritize using information from the documents to answer the question
2. Clearly indicate which parts are extracted from the documents and which are supplemented based on general knowledge
3. If there is no relevant information in the documents at all, please clearly inform the user"""
        
        return context

    async def determine_chunking_strategy(self, text_sample: str, file_type: str) -> Tuple[int, int, List[Dict]]:
        """Determine the best chunking strategy for document text
        
        Args:
            text_sample: Sample text from document for analysis
            file_type: Type of the document file (pdf, txt, etc.)
            
        Returns:
            Tuple containing chunk size, overlap size, and optional strategy info
        """
        # Default values for fixed size chunking
        default_chunk_size = 1000
        default_overlap = 200
        
        # If text sample is too short, return default values
        if len(text_sample) < 1000:
            return default_chunk_size, default_overlap, []
        
        try:
            # Create prompt for analyzing document structure
            prompt = f"""Analyze the following document text sample and recommend a chunking strategy for vector storage. 
The document appears to be a {file_type.upper()} file.

Document Sample:
---
{text_sample[:3000]}  # Limit sample size
---

Based on this sample, determine:
1. Is this document structured with clear sections, chapters, or paragraphs?
2. What would be the ideal chunk size (in characters) considering the document structure?
3. How much overlap between chunks is recommended?
4. Are there any special considerations for this document type?

Return your analysis as a structured JSON object with the following fields:
- chunk_size: (integer) Recommended size in characters
- overlap: (integer) Recommended overlap in characters  
- strategy: (string) One of ["fixed_size", "paragraph", "section", "semantic"]
- reasoning: (string) Brief explanation of your recommendation
- additional_notes: (string) Any special considerations

JSON response only:"""
            
            # Generate analysis
            print("Generating document structure analysis...")
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Try to extract JSON from response
            try:
                # Remove any markdown formatting if present
                json_text = response_text
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1].split("```")[0].strip()
                elif "```" in json_text:
                    json_text = json_text.split("```")[1].split("```")[0].strip()
                
                recommendation = json.loads(json_text)
                
                # Extract values with validation
                chunk_size = int(recommendation.get("chunk_size", default_chunk_size))
                if chunk_size < 100 or chunk_size > 10000:
                    print(f"Invalid chunk_size recommended: {chunk_size}, using default")
                    chunk_size = default_chunk_size
                    
                overlap = int(recommendation.get("overlap", default_overlap))
                if overlap < 0 or overlap > chunk_size // 2:
                    print(f"Invalid overlap recommended: {overlap}, using default")
                    overlap = default_overlap
                
                strategy = recommendation.get("strategy", "fixed_size")
                reasoning = recommendation.get("reasoning", "")
                notes = recommendation.get("additional_notes", "")
                
                print(f"Recommended chunking strategy: {strategy}, chunk_size: {chunk_size}, overlap: {overlap}")
                
                return chunk_size, overlap, [recommendation]
                
            except json.JSONDecodeError:
                print(f"Could not parse JSON from response: {response_text}")
                return default_chunk_size, default_overlap, []
                
        except Exception as e:
            print(f"Error determining chunking strategy: {e}")
            return default_chunk_size, default_overlap, []

    async def intelligent_chunking(self, text: str, file_type: str) -> List[Dict]:
        """Intelligently chunk document text based on content and structure
        
        Args:
            text: Full document text
            file_type: Type of the document file (pdf, txt, etc.)
            
        Returns:
            List of chunks, each containing content and metadata
        """
        # Sample the text to determine chunking strategy
        text_sample = text[:5000]
        chunk_size, overlap, strategy_info = await self.determine_chunking_strategy(text_sample, file_type)
        
        # If very short text, don't chunk
        if len(text) < chunk_size // 2:
            return [{
                "content": text,
                "metadata": {
                    "strategy": "no_chunking",
                    "chunk_index": 1,
                    "total_chunks": 1
                }
            }]
        
        strategy = strategy_info[0].get("strategy", "fixed_size") if strategy_info else "fixed_size"
        
        if strategy == "paragraph":
            # Split by paragraphs
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            
            chunks = []
            current_chunk = ""
            current_chunks = []
            
            for i, para in enumerate(paragraphs):
                # If paragraph is too long, split it further
                if len(para) > chunk_size:
                    if current_chunk:
                        chunks.append({
                            "content": current_chunk,
                            "metadata": {
                                "strategy": "paragraph",
                                "chunk_index": len(chunks) + 1
                            }
                        })
                        current_chunk = ""
                    
                    # Split long paragraph into smaller pieces
                    for j in range(0, len(para), chunk_size - overlap):
                        sub_chunk = para[j:j + chunk_size]
                        if sub_chunk:
                            chunks.append({
                                "content": sub_chunk,
                                "metadata": {
                                    "strategy": "paragraph_split",
                                    "chunk_index": len(chunks) + 1,
                                    "paragraph_index": i + 1
                                }
                            })
                else:
                    # Add paragraph to current chunk
                    if len(current_chunk) + len(para) > chunk_size:
                        # Current chunk is full, save it and start a new one
                        chunks.append({
                            "content": current_chunk,
                            "metadata": {
                                "strategy": "paragraph",
                                "chunk_index": len(chunks) + 1
                            }
                        })
                        current_chunk = para
                    else:
                        # Add to current chunk
                        current_chunk += ("\n\n" if current_chunk else "") + para
            
            # Add the last chunk if not empty
            if current_chunk:
                chunks.append({
                    "content": current_chunk,
                    "metadata": {
                        "strategy": "paragraph",
                        "chunk_index": len(chunks) + 1
                    }
                })
            
            # Add total chunks to metadata
            for chunk in chunks:
                chunk["metadata"]["total_chunks"] = len(chunks)
            
            return chunks
            
        else:
            # Default to fixed size chunking
            chunks = []
            for i in range(0, len(text), chunk_size - overlap):
                chunk_text = text[i:i + chunk_size]
                if chunk_text.strip():
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {
                            "strategy": "fixed_size",
                            "chunk_size": chunk_size,
                            "overlap": overlap,
                            "chunk_index": len(chunks) + 1
                        }
                    })
            
            # Add total chunks to metadata
            for chunk in chunks:
                chunk["metadata"]["total_chunks"] = len(chunks)
            
            return chunks 
