# Bugfix: Auto-Restore Session After Bot Restart

## Problem

After bot restart, players couldn't continue existing games and had to use `/start` to create a new session.

### Root Cause

1. **FSM state stored in memory** - Aiogram uses `MemoryStorage` which clears all states on restart
2. **State becomes `None`** after restart
3. **Handler requires specific state** - `handle_conversation` only responds to `ConversationState.in_conversation`
4. **Messages not handled** - Updates marked as "not handled" because state doesn't match

### Evidence from Logs

```
# Before restart - working
2025-11-10 02:51:56,814 - app.db.characters - INFO - Loaded character Korso [ Sergey ]
2025-11-10 02:51:57,387 - app.db.sessions - INFO - Found active session...

# After restart - broken
2025-11-10 02:53:26,661 - aiogram.event - INFO - Update id=41351214 is not handled.
```

## Solution

Added **fallback handler** that automatically restores session state when character exists in database.

### Changes

**File:** `app/bot/handlers.py`

1. Added `handle_any_message()` handler with `F.text` filter (catches all text messages)
2. Checks if character exists in database via `get_character_by_telegram_id()`
3. If character found:
   - Restores `ConversationState.in_conversation` state
   - Initializes FSM data if needed
   - Forwards to `handle_conversation()`
4. If no character:
   - Shows welcome message

### Handler Order

```python
@router.message(Command("start"))         # Priority 1: Commands
async def cmd_start(...)

@router.message(ConversationState.in_conversation, F.text)  # Priority 2: Active sessions
async def handle_conversation(...)

@router.message(F.text)                   # Priority 3: Fallback with auto-restore
async def handle_any_message(...)
```

Aiogram processes handlers top-to-bottom, so:
- Active sessions skip fallback (already in correct state)
- Restarted sessions hit fallback → auto-restore → forward to conversation handler
- New users hit fallback → see welcome message

## Testing

**Test file:** `tests/test_session_restore.py`

3 test cases:
1. ✅ Character exists in DB → state restored, conversation continues
2. ✅ No character in DB → welcome message shown
3. ✅ Already in conversation → state unchanged, no duplicate restore

**Run tests:**
```bash
uv run pytest tests/test_session_restore.py -v
```

## User Experience

### Before Fix
```
[Player restarts bot]
Player: "Иду на север"
Bot: [no response - update not handled]
Player: /start
Bot: "Привет! Выбери класс персонажа..."
```

### After Fix
```
[Player restarts bot]
Player: "Иду на север"
Bot: [auto-restores session]
Bot: "🎲 Ты идёшь на север и видишь..." [game continues]
```

## Implementation Details

### State Restoration Logic

```python
# Check database for character
character = await get_character_by_telegram_id(telegram_user_id)

if character:
    current_state = await state.get_state()
    
    if current_state != ConversationState.in_conversation:
        # Restore state
        await state.set_state(ConversationState.in_conversation)
        
        # Initialize FSM data
        await state.update_data(
            character=character.model_dump_for_storage(),
            history=[]
        )
    
    # Forward to conversation handler
    await handle_conversation(message, state)
```

### Why This Works

- **Database is persistent** - Character survives restarts
- **FSM is ephemeral** - State resets on restart
- **Auto-recovery bridge** - Fallback handler reconnects FSM to DB state

## Future Improvements

### Sprint 4+ (Persistent FSM Storage)

Consider migrating to persistent storage for FSM:

```python
# Instead of MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url("redis://localhost:6379")
dp = Dispatcher(storage=storage)
```

**Benefits:**
- State survives restarts
- Supports multiple bot instances (horizontal scaling)
- No auto-restore logic needed

**Trade-offs:**
- Requires Redis infrastructure
- Added complexity
- Slightly higher latency

For MVP, auto-restore is simpler and works well.

## Related Files

- `app/bot/handlers.py` - Handler implementation
- `app/bot/states.py` - FSM state definitions
- `app/main.py` - MemoryStorage configuration
- `app/db/characters.py` - Database character lookup
- `tests/test_session_restore.py` - Test coverage

## Date

November 10, 2025

## Status

✅ **Fixed and tested**
