-- Additive migration: references and modifies only the new Richard table.
-- Intentionally no IF NOT EXISTS: an unexpected name collision must fail.
CREATE TABLE public.richard_youtube_episodes (
    pipeline_id uuid NOT NULL,
    episode_id text NOT NULL,
    topic_key text NOT NULL,
    title text NOT NULL,
    status text NOT NULL,
    youtube_id text,
    publish_slot text,
    bucket text NOT NULL CHECK (bucket = 'richard-youtube'),
    objects jsonb NOT NULL,
    manifest jsonb NOT NULL,
    source_updated_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (pipeline_id, episode_id),
    UNIQUE (pipeline_id, topic_key)
);
ALTER TABLE public.richard_youtube_episodes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.richard_youtube_episodes FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.richard_youtube_episodes TO service_role;
COMMENT ON TABLE public.richard_youtube_episodes IS
    'Richard YouTube archive v1; isolated from existing application and Instagram records';
NOTIFY pgrst, 'reload schema';
