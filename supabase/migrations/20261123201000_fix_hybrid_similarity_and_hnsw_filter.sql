-- ==============================================================================
-- MIGRATION: Fix hybrid search HNSW post-filter starvation and outer similarity
-- calculation, and calibrate synthetic_penalty to 0.60 so exact synthetic article
-- queries still surface for the synthetic-template-guardrail while real articles
-- dominate conceptual and case-based legal queries.
-- ==============================================================================

DROP FUNCTION IF EXISTS public.match_legal_chunks_hybrid(TEXT, VECTOR(1536), INT, FLOAT, FLOAT, INT, FLOAT);

CREATE OR REPLACE FUNCTION public.match_legal_chunks_hybrid(
    query_text TEXT,
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    full_text_weight FLOAT DEFAULT 1.0,
    vector_weight FLOAT DEFAULT 1.0,
    rrf_k INT DEFAULT 60,
    synthetic_penalty FLOAT DEFAULT 0.60
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
WITH parsed_query AS (
    SELECT
        CASE
            WHEN NULLIF(plainto_tsquery('spanish', coalesce(query_text, ''))::text, '') IS NULL
                THEN NULL::tsquery
            ELSE to_tsquery(
                'spanish',
                replace(plainto_tsquery('spanish', query_text)::text, ' & ', ' | ')
            )
        END AS tsq
),
vector_all AS (
    SELECT
        lc.id,
        ROW_NUMBER() OVER (ORDER BY lc.embedding <=> query_embedding) AS rank
    FROM public.legal_chunks lc
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count * 4
),
vector_real AS (
    -- Adding +0 prevents pgvector HNSW ef_search starvation when real rows are ~1% of table
    SELECT
        lc.id,
        ROW_NUMBER() OVER (ORDER BY (lc.embedding <=> query_embedding) + 0) AS rank
    FROM public.legal_chunks lc
    WHERE COALESCE((lc.metadata->>'is_synthetic_template')::boolean, false) = false
    ORDER BY (lc.embedding <=> query_embedding) + 0
    LIMIT match_count * 2
),
vector_search AS (
    SELECT
        id,
        MIN(rank) AS rank
    FROM (
        SELECT * FROM vector_all
        UNION ALL
        SELECT * FROM vector_real
    ) v
    GROUP BY id
),
text_all AS (
    SELECT
        lc.id,
        ROW_NUMBER() OVER (ORDER BY ts_rank_cd(lc.tsv_content, pq.tsq) DESC) AS rank
    FROM public.legal_chunks lc
    CROSS JOIN parsed_query pq
    WHERE pq.tsq IS NOT NULL
      AND lc.tsv_content @@ pq.tsq
    ORDER BY ts_rank_cd(lc.tsv_content, pq.tsq) DESC
    LIMIT match_count * 4
),
text_real AS (
    SELECT
        lc.id,
        ROW_NUMBER() OVER (ORDER BY ts_rank_cd(lc.tsv_content, pq.tsq) DESC) AS rank
    FROM public.legal_chunks lc
    CROSS JOIN parsed_query pq
    WHERE pq.tsq IS NOT NULL
      AND COALESCE((lc.metadata->>'is_synthetic_template')::boolean, false) = false
      AND lc.tsv_content @@ pq.tsq
    ORDER BY ts_rank_cd(lc.tsv_content, pq.tsq) DESC
    LIMIT match_count * 2
),
text_search AS (
    SELECT
        id,
        MIN(rank) AS rank
    FROM (
        SELECT * FROM text_all
        UNION ALL
        SELECT * FROM text_real
    ) t
    GROUP BY id
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
    -- Always compute exact cosine similarity on candidate rows (never default to 0.0)
    (1 - (lc.embedding <=> query_embedding))::FLOAT AS semantic_similarity,
    (
        (
            coalesce(1.0 / (rrf_k + vs.rank), 0.0) * vector_weight +
            coalesce(1.0 / (rrf_k + ts.rank), 0.0) * full_text_weight
        ) * CASE
            WHEN COALESCE((lc.metadata->>'is_synthetic_template')::boolean, false)
                THEN synthetic_penalty
            ELSE 1.0
        END
    )::FLOAT AS combined_score
FROM public.legal_chunks lc
LEFT JOIN vector_search vs ON lc.id = vs.id
LEFT JOIN text_search ts ON lc.id = ts.id
WHERE vs.id IS NOT NULL OR ts.id IS NOT NULL
ORDER BY combined_score DESC
LIMIT match_count;
$$;
