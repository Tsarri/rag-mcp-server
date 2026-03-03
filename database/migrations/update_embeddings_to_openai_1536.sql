-- Migration: Replace Sentence Transformers 384-dim embeddings with OpenAI 1536-dim
-- Run this in Supabase SQL Editor before deploying the updated backend

-- Drop existing vector documents and function (384-dim vectors are incompatible with 1536-dim)
drop function if exists match_documents;
drop table if exists vector_documents;

-- Recreate table with 1536-dimensional vectors (OpenAI text-embedding-3-small)
create table vector_documents (
    id bigserial primary key,
    content text not null,
    embedding vector(1536),
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default now()
);

-- Recreate similarity search function for 1536-dim vectors
create or replace function match_documents (
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
returns table (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
language sql stable
as $$
    select
        vector_documents.id,
        vector_documents.content,
        vector_documents.metadata,
        1 - (vector_documents.embedding <=> query_embedding) as similarity
    from vector_documents
    where 1 - (vector_documents.embedding <=> query_embedding) > match_threshold
    order by similarity desc
    limit match_count;
$$;

-- Index for fast similarity search
create index on vector_documents using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);
