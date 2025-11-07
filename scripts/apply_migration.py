"""Apply database migration to Supabase."""
import asyncio
import asyncpg
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def apply_migration():
    """Apply initial schema migration."""
    print("🔄 Starting database migration...")
    
    # Read migration file
    migration_path = Path(__file__).parent.parent / 'app' / 'db' / 'migrations' / '001_initial_schema.sql'
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print(f"📄 Loaded migration file: {migration_path.name}")
    
    try:
        # Connect to database
        print(f"🔌 Connecting to database...")
        conn = await asyncpg.connect(settings.supabase_db_url)
        
        print("⚙️  Applying migration...")
        await conn.execute(migration_sql)
        
        print("✅ Migration applied successfully!")
        print("\n📊 Verifying tables...")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"\n✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Verify pgvector extension
        extensions = await conn.fetch("""
            SELECT extname FROM pg_extension WHERE extname = 'vector'
        """)
        
        if extensions:
            print("\n✅ pgvector extension enabled")
        else:
            print("\n⚠️  Warning: pgvector extension not found")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    sys.exit(0 if success else 1)
