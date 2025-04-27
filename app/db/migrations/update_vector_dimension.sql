-- 更新向量维度为 768
ALTER TABLE documents ALTER COLUMN embedding TYPE vector(768); 