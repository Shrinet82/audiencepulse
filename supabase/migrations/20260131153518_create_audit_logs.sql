-- Create Audit Logs table for Campaign History
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- In production, link to auth.users. For MVP, we might store email or placeholder if using custom auth currently
    -- ideally: user_id UUID REFERENCES auth.users(id),
    user_email VARCHAR(255), 
    
    -- INPUTS (Memory Engine)
    target_video_url TEXT NOT NULL,
    product_name VARCHAR(255),
    price_tier VARCHAR(50), 
    campaign_description TEXT,
    
    -- OUTPUTS (Cache Engine)
    final_score INT,
    analysis_json JSONB, -- Stores full 'Audience DNA', 'Verdict', 'Breakdown'
    
    -- METADATA
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for fast history loading
CREATE INDEX IF NOT EXISTS idx_audit_logs_email_created ON audit_logs(user_email, created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see their own logs
-- (Commented out until Auth is fully configured, enabling public for dev testing if needed, or restricting)
-- CREATE POLICY "Users can view their own logs" ON audit_logs FOR SELECT USING (auth.uid() = user_id);
