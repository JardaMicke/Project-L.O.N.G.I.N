-- Povolení rozšíření pgvector pro práci s vektory
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabulka pro ukládání vektorových embeddingů a jejich metadat
CREATE TABLE IF NOT EXISTS vector_embeddings (
    id UUID PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabulka pro zaznamenávání úspěšně dokončených pracovních postupů (flow)
CREATE TABLE IF NOT EXISTS successful_flows (
    id UUID PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    flow_details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabulka pro obecné ukládání klíč-hodnota
CREATE TABLE IF NOT EXISTS key_value_store (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB,
    expires_at TIMESTAMPTZ
);
