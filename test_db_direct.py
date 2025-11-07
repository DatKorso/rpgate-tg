"""Test direct database connection with different methods."""
import asyncio
from urllib.parse import quote_plus

# Password with special characters
PASSWORD = "7224596Fiz!"
ENCODED_PASSWORD = quote_plus(PASSWORD)
PROJECT_REF = "akabzlotszniqxdkwixw"

# Different connection string variants
CONNECTIONS = {
    "Direct (db.)": f"postgresql://postgres:{ENCODED_PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres",
    "Direct (raw password)": f"postgresql://postgres:{PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres",
    "Pooler (aws)": f"postgresql://postgres.{PROJECT_REF}:{ENCODED_PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
}

async def test_asyncpg():
    """Test with asyncpg (used in the bot)."""
    print("=" * 60)
    print("Testing with asyncpg (used in bot)")
    print("=" * 60)
    
    try:
        import asyncpg
    except ImportError:
        print("❌ asyncpg not installed. Installing...")
        import subprocess
        subprocess.run(["uv", "add", "asyncpg"])
        import asyncpg
    
    for name, conn_string in CONNECTIONS.items():
        print(f"\n🔍 Testing: {name}")
        print(f"   Connection: {conn_string.replace(ENCODED_PASSWORD, '***').replace(PASSWORD, '***')}")
        
        try:
            conn = await asyncpg.connect(conn_string, timeout=10.0)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            print(f"   ✅ SUCCESS!")
            print(f"   └─ {version[:50]}...")
            return conn_string  # Return working connection
        except Exception as e:
            print(f"   ❌ FAILED: {type(e).__name__}")
            print(f"   └─ {str(e)[:100]}")
    
    return None

def test_psycopg2():
    """Test with psycopg2 (suggested by Supabase)."""
    print("\n" + "=" * 60)
    print("Testing with psycopg2 (Supabase recommendation)")
    print("=" * 60)
    
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        import subprocess
        subprocess.run(["uv", "add", "psycopg2-binary"])
        import psycopg2
    
    for name, conn_string in CONNECTIONS.items():
        print(f"\n🔍 Testing: {name}")
        
        try:
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            print(f"   ✅ SUCCESS!")
            print(f"   └─ {version[:50]}...")
            return conn_string
        except Exception as e:
            print(f"   ❌ FAILED: {type(e).__name__}")
            print(f"   └─ {str(e)[:100]}")
    
    return None

async def main():
    """Run all tests."""
    print("🔌 Testing Supabase Database Connections")
    print("=" * 60)
    
    # Test asyncpg first (what the bot uses)
    working_asyncpg = await test_asyncpg()
    
    # Test psycopg2
    working_psycopg2 = test_psycopg2()
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    if working_asyncpg:
        print(f"\n✅ asyncpg (bot) works with:")
        print(f"   {working_asyncpg.replace(ENCODED_PASSWORD, '***').replace(PASSWORD, '***')}")
        print(f"\n💡 Add this to .env as SUPABASE_DB_URL")
    else:
        print("\n❌ asyncpg failed with all connection strings")
    
    if working_psycopg2:
        print(f"\n✅ psycopg2 works with:")
        print(f"   {working_psycopg2.replace(ENCODED_PASSWORD, '***').replace(PASSWORD, '***')}")
    else:
        print("\n❌ psycopg2 failed with all connection strings")
    
    if not working_asyncpg and not working_psycopg2:
        print("\n⚠️  TROUBLESHOOTING:")
        print("1. Check your password in Supabase Dashboard")
        print("2. Go to Settings → Database → Connection String")
        print("3. Use 'Direct connection' (port 5432), NOT pooler")
        print("4. Make sure your IP is not blocked (check Database settings)")

if __name__ == "__main__":
    asyncio.run(main())
