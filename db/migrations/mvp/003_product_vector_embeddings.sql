-- Product Plane: Vector embeddings table for Context Service
-- Uses pgvector extension for similarity search

CREATE TABLE IF NOT EXISTS app.vector_embeddings (
    embedding_id TEXT PRIMARY KEY,
    tenant_id TEXT,
    content_type TEXT NOT NULL,  -- e.g., 'context_snapshot', 'policy_rule', etc.
    content_id TEXT NOT NULL,
    embedding vector(1536),  -- Default dimension; adjust based on embedding model
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vector_embeddings_tenant ON app.vector_embeddings(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_content ON app.vector_embeddings(content_type, content_id);
-- HNSW index for vector similarity search (requires pgvector)
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_hnsw ON app.vector_embeddings USING hnsw (embedding vector_cosine_ops);

COMMENT ON TABLE app.vector_embeddings IS 'Vector embeddings for Context Service similarity search. Uses pgvector extension.';

