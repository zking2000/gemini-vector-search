import os
import sys
import json
import asyncio
from pathlib import Path
from sqlalchemy import text

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.db.database import get_db
from app.services.vector_service import VectorService
from app.models.vector_models import Document

# 加载环境变量
load_dotenv()

async def test_vector_operations():
    """测试向量数据库的基本操作，包括添加文档和相似度搜索"""
    print("开始测试向量数据库操作...")
    
    vector_service = VectorService()
    
    # 测试文档
    test_documents = [
        {
            "content": "人工智能是计算机科学的一个分支，它致力于创造能够执行通常需要人类智能的任务的系统。",
            "metadata": {"source": "AI介绍", "category": "技术"}
        },
        {
            "content": "机器学习是人工智能的一个子领域，它使用统计技术使计算机系统能够从数据中学习，而无需明确编程。",
            "metadata": {"source": "ML介绍", "category": "技术"}
        },
        {
            "content": "深度学习是机器学习的一种方法，它使用多层神经网络来模拟人脑的学习过程。",
            "metadata": {"source": "DL介绍", "category": "技术"}
        },
        {
            "content": "自然语言处理是人工智能的一个分支，专注于使计算机能够理解、解释和生成人类语言。",
            "metadata": {"source": "NLP介绍", "category": "技术"}
        },
        {
            "content": "计算机视觉是一个跨学科领域，专注于使计算机能够从数字图像或视频中获取高级理解。",
            "metadata": {"source": "CV介绍", "category": "技术"}
        }
    ]
    
    # 获取数据库会话
    db = next(get_db())

    try:
        # 添加测试文档
        print("\n添加测试文档到向量数据库...")
        doc_ids = []
        for doc in test_documents:
            document = await vector_service.add_document(
                db=db, 
                content=doc["content"], 
                metadata=doc["metadata"]
            )
            doc_ids.append(document.id)
            print(f"添加文档 ID: {document.id}, 内容: {doc['content'][:50]}...")
        
        # 执行相似度搜索
        print("\n执行相似度搜索...")
        query = "神经网络和深度学习"
        results = await vector_service.search_similar(db=db, query=query, limit=3)
        
        print(f"\n查询: '{query}'")
        print(f"找到 {len(results)} 个相似文档:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 文档 ID: {result['id']}")
            print(f"   标题/内容: {result['title']}")
            if result['title'] != result['content']:
                print(f"   内容: {result['content']}")
            print(f"   元数据: {result['metadata']}")
            print(f"   相似度: {result['similarity']:.4f}")
        
        print("\n查询数据库中的原始文档...");
        # 查询数据库中存储的文档信息
        result_ids = [result['id'] for result in results]
        for doc_id in result_ids:
            try:
                # 使用SQL直接查询以避免ORM模型字段不匹配的问题
                query = f"SELECT id, title, doc_metadata FROM documents WHERE id = {doc_id}"
                doc_row = db.execute(text(query)).fetchone()
                if doc_row:
                    print(f"\n文档 ID: {doc_row.id}")
                    print(f"   标题: {doc_row.title}")
                    # 尝试解析元数据
                    try:
                        metadata = json.loads(doc_row.doc_metadata) if isinstance(doc_row.doc_metadata, str) else doc_row.doc_metadata
                        # 不显示嵌入向量以简化输出
                        if '_embedding' in metadata:
                            embedding_length = len(metadata['_embedding'])
                            metadata['_embedding'] = f"[向量，维度: {embedding_length}]"
                        print(f"   元数据: {metadata}")
                    except Exception as e:
                        print(f"   元数据解析错误: {e}")
            except Exception as e:
                print(f"查询文档 {doc_id} 时出错: {e}")
        
        print("\n向量数据库测试完成!")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # 运行异步测试函数
    asyncio.run(test_vector_operations()) 