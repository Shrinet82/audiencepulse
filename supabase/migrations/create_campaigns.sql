-- 1. Create Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Link Audit Logs to Campaigns
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id);

-- 3. Security (RLS)
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for now" 
ON "public"."campaigns"
AS PERMISSIVE FOR ALL
TO public
USING (true)
WITH CHECK (true);
