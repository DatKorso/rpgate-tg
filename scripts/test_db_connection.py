"""Test database connection (async, marked for pytest)."""
import asyncio
import pytest
from app.config import settings


@pytest.mark.asyncio
async def test_db_connection():
    """Test database connection and display status."""
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    
    # Check configuration
    print("\n📋 Configuration:")
    if settings.supabase_url:
        print(f"✅ SUPABASE_URL: {settings.supabase_url[:30]}...")
    else:
        print("❌ SUPABASE_URL: Not set")
    
    if settings.supabase_key:
        print(f"✅ SUPABASE_KEY: {settings.supabase_key[:10]}...{settings.supabase_key[-10:]}")
    else:
        print("❌ SUPABASE_KEY: Not set")
    
    if settings.supabase_db_url:
        # Hide password in URL
        url_parts = settings.supabase_db_url.split('@')
        if len(url_parts) > 1:
            print(f"✅ SUPABASE_DB_URL: postgresql://***@{url_parts[1]}")
        else:
            print(f"✅ SUPABASE_DB_URL: {settings.supabase_db_url[:30]}...")
    else:
        print("❌ SUPABASE_DB_URL: Not set")
    
    # Try to connect
    if not (settings.supabase_url and settings.supabase_key and settings.supabase_db_url):
        print("\n⚠️  Database not configured. Cannot test connection.")
        print("See: docs/SPRINT3_SETUP_GUIDE.md")
        return False
    
    print("\n🔌 Testing connection...")
    
    try:
        import asyncpg
        conn = await asyncpg.connect(settings.supabase_db_url, timeout=10)
        print("✅ Connection established!")

        # Get PostgreSQL version
        version = await conn.fetchval("SELECT version()")
        print(f"\n📊 PostgreSQL version:")
        print(f"   {version.split(',')[0]}")

        # Check tables
        tables = await conn.fetch(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )

        if tables:
            print(f"\n📁 Tables ({len(tables)}):")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("\n⚠️  No tables found. Run migration:")
            print("   uv run python scripts/apply_migration.py")

        # Check pgvector extension
        has_vector = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )

        if has_vector:
            print("\n✅ pgvector extension: Enabled")
        else:
            print("\n⚠️  pgvector extension: Not enabled")
            print("   Run migration to enable it")

        await conn.close()

        print("\n" + "=" * 60)
        print("✅ Database connection test PASSED")
        print("=" * 60)
        return True
        
    except ImportError:
        print("\n❌ asyncpg package not installed")
        print("   Run: uv add asyncpg")
        return False
        
    except asyncpg.exceptions.InvalidPasswordError:
        print("\n❌ Invalid database credentials")
        print("   Check SUPABASE_DB_URL in .env")
        return False
        
    except asyncpg.exceptions.CannotConnectNowError:
        print("\n❌ Cannot connect to database")
        print("   - Check if Supabase project is running")
        print("   - Verify connection string is correct")
        return False
    
    except OSError as e:
        if "nodename nor servname" in str(e):
            print("\n❌ DNS resolution failed")
            print("   - Check your internet connection")
            print("   - Verify SUPABASE_DB_URL hostname is correct")
            print(f"   - Error: {e}")
        else:
            print(f"\n❌ Network error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    exit(0 if success else 1)
