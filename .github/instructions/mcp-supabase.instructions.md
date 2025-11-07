---
applyTo: '**'
---
# Supabase MCP Integration

## Project Context
This project uses Supabase for PostgreSQL database with pgvector extension for memory/RAG functionality (Sprint 3+). Database schema includes tables for game sessions, character sheets, and episodic memory with embeddings.

## Key MCP Tools for This Project

### Database Operations (Primary Use)
- `list_tables` - Check existing schema (sessions, characters, memories, etc.)
- `apply_migration` - Apply schema changes (DDL). Use for migrations in `app/db/migrations/`
- `execute_sql` - Run queries (SELECT, INSERT, UPDATE). Use for data operations and testing
- `list_extensions` - Verify pgvector extension is enabled

### Development
- `get_project_url` - Get API endpoint for `app/db/supabase.py` configuration
- `get_publishable_keys` - Get anon key for client connections (use publishable keys for new code)

### Debugging
- `get_logs` - Check postgres/api logs when troubleshooting database issues
- `get_advisors` - Check for performance or security issues

### Documentation
- `search_docs` - Look up Supabase features (pgvector, RLS policies, etc.)

## Usage Guidelines

### Schema Changes
Always use `apply_migration` for DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX):
```sql
-- This gets tracked in migration history
CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Data Operations
Use `execute_sql` for queries that don't change schema:
```sql
-- Regular queries
SELECT * FROM game_sessions WHERE user_id = 123;
INSERT INTO characters (name, class) VALUES ('Aragorn', 'Warrior');
```

### Migration Workflow
1. Create migration file in `app/db/migrations/` (e.g., `002_add_memory_tables.sql`)
2. Use `apply_migration` to apply it to Supabase
3. Update `app/db/models.py` with corresponding Pydantic models
4. Test with `execute_sql` queries

## Project-Specific Schema

### Core Tables (Sprint 3)
- `game_sessions` - Session metadata and state
- `character_sheets` - Persistent character data
- `episodic_memories` - Conversation history with embeddings (pgvector)
- `semantic_memories` - World lore and facts

### Vector Search
pgvector extension required for RAG. Use for similarity search on episodic memories:
```sql
SELECT * FROM episodic_memories 
ORDER BY embedding <-> '[0.1, 0.2, ...]'::vector 
LIMIT 5;
```

## Connection Details
Supabase client configured in `app/db/supabase.py`. Environment variables:
- `SUPABASE_URL` - From `get_project_url`
- `SUPABASE_KEY` - From `get_publishable_keys`

## Limitations
- Account tools unavailable when scoped to project
- Storage tools disabled by default (not needed for this project)
- Branching requires paid plan (use with caution)