# Sprint 3 Setup Guide

## Database Setup Instructions

### Step 1: Create Supabase Project

1. **Sign up for Supabase** (if you don't have an account):
   - Go to [supabase.com](https://supabase.com)
   - Click "Start your project"
   - Sign up with GitHub or email

2. **Create a new project**:
   - Click "New Project"
   - Choose your organization (or create one)
   - Enter project details:
     - **Name**: `rpgate-tg` (or your preferred name)
     - **Database Password**: Choose a strong password (save it!)
     - **Region**: Choose closest to your target audience
     - **Pricing Plan**: Free tier is fine for MVP
   - Click "Create new project"
   - Wait for project initialization (~2 minutes)

3. **Get your credentials**:
   - Go to **Project Settings** (gear icon in sidebar)
   - Go to **API** section
   - Copy the following:
     - **Project URL** (e.g., `https://xxxxx.supabase.co`)
     - **anon/public** key (under "Project API keys")
   - Go to **Database** section
   - Copy **Connection string** under "Connection string" → "URI"
     - It looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`
     - Replace `[YOUR-PASSWORD]` with the password you chose

### Step 2: Update Environment Variables

1. **Copy `.env.example` to `.env`** (if you haven't already):
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** and add your Supabase credentials:
   ```bash
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
   
   # Embeddings Configuration (uses OpenRouter, no separate key needed)
   EMBEDDING_MODEL=qwen/qwen3-embedding-8b
   EMBEDDING_DIMENSION=4096
   ```

3. **Get OpenAI API key** (for embeddings):
   - **UPDATE**: Embeddings используют OpenRouter API key
   - Отдельный OpenAI API key **НЕ НУЖЕН**
   - Embeddings будут использовать `OPENROUTER_API_KEY`

### Step 3: Install Dependencies

```bash
# Install Supabase and database dependencies
uv add supabase asyncpg sqlalchemy pgvector

# Install httpx for embeddings API calls (OpenRouter)
uv add httpx

# Install dev dependencies for testing
uv add --dev pytest-asyncio
```

**Note**: OpenAI package НЕ нужен, embeddings идут через OpenRouter API.

### Step 4: Apply Database Migration

```bash
# Run migration script
uv run python scripts/apply_migration.py
```

**Expected output:**
```
🔄 Starting database migration...
📄 Loaded migration file: 001_initial_schema.sql
🔌 Connecting to database...
⚙️  Applying migration...
✅ Migration applied successfully!

📊 Verifying tables...

✅ Created 5 tables:
   - characters
   - episodic_memories
   - game_sessions
   - semantic_memories
   - world_state

✅ pgvector extension enabled
```

### Step 5: Verify Setup

1. **Check Supabase Dashboard**:
   - Go to your project dashboard
   - Click on **Table Editor** (left sidebar)
   - You should see 5 tables created

2. **Check sample data**:
   - Open `semantic_memories` table
   - You should see 4 rows of sample lore data

3. **Check pgvector**:
   - Go to **SQL Editor**
   - Run: `SELECT * FROM pg_extension WHERE extname = 'vector';`
   - Should return 1 row

## Troubleshooting

### Migration fails with "extension already exists"

**Solution**: This is OK! It means pgvector was already enabled. The migration will continue.

### Connection refused or timeout

**Solution**: 
- Check your `SUPABASE_DB_URL` is correct
- Check your database password is correct
- Try copying the connection string again from Supabase dashboard

### Missing packages

**Solution**:
```bash
# Make sure all packages are installed
uv sync
```

### OpenAI API errors

**Solution**:
- ❌ **OpenAI API key больше НЕ нужен!**
- ✅ Embeddings используют OpenRouter API (тот же ключ что и для LLM)
- Check your `OPENROUTER_API_KEY` is valid
- Verify you have credits in your OpenRouter account
- Embedding model: `qwen/qwen3-embedding-8b` (через OpenRouter)

## Next Steps

After successful setup, proceed to:
- **Week 2**: Memory System & Agents implementation
- See `SPRINT3_CHECKLIST.md` for detailed task list

## Cost Estimates

### Supabase (Free Tier)
- **Database**: 500MB (enough for 1000s of memories)
- **Bandwidth**: 2GB/month
- **Cost**: $0/month for MVP

### OpenAI Embeddings
- **Model**: text-embedding-3-small (через OpenRouter)
- **Cost**: $0.02 per 1M tokens (через OpenRouter pricing)
- **Per memory**: ~$0.000002 (100 tokens avg)
- **1000 memories**: ~$0.002 total

**Note**: Используется OpenRouter API, не прямой OpenAI API

## Security Notes

⚠️ **Never commit `.env` file to git!**

Make sure `.env` is in your `.gitignore`:
```bash
# Check if .env is ignored
git check-ignore .env
# Should output: .env
```

🔒 **Use anon key** for client-side operations (already configured)

🔐 **Database password** should be strong and unique

## Support

If you encounter issues:
1. Check Supabase status: [status.supabase.com](https://status.supabase.com)
2. Review Supabase docs: [supabase.com/docs](https://supabase.com/docs)
3. Check pgvector docs: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
