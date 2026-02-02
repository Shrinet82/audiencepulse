-- Creator Identity (Global Registry)
CREATE TABLE IF NOT EXISTS creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT DEFAULT 'youtube',
    channel_id TEXT NOT NULL, -- "UC..."
    handle TEXT, -- "@mkbhd"
    name TEXT NOT NULL,
    avatar_url TEXT,
    subscriber_count BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(platform, channel_id)
);

-- Junction: Campaigns <-> Creators
CREATE TABLE IF NOT EXISTS campaign_creators (
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (campaign_id, creator_id)
);

-- Analysis History (One Creator -> Many Analyses)
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id), -- Optional context
    status TEXT DEFAULT 'pending', -- pending, completed, failed
    fit_score INTEGER,
    report_json JSONB, -- The full analysis result
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_creators_channel ON creators(channel_id);
CREATE INDEX IF NOT EXISTS idx_camp_creators_camp ON campaign_creators(campaign_id);
CREATE INDEX IF NOT EXISTS idx_analysis_creator ON analysis_runs(creator_id);
