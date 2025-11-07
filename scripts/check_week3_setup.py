#!/usr/bin/env python3
"""
Sprint 3 Week 3 Setup Check Script
Проверяет готовность к интеграции и полировке.
"""
import asyncio
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_status(message: str, status: str):
    """Print status message with color."""
    if status == "ok":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "fail":
        print(f"{RED}✗{RESET} {message}")
    elif status == "warn":
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"{BLUE}ℹ{RESET} {message}")


async def check_week3_setup():
    """Check Sprint 3 Week 3 integration setup."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Sprint 3 Week 3: Integration & Polish - Setup Check{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")
    
    all_ok = True
    
    # 1. Check database CRUD modules
    print(f"\n{BLUE}[1] Database CRUD Modules{RESET}")
    
    try:
        from app.db.characters import (
            get_character_by_telegram_id,
            create_character,
            update_character,
            delete_character
        )
        print_status("app/db/characters.py exists and imports correctly", "ok")
    except ImportError as e:
        print_status(f"app/db/characters.py import error: {e}", "fail")
        all_ok = False
    
    try:
        from app.db.sessions import (
            create_session,
            get_active_session,
            end_session,
            update_session_stats,
            get_or_create_session
        )
        print_status("app/db/sessions.py exists and imports correctly", "ok")
    except ImportError as e:
        print_status(f"app/db/sessions.py import error: {e}", "fail")
        all_ok = False
    
    # 2. Check Memory Manager integration
    print(f"\n{BLUE}[2] Memory Manager Agent{RESET}")
    
    try:
        from app.agents.memory_manager import memory_manager_agent
        print_status("Memory Manager Agent exists", "ok")
        
        # Check methods
        if hasattr(memory_manager_agent, 'execute'):
            print_status("Memory Manager has execute() method", "ok")
        else:
            print_status("Memory Manager missing execute() method", "fail")
            all_ok = False
        
        if hasattr(memory_manager_agent, 'extract_memory_metadata'):
            print_status("Memory Manager has extract_memory_metadata() method", "ok")
        else:
            print_status("Memory Manager missing extract_memory_metadata()", "fail")
            all_ok = False
            
    except ImportError as e:
        print_status(f"Memory Manager import error: {e}", "fail")
        all_ok = False
    
    # 3. Check World State Agent
    print(f"\n{BLUE}[3] World State Agent{RESET}")
    
    try:
        from app.agents.world_state import world_state_agent
        print_status("World State Agent exists", "ok")
        
        # Check methods
        if hasattr(world_state_agent, 'execute'):
            print_status("World State has execute() method", "ok")
        else:
            print_status("World State missing execute() method", "fail")
            all_ok = False
        
        if hasattr(world_state_agent, 'load_world_state'):
            print_status("World State has load_world_state() method", "ok")
        else:
            print_status("World State missing load_world_state()", "fail")
            all_ok = False
            
    except ImportError as e:
        print_status(f"World State Agent import error: {e}", "fail")
        all_ok = False
    
    # 4. Check Orchestrator updates
    print(f"\n{BLUE}[4] Updated Orchestrator{RESET}")
    
    try:
        from app.agents.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        
        # Check agent instances
        if hasattr(orchestrator, 'memory_manager'):
            print_status("Orchestrator has memory_manager instance", "ok")
        else:
            print_status("Orchestrator missing memory_manager", "fail")
            all_ok = False
        
        if hasattr(orchestrator, 'world_state'):
            print_status("Orchestrator has world_state instance", "ok")
        else:
            print_status("Orchestrator missing world_state", "fail")
            all_ok = False
        
        if hasattr(orchestrator, '_save_memory'):
            print_status("Orchestrator has _save_memory() method", "ok")
        else:
            print_status("Orchestrator missing _save_memory() method", "fail")
            all_ok = False
            
    except Exception as e:
        print_status(f"Orchestrator check error: {e}", "fail")
        all_ok = False
    
    # 5. Check Bot Handlers integration
    print(f"\n{BLUE}[5] Bot Handlers Integration{RESET}")
    
    try:
        from app.bot.handlers import router
        print_status("Bot handlers module loads correctly", "ok")
        
        # Check if handlers import DB modules
        with open("app/bot/handlers.py", "r") as f:
            content = f.read()
            
            if "from app.db.characters import" in content:
                print_status("Handlers import characters CRUD", "ok")
            else:
                print_status("Handlers don't import characters CRUD", "warn")
            
            if "from app.db.sessions import" in content:
                print_status("Handlers import sessions CRUD", "ok")
            else:
                print_status("Handlers don't import sessions CRUD", "warn")
            
            if "from app.agents.world_state import" in content:
                print_status("Handlers import world_state agent", "ok")
            else:
                print_status("Handlers don't import world_state agent", "warn")
                
    except Exception as e:
        print_status(f"Handlers check error: {e}", "fail")
        all_ok = False
    
    # 6. Check database connection
    print(f"\n{BLUE}[6] Database Connection{RESET}")
    
    try:
        from app.db.supabase import get_db_connection
        
        conn = await get_db_connection()
        await conn.close()
        print_status("Database connection successful", "ok")
        
    except Exception as e:
        print_status(f"Database connection error: {e}", "fail")
        all_ok = False
    
    # 7. Check environment variables
    print(f"\n{BLUE}[7] Environment Configuration{RESET}")
    
    try:
        from app.config import settings
        
        if settings.supabase_url:
            print_status("SUPABASE_URL configured", "ok")
        else:
            print_status("SUPABASE_URL not configured", "fail")
            all_ok = False
        
        if settings.supabase_key:
            print_status("SUPABASE_KEY configured", "ok")
        else:
            print_status("SUPABASE_KEY not configured", "fail")
            all_ok = False
        
        if settings.supabase_db_url:
            print_status("SUPABASE_DB_URL configured", "ok")
        else:
            print_status("SUPABASE_DB_URL not configured", "fail")
            all_ok = False
            
    except Exception as e:
        print_status(f"Config check error: {e}", "fail")
        all_ok = False
    
    # 8. Check test file
    print(f"\n{BLUE}[8] Integration Tests{RESET}")
    
    test_file = Path("tests/test_integration_week3.py")
    if test_file.exists():
        print_status("Integration test file exists", "ok")
    else:
        print_status("Integration test file missing", "warn")
    
    # Final summary
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    if all_ok:
        print(f"{GREEN}✅ All checks passed! Ready for Sprint 3 Week 3{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print("  1. Run integration tests: uv run pytest tests/test_integration_week3.py -v")
        print("  2. Test bot with DB: uv run start")
        print("  3. Create a character and test memory persistence")
    else:
        print(f"{RED}❌ Some checks failed. Please fix issues above.{RESET}")
        return False
    
    print(f"{BLUE}{'=' * 60}{RESET}\n")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(check_week3_setup())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠ Check interrupted{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}✗ Error: {e}{RESET}")
        sys.exit(1)
