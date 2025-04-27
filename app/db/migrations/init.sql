-- 安装 pgvector 扩展
DROP EXTENSION IF EXISTS vector CASCADE;
CREATE EXTENSION vector;

-- 删除现有的表（如果存在）
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- 创建 documents 表
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    doc_metadata TEXT,
    embedding vector(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chunking_strategy VARCHAR(50)
);

-- 创建 document_chunks 表
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 