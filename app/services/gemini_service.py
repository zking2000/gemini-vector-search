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

# 配置Google Cloud
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = "us-central1"  # 可根据需要调整
API_KEY = os.getenv("GOOGLE_API_KEY")

# 初始化Google AI
if API_KEY:
    genai.configure(api_key=API_KEY)

# 初始化Vertex AI
aiplatform.init(project=PROJECT_ID, location=REGION)

class GeminiService:
    """Gemini模型服务封装"""
    
    def __init__(self):
        self.model_id = "gemini-2.0-flash"
        self.embedding_model_name = "models/gemini-embedding-exp-03-07"  # 更新为正确的模型名称格式
        # 添加简单的嵌入缓存，用于避免重复计算
        self.embedding_cache = {}
        
    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本的嵌入向量"""
        import time
        import random
        import hashlib
        
        # 如果文本为空，返回全零向量
        if not text.strip():
            return [0.0] * 768  # 保持一致的768维
            
        # 使用文本的哈希作为缓存键
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # 检查缓存
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # 最大重试次数
        max_retries = 3
        # 初始等待时间（秒）
        base_wait_time = 2
        
        for retry in range(max_retries + 1):
            try:
                # 使用正确的嵌入模型API调用
                result = genai.embed_content(
                    model="models/gemini-embedding-exp-03-07",
                    content=text,
                    task_type="SEMANTIC_SIMILARITY"
                )
                
                # 正确提取嵌入向量
                embedding = None
                
                # Google AI API返回的结构可能是字典，需要正确提取
                if isinstance(result, dict):
                    if 'embedding' in result:
                        embedding = result['embedding']
                    elif 'embeddings' in result:
                        embedding = result['embeddings'][0]
                    elif 'values' in result:
                        embedding = result['values']
                    else:
                        # 检查嵌套结构
                        print(f"嵌入结果结构: {result.keys()}")
                else:
                    # 尝试使用属性访问
                    try:
                        embedding = result.embedding
                    except AttributeError:
                        try:
                            embedding = result.embeddings[0]
                        except (AttributeError, IndexError):
                            print(f"嵌入结果类型: {type(result)}")
                
                if embedding:
                    # 保证维度一致 - 截断或填充到768维
                    embedding_length = len(embedding)
                    if embedding_length != 768:
                        print(f"嵌入向量维度不是768 ({embedding_length})，进行调整")
                        if embedding_length > 768:
                            # 截断到768维
                            embedding = embedding[:768]
                        else:
                            # 填充到768维
                            embedding = embedding + [0.0] * (768 - embedding_length)
                    
                    # 保存到缓存
                    self.embedding_cache[cache_key] = embedding
                    return embedding
                
            except Exception as e:
                error_message = str(e)
                print(f"生成嵌入向量时出错: {error_message}")
                
                # 检查是否是配额限制错误
                if "429" in error_message or "Resource has been exhausted" in error_message:
                    if retry < max_retries:
                        # 计算等待时间（指数退避）
                        wait_time = base_wait_time * (2 ** retry) + random.uniform(0, 1)
                        print(f"API配额限制，等待 {wait_time:.2f} 秒后重试 ({retry+1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("达到最大重试次数，使用随机向量")
                
                # 对于其他错误或重试失败后，使用随机向量
                break
                
        # 所有重试都失败，返回随机向量 - 使用固定768维度
        print("使用随机向量作为嵌入向量")
        random_embedding = list(np.random.rand(768))  # 始终返回768维随机向量
        
        # 保存随机向量到缓存，避免对同一文本重复生成不同的随机向量
        self.embedding_cache[cache_key] = random_embedding
        return random_embedding
        
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 5) -> List[List[float]]:
        """批量生成文本的嵌入向量，减少API调用次数"""
        results = []
        # 将输入分成多个批次
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            print(f"处理嵌入批次 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}, 大小: {len(batch)}")
            
            # 并行处理批次中的每个文本
            import asyncio
            embeddings = await asyncio.gather(*[self.generate_embedding(text) for text in batch])
            results.extend(embeddings)
            
            # 在批次之间添加短暂延迟以避免超出API限制
            if i + batch_size < len(texts):
                await asyncio.sleep(1)
                
        return results
        
    async def generate_completion(self, prompt: str, context: Optional[str] = None) -> str:
        """使用Gemini生成文本补全"""
        model = genai.GenerativeModel(self.model_id)
        
        if context:
            prompt = f"{context}\n\n{prompt}"
            
        response = model.generate_content(prompt)
        return response.text
        
    async def prepare_context(self, query: str, similar_docs: List[Dict[str, Any]]) -> str:
        """准备提示上下文，包含相关文档"""
        # 检测是否为中文查询
        is_chinese_query = any('\u4e00' <= c <= '\u9fff' for c in query)
        
        if is_chinese_query:
            context = "以下是与你的查询相关的文档内容：\n\n"
            
            # 为中文查询添加额外指导
            if "道教" in query or "老子" in query:
                context += """参考资料中包含关于道教的信息。请仔细阅读并提取相关内容来回答问题。
注意道教的历史发展、主要人物（如老子、张道陵等）以及核心概念（如道、德、无为等）。
如果问题是关于道教创始人，请特别注意关于老子、张道陵和五斗米道的内容。\n\n"""
            elif "佛教" in query or "释迦牟尼" in query:
                context += """参考资料中包含关于佛教的信息。请仔细阅读并提取相关内容来回答问题。
注意佛教的历史发展、主要人物（如释迦牟尼、菩萨等）以及核心概念（如四谛、八正道等）。
如果问题是关于佛教创始人，请特别关注释迦牟尼佛（悉达多·乔达摩）的内容。\n\n"""
        else:
            context = "以下是与你的查询相关的信息：\n\n"
        
        # 按相似度排序，确保最相关的文档在前面
        sorted_docs = sorted(similar_docs, key=lambda x: x.get("similarity", 0), reverse=True)
        
        # 分析文档内容以检测是否有特别相关的内容
        has_highly_relevant = False
        for doc in sorted_docs:
            similarity = doc.get("similarity", 0)
            content = doc.get("content", "")
            if similarity > 0.7 or any(term in content for term in ["道教", "老子", "佛教", "释迦牟尼"] if term in query):
                has_highly_relevant = True
                break
        
        # 添加文档内容到上下文
        for i, doc in enumerate(sorted_docs):
            # 获取文档元数据，尤其是来源信息
            metadata = doc.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            doc_id = doc.get("id", "")
            # 获取来源，尝试多个可能的字段
            source = (
                metadata.get("source", "") or 
                doc.get("source", "") or 
                metadata.get("pdf_filename", "") or 
                metadata.get("filename", "")
            )
            
            if not source and doc_id:
                source = f"文档ID: {doc_id}"
            elif not source:
                source = f"文档片段 #{i+1}"
                
            # 获取块信息
            chunk_info = ""
            if "chunk" in metadata and "total_chunks" in metadata:
                chunk_info = f"(第{metadata['chunk']}/{metadata['total_chunks']}块)"
            
            # 获取相似度
            similarity = doc.get("similarity", 0)
            similarity_info = f"相似度: {similarity:.2f}" if similarity else ""
            
            # 添加完整的文档内容，带有更好的格式
            content = doc.get("content", "").strip()
            if content:
                document_header = f"文档 {i+1} {chunk_info} {similarity_info}:"
                if is_chinese_query:
                    # 为中文内容添加更简洁的分隔，避免使用大量的"="符号
                    context += f"{document_header}\n---\n{content}\n---\n\n"
                else:
                    context += f"{document_header}\n{content}\n\n"
        
        # 为中文查询添加特定指示
        if is_chinese_query:
            if has_highly_relevant:
                # 有高度相关的内容
                context += """请基于上述文档内容回答以下问题。请特别注意：
1. 从文档中提取与问题最相关的信息
2. 组织信息形成有逻辑、有条理的回答
3. 如果文档中信息不足或有矛盾，请明确指出
4. 以用户能够理解的方式解释专业概念
5. 首先确定问题的核心，然后有针对性地从文档中寻找答案"""
            else:
                # 没有高度相关的内容
                context += """请基于上述文档内容回答以下问题，如果文档中没有足够信息，请明确指出：
1. 优先使用文档中的信息回答问题
2. 明确指出哪些部分是从文档中提取的，哪些是基于一般知识补充的
3. 如果文档中完全没有相关信息，请明确告知用户"""
        else:
            context += "请基于上述信息回答以下问题："
            
        return context
        
    async def determine_chunking_strategy(self, text_sample: str, file_type: str) -> Tuple[int, int, List[Dict]]:
        """使用Gemini分析文档内容，确定最佳分块策略"""
        model = genai.GenerativeModel(self.model_id)
        
        # 限制样本大小以避免超出模型上下文窗口
        text_sample = text_sample[:10000] if len(text_sample) > 10000 else text_sample
        
        prompt = f"""
分析以下{file_type.upper()}文档的内容，并确定最佳的文本分块策略。

文档样本内容开始:
{text_sample}
文档样本内容结束

任务:
分析文档结构和内容，推荐最佳分块策略。

请以JSON格式回复，不要使用markdown格式或代码块，直接返回JSON对象:
{{"strategy": "fixed_size", "chunk_size": 数字, "overlap": 数字}}

例如:
{{"strategy": "fixed_size", "chunk_size": 1500, "overlap": 300}}
"""
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # 删除markdown代码块标记
            response_text = re.sub(r'```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```', '', response_text)
            
            print(f"处理后的JSON响应: {response_text}")
            
            # 提取JSON对象
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result_str = json_match.group(0)
                try:
                    result = json.loads(result_str)
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}, 原始文本: {result_str}")
                    return 1000, 200, []
            else:
                print(f"无法从响应中提取JSON: {response_text}")
                return 1000, 200, []
            
            # 获取分块参数
            chunk_size = result.get("chunk_size", 1000)
            overlap = result.get("overlap", 200)
            custom_chunks = result.get("custom_chunks", [])
            
            # 确保chunk_size和overlap不为None
            if chunk_size is None:
                chunk_size = 1000
            if overlap is None:
                overlap = 200
                
            print(f"成功解析分块策略: chunk_size={chunk_size}, overlap={overlap}")
            return chunk_size, overlap, custom_chunks
        except Exception as e:
            print(f"确定分块策略时出错: {e}")
            # 返回默认值
            return 1000, 200, []
    
    async def intelligent_chunking(self, text: str, file_type: str) -> List[Dict]:
        """智能分块处理
        
        Args:
            text: 要分块的完整文本
            file_type: 文件类型
            
        Returns:
            chunks: 包含内容和元数据的分块列表
        """
        # 获取前10000个字符作为样本
        text_sample = text[:10000]
        
        # 确定分块策略
        chunk_size, overlap, custom_chunks = await self.determine_chunking_strategy(text_sample, file_type)
        
        # 如果模型返回了自定义分块，直接使用
        if custom_chunks:
            return custom_chunks
        
        # 否则使用推荐的chunk_size和overlap进行分块
        chunks = []
        sentences = text.replace('\n', ' ').split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                chunks.append({
                    "content": current_chunk,
                    "metadata": {}
                })
                # 保留一些重叠，以维持上下文连贯性
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk += sentence + ". "
        
        # 添加最后一个块
        if current_chunk:
            chunks.append({
                "content": current_chunk,
                "metadata": {}
            })
        
        return chunks 
