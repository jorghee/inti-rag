-- ==============================================================================
-- MIGRATION: Add JSONB metadata column to legal_chunks and expose it in hybrid RPC
-- Uses structural article_number_raw whitelist for one-time backfill of existing
-- CODIGO_CIVIL_1984 rows; future ingestions set metadata.is_synthetic_template directly.
-- ==============================================================================

ALTER TABLE public.legal_chunks
ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Structural backfill for rows ingested prior to metadata column creation
UPDATE public.legal_chunks
SET metadata = jsonb_set(
    COALESCE(metadata, '{}'::jsonb),
    '{is_synthetic_template}',
    to_jsonb(
        statute_code = 'CODIGO_CIVIL_1984'
        AND article_number_raw NOT IN (
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            '1', '2', '140', '219', '923', '949', '1351', '1529',
            '1969', '1970', '2001', '2122'
        )
    )
)
WHERE NOT (COALESCE(metadata, '{}'::jsonb) ? 'is_synthetic_template');

DROP FUNCTION IF EXISTS public.match_legal_chunks_hybrid(TEXT, VECTOR(1536), INT, FLOAT, FLOAT, INT);

CREATE OR REPLACE FUNCTION public.match_legal_chunks_hybrid(
    query_text TEXT,
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    full_text_weight FLOAT DEFAULT 1.0,
    vector_weight FLOAT DEFAULT 1.0,
    rrf_k INT DEFAULT 60
)
RETURNS TABLE (
    id UUID,
    statute_code VARCHAR,
    statutory_hierarchy TEXT,
    article_number INT,
    article_number_raw VARCHAR,
    raw_content TEXT,
    official_spij_url TEXT,
    metadata JSONB,
    semantic_similarity FLOAT,
    combined_score FLOAT
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
WITH vector_search AS (
    SELECT
        lc.id,
        1 - (lc.embedding <=> query_embedding) AS sim,
        ROW_NUMBER() OVER (ORDER BY lc.embedding <=> query_embedding) AS rank
    FROM public.legal_chunks lc
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count * 3
),
text_search AS (
    SELECT
        lc.id,
        ts_rank_cd(lc.tsv_content, plainto_tsquery('spanish', query_text)) AS rank_score,
        ROW_NUMBER() OVER (ORDER BY ts_rank_cd(lc.tsv_content, plainto_tsquery('spanish', query_text)) DESC) AS rank
    FROM public.legal_chunks lc
    WHERE lc.tsv_content @@ plainto_tsquery('spanish', query_text)
    ORDER BY rank_score DESC
    LIMIT match_count * 3
)
SELECT
    lc.id,
    lc.statute_code,
    lc.statutory_hierarchy,
    lc.article_number,
    lc.article_number_raw,
    lc.raw_content,
    lc.official_spij_url,
    lc.metadata,
    coalesce(vs.sim, 0.0)::FLOAT AS semantic_similarity,
    (
        coalesce(1.0 / (rrf_k + vs.rank), 0.0) * vector_weight +
        coalesce(1.0 / (rrf_k + ts.rank), 0.0) * full_text_weight
    )::FLOAT AS combined_score
FROM public.legal_chunks lc
LEFT JOIN vector_search vs ON lc.id = vs.id
LEFT JOIN text_search ts ON lc.id = ts.id
WHERE vs.id IS NOT NULL OR ts.id IS NOT NULL
ORDER BY combined_score DESC
LIMIT match_count;
$$;
