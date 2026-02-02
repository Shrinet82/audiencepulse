-- Enforce unique campaign names per user
-- This means User A can have "Q1 Launch" and User B can have "Q1 Launch",
-- But User A cannot have two "Q1 Launch" campaigns.

ALTER TABLE campaigns 
ADD CONSTRAINT unique_user_campaign_name 
UNIQUE (user_email, name);
