-- ==============================================================================
-- MIGRATION: Improve hybrid search recall (disjunctive Spanish tsquery + real-first
-- candidate union + synthetic template ranking penalty).
-- Leaves previous migrations untouched.
-- ==============================================================================

DROP FUNCTION IF EXISTS public.match_legal_chunks_hybrid(TEXT, VECTOR(1536), INT, FLOAT, FLOAT, INT);
DROP FUNCTION IF EXISTS public.match_legal_chunks_hybrid(TEXT, VECTOR(1536), INT, FLOAT, FLOAT, INT, FLOAT);

CREATE OR REPLACE FUNCTION public.match_legal_chunks_hybrid(
    query_text TEXT,
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    full_text_weight FLOAT DEFAULT 1.0,
    vector_weight FLOAT DEFAULT 1.0,
    rrf_k INT DEFAULT 60,
    synthetic_penalty FLOAT DEFAULT 0.35
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
    -- Convert Spanish plainto_tsquery lexemes from AND to OR so natural-language
    -- legal questions match partial term overlap and rank by coverage (ts_rank_cd).
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
        1 - (lc.embedding <=> query_embedding) AS sim,
        ROW_NUMBER() OVER (ORDER BY lc.embedding <=> query_embedding) AS rank
    FROM public.legal_chunks lc
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count * 4
),
vector_real AS (
    SELECT
        lc.id,
        1 - (lc.embedding <=> query_embedding) AS sim,
        ROW_NUMBER() OVER (ORDER BY lc.embedding <=> query_embedding) AS rank
    FROM public.legal_chunks lc
    WHERE COALESCE((lc.metadata->>'is_synthetic_template')::boolean, false) = false
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count * 2
),
vector_search AS (
    SELECT
        id,
        MAX(sim) AS sim,
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
        ts_rank_cd(lc.tsv_content, pq.tsq) AS rank_score,
        ROW_NUMBER() OVER (ORDER BY ts_rank_cd(lc.tsv_content, pq.tsq) DESC) AS rank
    FROM public.legal_chunks lc
    CROSS JOIN parsed_query pq
    WHERE pq.tsq IS NOT NULL
      AND lc.tsv_content @@ pq.tsq
    ORDER BY rank_score DESC
    LIMIT match_count * 4
),
text_real AS (
    SELECT
        lc.id,
        ts_rank_cd(lc.tsv_content, pq.tsq) AS rank_score,
        ROW_NUMBER() OVER (ORDER BY ts_rank_cd(lc.tsv_content, pq.tsq) DESC) AS rank
    FROM public.legal_chunks lc
    CROSS JOIN parsed_query pq
    WHERE pq.tsq IS NOT NULL
      AND COALESCE((lc.metadata->>'is_synthetic_template')::boolean, false) = false
      AND lc.tsv_content @@ pq.tsq
    ORDER BY rank_score DESC
    LIMIT match_count * 2
),
text_search AS (
    SELECT
        id,
        MAX(rank_score) AS rank_score,
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
    coalesce(vs.sim, 0.0)::FLOAT AS semantic_similarity,
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
