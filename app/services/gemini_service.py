import os
import json
import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import asyncio
import time
import random
from datetime import datetime

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

class APIRateLimitError(Exception):
    """API速率限制错误"""
    pass

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
        """Initialize Gemini service, configure Google Cloud and model

        Initialize Google Cloud configuration, Gemini model and various caches and rate limits
        """
        # Configure Google Cloud
        try:
            # Set credentials from environment variable if available
            credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            if credentials_json:
                # Write credentials to temporary file
                credentials_path = "/tmp/google_credentials.json"
                with open(credentials_path, "w") as f:
                    f.write(credentials_json)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            
            # Initialize Google Cloud client
            # No need to explicitly set project as it's included in the credentials
            
            # For production use - check if credentials properly set
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or credentials_json:
                print("Google Cloud credentials configured successfully")
            else:
                print("WARNING: Google Cloud credentials not found")
                
        except Exception as e:
            print(f"Error configuring Google Cloud: {e}")
        
        # Initialize Gemini model
        self.genai = genai
        
        # Use latest Gemini 1.5 Pro model for better comprehension and table handling
        self.model_id = "gemini-1.5-pro-latest"  # Updated to latest model
        self.embedding_model_name = "models/embedding-001"  # Latest embedding model
        
        # Initialize with safety settings
        try:
            # 设置safety_settings - 使用genai的安全设置格式
            safety_settings = {
                genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }
            
            # 使用genai创建模型
            self.model = genai.GenerativeModel(
                model_name=self.model_id,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=8192,
                    candidate_count=1,
                ),
                safety_settings=safety_settings
            )
            
            # Configure system prompt for better table handling
            self.table_system_prompt = """You are a highly capable AI assistant that specializes in understanding and processing data. 
When working with tables:
1. Maintain the structure and alignment of tables in your responses
2. Pay careful attention to numerical data and ensure accuracy when reporting figures
3. When asked about data in tables, respond with precise information from the specific cells referenced
4. For tables with financial data, ensure values are correctly associated with their categories, years, or other dimensions
5. Understand the context of tables - including headers, footers, and annotations - to provide complete and accurate information"""
            
            print(f"Gemini model '{self.model_id}' initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            self.model = None
        
        # Initialize embedding model
        try:
            # 使用genai初始化embedding模型
            self.embedding_model = genai.GenerativeModel(
                model_name=self.embedding_model_name
            )
            print(f"Gemini embedding model '{self.embedding_model_name}' initialized successfully")
        except Exception as e:
            print(f"Error initializing embedding model: {e}")
            self.embedding_model = None
        
        # Initialize cache
        self.embedding_cache = {}  # Cache for document embeddings
        self.completion_cache = {}  # Cache for completions
        
        # API request counter and rate limits
        self.api_requests = 0
        self.api_request_start_time = time.time()
        self.api_rate_limit = 60  # Requests per minute
        self.api_request_lock = asyncio.Lock()  # To prevent concurrent API calls
        
    async def _check_rate_limit(self, api_type: str) -> None:
        """
        检查API请求速率限制，必要时等待
        
        Args:
            api_type: API类型，"embedding"或"completion"
            
        Raises:
            APIRateLimitError: 如果速率限制被触发且不能等待
        """
        async with self.api_request_lock:
            current_time = time.time()
            counter = self.api_requests
            
            # 如果已过重置窗口，重置计数器
            if current_time - self.api_request_start_time > self.api_rate_limit:
                counter = 0
                self.api_request_start_time = current_time
            
            # 检查是否达到限制
            if counter >= self.api_rate_limit:
                # 计算需要等待的时间
                wait_time = self.api_rate_limit - (current_time - self.api_request_start_time)
                
                if wait_time > 0:
                    wait_time = min(wait_time + 1, 60)  # 最多等待60秒
                    print(f"API速率限制: {api_type} 请求达到限制，等待 {wait_time:.2f} 秒")
                    # 记录等待事件
                    start_wait = datetime.now().strftime("%H:%M:%S")
                    
                    # 等待指定时间
                    await asyncio.sleep(wait_time)
                    
                    # 等待结束后记录
                    end_wait = datetime.now().strftime("%H:%M:%S")
                    print(f"API速率限制等待结束 ({start_wait} -> {end_wait})")
                    
                    # 重置计数器
                    counter = 0
                    self.api_request_start_time = time.time()
            
            # 增加计数器
            counter += 1
            # 记录最后请求时间
            self.api_requests = counter
    
    async def generate_embedding(self, text: str) -> List[float]:
        """生成embedding向量，带重试和限流机制"""
        import hashlib
        
        # 如果文本为空，返回零向量
        if not text.strip():
            return [0.0] * 768  # 保持一致的768维度
            
        # 使用文本哈希作为缓存键
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # 检查缓存
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # 最大重试次数和初始等待时间
        max_retries = 5
        base_wait = 1.0
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 检查速率限制
                await self._check_rate_limit("embedding")
                
                # 调用embedding API
                result = genai.embed_content(
                    model="models/gemini-embedding-exp-03-07",
                    content=text,
                    task_type="SEMANTIC_SIMILARITY"
                )
                
                # 正确提取embedding向量
                embedding = None
                
                # Google AI API返回结构可能是字典，需要正确提取
                if isinstance(result, dict):
                    if 'embedding' in result:
                        embedding = result['embedding']
                    elif 'embeddings' in result:
                        embedding = result['embeddings'][0]
                    elif 'values' in result:
                        embedding = result['values']
                    else:
                        # 检查嵌套结构
                        print(f"Embedding结果结构: {result.keys()}")
                else:
                    # 尝试使用属性访问
                    try:
                        embedding = result.embedding
                    except AttributeError:
                        try:
                            embedding = result.embeddings[0]
                        except (AttributeError, IndexError):
                            print(f"Embedding结果类型: {type(result)}")
                
                if embedding:
                    # 确保一致的维度 - 截断或填充到768维度
                    embedding_length = len(embedding)
                    if embedding_length != 768:
                        print(f"Embedding向量维度不是768 ({embedding_length})，进行调整")
                        if embedding_length > 768:
                            # 截断到768维度
                            embedding = embedding[:768]
                        else:
                            # 填充到768维度
                            embedding = embedding + [0.0] * (768 - embedding_length)
                    
                    # 保存到缓存
                    self.embedding_cache[cache_key] = embedding
                    return embedding
                
                # 如果没有有效结果但没有异常，继续尝试
                retry_count += 1
                
            except Exception as e:
                error_message = str(e)
                print(f"生成embedding向量时出错: {error_message}")
                
                retry_count += 1
                
                # 检查是否是配额限制错误
                if "429" in error_message or "Resource has been exhausted" in error_message:
                    # 指数退避重试
                    if retry_count < max_retries:
                        wait_time = base_wait * (2 ** retry_count) + random.uniform(0, 1)
                        print(f"API配额限制，等待 {wait_time:.2f} 秒后重试 ({retry_count}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print("达到最大重试次数，返回随机向量")
                        break
            
            # 如果没有成功返回，等待一小段时间再次尝试
            if retry_count < max_retries:
                wait_time = base_wait * (1.5 ** retry_count) + random.uniform(0, 0.5)
                print(f"将在 {wait_time:.2f} 秒后进行第 {retry_count+1} 次重试...")
                await asyncio.sleep(wait_time)
            else:
                break
                
        # 所有重试都失败，返回随机向量
        print("使用随机向量作为embedding")
        random_embedding = list(np.random.rand(768))  # 始终返回768维随机向量
        
        # 将随机向量保存到缓存，避免为相同文本生成不同的随机向量
        self.embedding_cache[cache_key] = random_embedding
        return random_embedding
        
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 5) -> List[List[float]]:
        """批量生成embedding向量，优化API调用频率
        
        Args:
            texts: 待处理的文本列表
            batch_size: 每批处理的文本数量
            
        Returns:
            embedding向量列表
        """
        results = []
        
        # 优化批次大小 - 根据总数自动调整
        total_texts = len(texts)
        if total_texts > 100:
            # 大量文本时使用更大的批次
            batch_size = min(20, total_texts // 10)
        elif total_texts > 50:
            batch_size = min(10, total_texts // 5)
        
        # 计算所需批次数
        batch_count = (total_texts + batch_size - 1) // batch_size
        print(f"处理 {total_texts} 个文本，分为 {batch_count} 批，每批 {batch_size} 个")
        
        # 记录开始时间
        start_time = time.time()
        processed = 0
        
        # 分批处理
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            print(f"处理批次 {batch_num}/{batch_count}，包含 {len(batch)} 个文本...")
            
            # 创建任务
            tasks = [self.generate_embedding(text) for text in batch]
            
            # 并行执行任务
            embeddings = await asyncio.gather(*tasks)
            results.extend(embeddings)
            
            processed += len(batch)
            
            # 估计剩余时间
            elapsed = time.time() - start_time
            if processed > 0 and elapsed > 0:
                texts_per_second = processed / elapsed
                remaining_texts = total_texts - processed
                estimated_time = remaining_texts / texts_per_second if texts_per_second > 0 else 0
                print(f"进度: {processed}/{total_texts} ({processed/total_texts*100:.1f}%)，"
                      f"预计剩余时间: {estimated_time:.1f} 秒")
            
            # 批次之间添加短暂延迟，避免API限制
            if i + batch_size < total_texts:
                delay = min(2.0, max(0.5, 60 / self.api_rate_limit * batch_size))
                print(f"批次间延迟: {delay:.2f} 秒")
                await asyncio.sleep(delay)
                
        print(f"批量处理完成，总耗时: {time.time() - start_time:.2f} 秒")
        return results
        
    async def generate_completion(self, prompt: str, context: Optional[str] = None, complexity: str = "normal", use_cache: bool = True) -> str:
        """生成文本完成，带缓存、速率限制和重试机制
        
        Args:
            prompt: 提示文本
            context: 可选的上下文
            complexity: 任务复杂度级别 ('simple', 'normal', 'complex')
            use_cache: 是否使用缓存
            
        Returns:
            生成的文本完成
        """
        # 准备包含上下文的完整提示
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        # 使用缓存
        if use_cache:
            import hashlib
            cache_key = hashlib.md5((full_prompt + complexity).encode()).hexdigest()
            if cache_key in self.completion_cache:
                print(f"使用缓存的完成结果，提示: {prompt[:50]}...")
                return self.completion_cache[cache_key]
        
        # 根据任务复杂度选择模型
        model_name = self.model_id
        use_thinking_budget = False
        
        # 设置重试参数
        max_retries = 3
        base_wait_time = 2.0
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 检查速率限制
                await self._check_rate_limit("completion")
                
                # 创建生成模型
                model = genai.GenerativeModel(model_name)
                
                # 调用API生成文本
                response = model.generate_content(full_prompt)
                if not response or not response.text:
                    raise ValueError("API返回了空响应")
                
                result_text = response.text.strip()
                
                # 如果使用缓存，存储结果
                if use_cache:
                    self.completion_cache[cache_key] = result_text
                
                return result_text
                
            except Exception as e:
                error_msg = str(e)
                retry_count += 1
                print(f"文本生成失败 ({retry_count}/{max_retries}): {error_msg}")
                
                if "429" in error_msg or "Resource has been exhausted" in error_msg:
                    # 配额限制错误，应用指数退避
                    if retry_count <= max_retries:
                        wait_time = base_wait_time * (2 ** retry_count) + random.uniform(0, 1)
                        print(f"API配额限制，等待 {wait_time:.2f} 秒后重试...")
                        await asyncio.sleep(wait_time)
                    else:
                        return f"很抱歉，由于API请求限制，无法生成回答。请稍后再试。错误: {error_msg}"
                elif retry_count <= max_retries:
                    # 其他错误，简单重试
                    wait_time = base_wait_time * retry_count + random.uniform(0, 1)
                    print(f"将在 {wait_time:.2f} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    return f"生成回答时出错: {error_msg}"
                    
        # 所有重试都失败
        return "生成回答失败，请稍后再试。"
        
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

    async def intelligent_chunking(self, text, file_type=None):
        """智能分块方法，根据内容和文件类型进行智能分块
        
        参数:
            text: 需要分块的文本内容
            file_type: 文件类型，如'pdf', 'txt'等
            
        返回:
            chunks: 分块后的列表，每个元素为包含content和metadata的字典
        """
        
        chunks = []
        MAX_CHUNK_SIZE = 4000  # 最大块大小
        MIN_CHUNK_SIZE = 500   # 最小块大小
        
        # 特殊处理财务报告或年报
        if file_type == 'pdf' and (
            any(keyword in text.lower() for keyword in ['annual report', 'financial statement', 'financial report', '年报', '财务报表'])
        ):
            print("检测到财务报告或年报，使用特殊分块策略")
            # 特殊处理表格内容
            table_pattern = r'(\s*[-+|]+[-+|]+\s*\n)(?:(?:\s*\|.*\|\s*\n)+)'
            tables = re.findall(table_pattern, text, re.MULTILINE)
            
            # 划分表格和非表格部分
            if tables:
                print(f"检测到{len(tables)}个表格，进行特殊处理")
                # 替换表格为标记
                marked_text = text
                table_markers = []
                for i, table in enumerate(tables):
                    marker = f"[TABLE_{i}]"
                    marked_text = marked_text.replace(table, marker, 1)
                    table_markers.append((marker, table))
                
                # 按章节分块
                section_pattern = r'(\n\s*#+\s+.*?\n|\n\s*[A-Z\u4e00-\u9fa5][A-Z\u4e00-\u9fa5 \t]*\n\s*={3,}|\n\s*[A-Z\u4e00-\u9fa5][A-Z\u4e00-\u9fa5 \t]*\n\s*-{3,})'
                sections = re.split(section_pattern, marked_text)
                
                current_chunk = ""
                current_section_title = "引言"
                
                for section in sections:
                    # 检查是否为章节标题
                    if re.match(section_pattern, '\n' + section.strip(), re.MULTILINE):
                        if current_chunk:
                            # 恢复表格标记为实际表格
                            for marker, table_content in table_markers:
                                if marker in current_chunk:
                                    current_chunk = current_chunk.replace(marker, table_content)
                            
                            chunks.append({
                                "content": current_chunk.strip(),
                                "metadata": {
                                    "strategy": "financial_report_section",
                                    "section": current_section_title
                                }
                            })
                        
                        current_chunk = section
                        current_section_title = section.strip()
                    else:
                        # 检查添加当前部分是否会超过最大块大小
                        if len(current_chunk) + len(section) > MAX_CHUNK_SIZE:
                            # 恢复表格标记为实际表格
                            for marker, table_content in table_markers:
                                if marker in current_chunk:
                                    current_chunk = current_chunk.replace(marker, table_content)
                            
                            chunks.append({
                                "content": current_chunk.strip(),
                                "metadata": {
                                    "strategy": "financial_report_section",
                                    "section": current_section_title
                                }
                            })
                            current_chunk = section
                        else:
                            current_chunk += section
                
                # 添加最后一个块
                if current_chunk:
                    # 恢复表格标记为实际表格
                    for marker, table_content in table_markers:
                        if marker in current_chunk:
                            current_chunk = current_chunk.replace(marker, table_content)
                    
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": {
                            "strategy": "financial_report_section",
                            "section": current_section_title
                        }
                    })
            else:
                # 无表格，按章节分块
                section_pattern = r'(\n\s*#+\s+.*?\n|\n\s*[A-Z\u4e00-\u9fa5][A-Z\u4e00-\u9fa5 \t]*\n\s*={3,}|\n\s*[A-Z\u4e00-\u9fa5][A-Z\u4e00-\u9fa5 \t]*\n\s*-{3,})'
                sections = re.split(section_pattern, text)
                
                current_chunk = ""
                current_section_title = "引言"
                
                for section in sections:
                    # 检查是否为章节标题
                    if re.match(section_pattern, '\n' + section.strip(), re.MULTILINE):
                        if current_chunk:
                            chunks.append({
                                "content": current_chunk.strip(),
                                "metadata": {
                                    "strategy": "financial_report_section",
                                    "section": current_section_title
                                }
                            })
                        
                        current_chunk = section
                        current_section_title = section.strip()
                    else:
                        # 检查添加当前部分是否会超过最大块大小
                        if len(current_chunk) + len(section) > MAX_CHUNK_SIZE:
                            chunks.append({
                                "content": current_chunk.strip(),
                                "metadata": {
                                    "strategy": "financial_report_section",
                                    "section": current_section_title
                                }
                            })
                            current_chunk = section
                        else:
                            current_chunk += section
                
                # 添加最后一个块
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": {
                            "strategy": "financial_report_section",
                            "section": current_section_title
                        }
                    })
        else:
            # 一般文档的分块策略 - 语义分块
            paragraphs = re.split(r'\n\s*\n', text)
            current_chunk = ""
            current_section = "通用文档"
            
            # 检测章节标题模式
            section_heading = re.compile(r'^(#+\s+|\d+(\.\d+)*\s+|[A-Z\u4e00-\u9fa5][A-Z\u4e00-\u9fa5 \t]*\n\s*[-=]{3,})')
            
            for para in paragraphs:
                # 检测是否为章节标题
                if section_heading.search(para):
                    if current_chunk and len(current_chunk) >= MIN_CHUNK_SIZE:
                        chunks.append({
                            "content": current_chunk.strip(),
                            "metadata": {
                                "strategy": "semantic_paragraph",
                                "section": current_section
                            }
                        })
                        current_chunk = ""
                    
                    current_section = para.strip()
                
                # 检查添加当前段落是否会超过最大块大小
                if len(current_chunk) + len(para) > MAX_CHUNK_SIZE:
                    if current_chunk:
                        chunks.append({
                            "content": current_chunk.strip(),
                            "metadata": {
                                "strategy": "semantic_paragraph",
                                "section": current_section
                            }
                        })
                    current_chunk = para + "\n\n"
                else:
                    current_chunk += para + "\n\n"
            
            # 添加最后一个块
            if current_chunk and len(current_chunk) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": {
                        "strategy": "semantic_paragraph",
                        "section": current_section
                    }
                })
            elif current_chunk:
                # 如果最后一个块太小，尝试合并到前一个块
                if chunks:
                    last_chunk = chunks.pop()
                    combined_content = last_chunk["content"] + "\n\n" + current_chunk
                    chunks.append({
                        "content": combined_content.strip(),
                        "metadata": last_chunk["metadata"]
                    })
                else:
                    # 没有前一个块可合并，创建新块
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": {
                            "strategy": "semantic_paragraph",
                            "section": current_section
                        }
                    })
        
        # 后处理 - 确保每个块都符合大小限制
        processed_chunks = []
        for chunk in chunks:
            content = chunk["content"]
            if len(content) > MAX_CHUNK_SIZE:
                # 切分大块
                sentences = re.split(r'(?<=[.!?])\s+', content)
                sub_chunk = ""
                for sentence in sentences:
                    if len(sub_chunk) + len(sentence) < MAX_CHUNK_SIZE:
                        sub_chunk += sentence + " "
                    else:
                        if sub_chunk:
                            processed_chunks.append({
                                "content": sub_chunk.strip(),
                                "metadata": chunk["metadata"]
                            })
                        sub_chunk = sentence + " "
                
                if sub_chunk:
                    processed_chunks.append({
                        "content": sub_chunk.strip(),
                        "metadata": chunk["metadata"]
                    })
            else:
                processed_chunks.append(chunk)
        
        return processed_chunks
