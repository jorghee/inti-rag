-- ==============================================================================
-- INTI - ASISTENTE JURÍDICO INTELIGENTE (UNSA)
-- ESQUEMA INTEGRAL UNIFICADO DE PRODUCCIÓN (ALINEADO A ARQUITECTURA OFICIAL Y PIPELINE)
-- Sprint 1 (TASK-05.1) y Sprint 2 (HU-03 Fase 2)
-- Autor: Rafael Diego Nina Calizaya (@DrN25) - QA & Database Lead
-- Conforme a: docs/architecture/data-model.md y ingestion/chunker.py (PR #3)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 0. LIMPIEZA TOTAL PREVIA (DROP CASCADE DE TABLAS EXISTENTES)
-- Elimina tablas previas y artefactos obsoletos (como legal_articles) de forma limpia
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS public.citation_refs CASCADE;
DROP TABLE IF EXISTS public.query_logs CASCADE;
DROP TABLE IF EXISTS public.query_sessions CASCADE;
DROP TABLE IF EXISTS public.legal_chunks CASCADE;
DROP TABLE IF EXISTS public.legal_articles CASCADE;
DROP TABLE IF EXISTS public.legal_statutes CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;
DROP TABLE IF EXISTS public.roles CASCADE;

DROP FUNCTION IF EXISTS public.match_legal_chunks_hybrid(TEXT, VECTOR(1536), INT, FLOAT, FLOAT, INT);
DROP FUNCTION IF EXISTS public.match_legal_chunks(VECTOR(1536), FLOAT, INT);
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;

-- ------------------------------------------------------------------------------
-- 1. HABILITAR EXTENSIONES DEL SISTEMA
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector para embeddings densos 1536d
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 2. TABLA DE ROLES INSTITUCIONALES (RBAC)
-- ------------------------------------------------------------------------------
CREATE TABLE public.roles (
    name VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.roles (name, display_name, description) VALUES
    ('student', 'Estudiante de Derecho', 'Estudiante de pregrado o posgrado de la Facultad de Derecho UNSA con acceso a consultas y biblioteca civil.'),
    ('docent', 'Docente Universitario', 'Catedrático de la Facultad de Derecho con acceso a consultas y validación doctrinal.'),
    ('faculty', 'Personal Administrativo', 'Personal administrativo o directivo de la Facultad de Derecho.'),
    ('admin', 'Administrador del Sistema', 'Administrador con acceso a métricas de ingestión y auditoría del sistema Inti.')
ON CONFLICT (name) DO UPDATE 
SET display_name = EXCLUDED.display_name, description = EXCLUDED.description;

ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "roles_read_policy" ON public.roles FOR SELECT TO authenticated USING (true);

-- ------------------------------------------------------------------------------
-- 3. PERFILES DE USUARIO (public.profiles)
-- Vinculado a auth.users con restricción estricta de dominio @unsa.edu.pe
-- ------------------------------------------------------------------------------
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'student' REFERENCES public.roles(name) ON UPDATE CASCADE,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_unsa_email CHECK (email LIKE '%@unsa.edu.pe')
);

CREATE INDEX idx_profiles_email ON public.profiles(email);
CREATE INDEX idx_profiles_role ON public.profiles(role);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_policy" ON public.profiles
    FOR SELECT TO authenticated
    USING (id = (SELECT auth.uid()));

CREATE POLICY "profiles_update_policy" ON public.profiles
    FOR UPDATE TO authenticated
    USING (id = (SELECT auth.uid()))
    WITH CHECK (
        id = (SELECT auth.uid()) 
        AND email = (SELECT email FROM auth.users WHERE id = (SELECT auth.uid()))
        AND role = (SELECT role FROM public.profiles WHERE id = (SELECT auth.uid()))
    );

-- Trigger de auto-aprovisionamiento seguro en auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    extracted_full_name TEXT;
    extracted_role TEXT;
BEGIN
    IF NEW.email NOT LIKE '%@unsa.edu.pe' THEN
        RAISE EXCEPTION 'Acceso denegado: El correo % no pertenece al dominio institucional @unsa.edu.pe', NEW.email;
    END IF;

    extracted_full_name := COALESCE(
        NEW.raw_user_meta_data->>'full_name',
        split_part(NEW.email, '@', 1)
    );

    extracted_role := COALESCE(
        NEW.raw_user_meta_data->>'role',
        'student'
    );

    IF extracted_role NOT IN ('student', 'docent', 'faculty', 'admin') THEN
        extracted_role := 'student';
    END IF;

    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (NEW.id, NEW.email, extracted_full_name, extracted_role)
    ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        updated_at = NOW();

    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ------------------------------------------------------------------------------
-- 4. TABLA DE NORMAS (public.legal_statutes)
-- Metadatos de la norma oficial promulgada
-- ------------------------------------------------------------------------------
CREATE TABLE public.legal_statutes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(100) UNIQUE NOT NULL,
    official_name VARCHAR(255) NOT NULL,
    promulgation_date DATE,
    valid_from DATE,
    official_source_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.legal_statutes (code, official_name, promulgation_date, valid_from, official_source_url)
VALUES (
    'CODIGO_CIVIL_1984',
    'Código Civil Peruano de 1984 (Decreto Legislativo Nº 295)',
    '1984-07-24',
    '1984-11-14',
    'https://spij.minjus.gob.pe'
) ON CONFLICT (code) DO NOTHING;

ALTER TABLE public.legal_statutes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "legal_statutes_read" ON public.legal_statutes FOR SELECT TO authenticated USING (true);

-- ------------------------------------------------------------------------------
-- 5. TABLA VECTORIAL DE CHUNKS (public.legal_chunks)
-- Alineada 100% con ingestion/chunker.py y docs/architecture/data-model.md
-- Incluye columna TSVECTOR autogenerada para búsqueda híbrida (RRF)
-- ------------------------------------------------------------------------------
CREATE TABLE public.legal_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    statute_code VARCHAR(100) NOT NULL DEFAULT 'CODIGO_CIVIL_1984' REFERENCES public.legal_statutes(code) ON UPDATE CASCADE,
    statutory_hierarchy TEXT NOT NULL,
    article_number INT NOT NULL,
    article_number_raw VARCHAR(50) NOT NULL,
    raw_content TEXT NOT NULL,
    official_spij_url TEXT,
    composite_text TEXT NOT NULL,
    sub_chunk_index INT NOT NULL DEFAULT 0,
    total_words INT NOT NULL DEFAULT 0,
    embedding VECTOR(1536) NOT NULL,
    tsv_content TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('spanish', coalesce(statutory_hierarchy, '') || ' ' || coalesce(raw_content, ''))
    ) STORED,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_statute_article_sub UNIQUE (statute_code, article_number_raw, sub_chunk_index)
);

-- Índice HNSW optimizado para distancia coseno (<=>)
CREATE INDEX idx_legal_chunks_embedding 
ON public.legal_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índice GIN para búsqueda de texto completo en español (BM25 lexical)
CREATE INDEX idx_legal_chunks_tsv 
ON public.legal_chunks 
USING gin (tsv_content);

-- Índice B-Tree para recuperación directa por número de artículo
CREATE INDEX idx_legal_chunks_article 
ON public.legal_chunks (statute_code, article_number);

ALTER TABLE public.legal_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "legal_chunks_read" ON public.legal_chunks FOR SELECT TO authenticated USING (true);

-- ------------------------------------------------------------------------------
-- 6. HISTORIAL DE CONSULTAS Y MÉTRICAS (public.query_sessions y public.query_logs)
-- Cumplimiento de HU-06 (Historial del Usuario)
-- ------------------------------------------------------------------------------
CREATE TABLE public.query_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_title VARCHAR(255) NOT NULL DEFAULT 'Nueva consulta jurídica',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_query_sessions_user ON public.query_sessions(user_id);
ALTER TABLE public.query_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sessions_owner_access" ON public.query_sessions
    FOR ALL TO authenticated
    USING (user_id = (SELECT auth.uid()))
    WITH CHECK (user_id = (SELECT auth.uid()));

CREATE TABLE public.query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.query_sessions(id) ON DELETE CASCADE,
    user_query TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    response_latency_ms NUMERIC(8, 2) NOT NULL DEFAULT 0,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    model_used VARCHAR(100) NOT NULL DEFAULT 'llama-3.3-70b-versatile',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_query_logs_session ON public.query_logs(session_id);
ALTER TABLE public.query_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "logs_owner_access" ON public.query_logs
    FOR ALL TO authenticated
    USING (session_id IN (SELECT id FROM public.query_sessions WHERE user_id = (SELECT auth.uid())))
    WITH CHECK (session_id IN (SELECT id FROM public.query_sessions WHERE user_id = (SELECT auth.uid())));

-- ------------------------------------------------------------------------------
-- 7. TRAZABILIDAD DE CITAS (public.citation_refs)
-- Cumplimiento de HU-02 (Citas verificables al SPIJ vinculadas a legal_chunks)
-- ------------------------------------------------------------------------------
CREATE TABLE public.citation_refs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_log_id UUID NOT NULL REFERENCES public.query_logs(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES public.legal_chunks(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) NOT NULL,
    inline_citation_index INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_citation_refs_query ON public.citation_refs(query_log_id);
CREATE INDEX idx_citation_refs_chunk ON public.citation_refs(chunk_id);
ALTER TABLE public.citation_refs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "citations_owner_access" ON public.citation_refs
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.query_logs ql
            JOIN public.query_sessions qs ON qs.id = ql.session_id
            WHERE ql.id = citation_refs.query_log_id
              AND qs.user_id = (SELECT auth.uid())
        )
    );

-- ------------------------------------------------------------------------------
-- 8. FUNCIONES RPC DE RECUPERACIÓN VECTORIAL E HÍBRIDA
-- ------------------------------------------------------------------------------

-- 8.1. Búsqueda híbrida con Reciprocal Rank Fusion (RRF)
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
    raw_content TEXT,
    official_spij_url TEXT,
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
    lc.raw_content,
    lc.official_spij_url,
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

-- 8.2. Búsqueda semántica pura (contingencia)
CREATE OR REPLACE FUNCTION public.match_legal_chunks(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.70,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    statute_code VARCHAR,
    statutory_hierarchy TEXT,
    article_number INT,
    raw_content TEXT,
    official_spij_url TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        lc.id,
        lc.statute_code,
        lc.statutory_hierarchy,
        lc.article_number,
        lc.raw_content,
        lc.official_spij_url,
        (1 - (lc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM public.legal_chunks lc
    WHERE 1 - (lc.embedding <=> query_embedding) >= match_threshold
    ORDER BY lc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
