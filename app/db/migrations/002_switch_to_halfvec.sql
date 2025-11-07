-- Sprint 3: Switch from vector(2000) to halfvec(2560)
-- RPGate Telegram Bot - Memory System Optimization

-- This migration switches to halfvec for better dimension support
-- halfvec uses fp16 (half precision) instead of fp32
-- Limit: 4000 dimensions vs 2000 for regular vector

-- ============================================
-- DROP OLD TABLES (if needed for fresh migration)
-- ============================================
-- Uncomment if you want to completely recreate:
-- DROP TABLE IF EXISTS episodic_memories CASCADE;
-- DROP TABLE IF EXISTS semantic_memories CASCADE;
-- DROP TABLE IF EXISTS world_state CASCADE;
-- DROP TABLE IF EXISTS game_sessions CASCADE;
-- DROP TABLE IF EXISTS characters CASCADE;

-- ============================================
-- ALTER EXISTING TABLES to use halfvec
-- ============================================

-- Episodic memories: change vector to halfvec
ALTER TABLE episodic_memories 
DROP COLUMN IF EXISTS embedding;

ALTER TABLE episodic_memories 
ADD COLUMN embedding halfvec(2560);

-- Recreate index for halfvec
DROP INDEX IF EXISTS idx_memories_embedding;
CREATE INDEX idx_memories_embedding ON episodic_memories 
USING hnsw (embedding halfvec_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Semantic memories: change vector to halfvec
ALTER TABLE semantic_memories 
DROP COLUMN IF EXISTS embedding;

ALTER TABLE semantic_memories 
ADD COLUMN embedding halfvec(2560);

-- Recreate index for halfvec
DROP INDEX IF EXISTS idx_semantic_embedding;
CREATE INDEX idx_semantic_embedding ON semantic_memories 
USING hnsw (embedding halfvec_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================
-- VERIFY
-- ============================================
-- Check column types
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name IN ('episodic_memories', 'semantic_memories') 
  AND column_name = 'embedding';
