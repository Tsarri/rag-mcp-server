-- Add completed tracking to deadlines table
-- Run this in Supabase SQL Editor after merging this PR

ALTER TABLE deadlines 
ADD COLUMN IF NOT EXISTS completed BOOLEAN DEFAULT FALSE;

ALTER TABLE deadlines 
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Add index for performance when filtering by completed status
CREATE INDEX IF NOT EXISTS idx_deadlines_completed ON deadlines(completed);

-- Verify columns were added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'deadlines' 
AND column_name IN ('completed', 'completed_at');
