"""
Verify Sprint 3 setup and configuration.

This script checks if all required configuration is present
and can connect to the database.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_config():
    """Check if configuration is loaded."""
    print("🔍 Checking configuration...")
    
    try:
        from app.config import settings
        
        # Check existing config
        print("✅ Basic configuration loaded")
        print(f"   - LLM Model: {settings.llm_model}")
        
        # Check Supabase config
        if settings.supabase_url and settings.supabase_key:
            print("✅ Supabase configuration found")
            print(f"   - URL: {settings.supabase_url[:30]}...")
        else:
            print("⚠️  Supabase not configured (optional for now)")
            print("   - See docs/SPRINT3_SETUP_GUIDE.md for setup instructions")
        
        # Check embeddings config
        print(f"✅ Embeddings configuration:")
        print(f"   - Model: {settings.embedding_model}")
        print(f"   - Dimension: {settings.embedding_dimension}")
        print(f"   - Uses OpenRouter API key (no separate key needed)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def check_database():
    """Check database connection."""
    print("\n🔍 Checking database connection...")
    
    try:
        from app.config import settings
        
        if not settings.supabase_db_url:
            print("⚠️  Database not configured")
            print("   - This is OK for now. Complete setup first.")
            print("   - See docs/SPRINT3_SETUP_GUIDE.md")
            return True
        
        # Try to connect
        import asyncio
        import asyncpg
        
        async def test_connection():
            try:
                print("🔌 Attempting connection...")
                conn = await asyncpg.connect(settings.supabase_db_url)
                
                # Test query
                version = await conn.fetchval("SELECT version()")
                print(f"✅ Database connected!")
                print(f"   - PostgreSQL version: {version.split(',')[0]}")
                
                # Check for tables
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                if tables:
                    print(f"✅ Found {len(tables)} tables:")
                    for table in tables:
                        print(f"   - {table['table_name']}")
                else:
                    print("⚠️  No tables found. Run migration:")
                    print("   uv run python scripts/apply_migration.py")
                
                # Check pgvector
                extensions = await conn.fetch("""
                    SELECT extname FROM pg_extension WHERE extname = 'vector'
                """)
                
                if extensions:
                    print("✅ pgvector extension enabled")
                else:
                    print("⚠️  pgvector extension not found")
                    print("   - Run migration to enable it")
                
                await conn.close()
                return True
                
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                print("\nTroubleshooting:")
                print("1. Check SUPABASE_DB_URL in .env")
                print("2. Verify password is correct")
                print("3. Check Supabase project is running")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print("   Run: uv add asyncpg")
        return True  # Not critical yet
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_files():
    """Check if required files exist."""
    print("\n🔍 Checking Sprint 3 files...")
    
    required_files = [
        "app/db/__init__.py",
        "app/db/models.py",
        "app/db/supabase.py",
        "app/db/migrations/001_initial_schema.sql",
        "scripts/apply_migration.py",
        "docs/SPRINT3_SETUP_GUIDE.md",
        "docs/SPRINT3_CHECKLIST.md",
        "docs/SPRINT3_PROGRESS.md",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist


def main():
    """Run all checks."""
    print("=" * 60)
    print("Sprint 3 Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Configuration", check_config),
        ("Files", check_files),
        ("Database", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed!")
        print("\nNext steps:")
        print("1. If database not configured, see: docs/SPRINT3_SETUP_GUIDE.md")
        print("2. Install dependencies: uv add supabase asyncpg sqlalchemy pgvector httpx")
        print("3. Apply migration: uv run python scripts/apply_migration.py")
    else:
        print("\n⚠️  Some checks failed. Review output above.")
        print("\nSee: docs/SPRINT3_SETUP_GUIDE.md for setup instructions")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
