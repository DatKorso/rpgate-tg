# Bug Fixes: Combat State & Markdown Formatting

**Date:** 2025-11-07  
**Status:** ✅ Fixed and tested

## Overview

Fixed two critical bugs discovered during manual testing based on log analysis:
1. **Combat state incorrectly resetting** after player attacks
2. **Markdown parsing errors** causing messages to fail

## Bug #1: Combat State Reset (CRITICAL)

### Problem

**Symptom:**
- Player attacks enemy → combat starts → combat immediately ends
- Log showed: `in_combat=True` from Narrative Director, but `in_combat=False` in final state

**Root Cause:**
```python
# In World State Agent _handle_combat_update()
if damage >= enemy_hp_threshold:
    enemies = state.get("enemies", [])
    if enemies:
        defeated_enemy = enemies[0]
        enemies = enemies[1:]
        state["enemies"] = enemies
        
        if not enemies:
            state["in_combat"] = False  # ❌ BUG: Overrides Narrative Director decision
```

**Why this is wrong:**
- **Narrative Director** sets `in_combat=True` with proper LLM reasoning
- **World State Agent** then checks damage and automatically resets `in_combat=False`
- This violates the **single source of truth principle** - only Narrative Director should manage combat state

### Solution

**Disabled `_handle_combat_update()` logic:**
```python
def _handle_combat_update(
    self,
    state: dict,
    mechanics_result: dict,
    changes: List[str]
):
    """
    Handle combat-specific state updates.
    
    NOTE: Combat state (in_combat, enemies, combat_ended) управляется 
    ТОЛЬКО Narrative Director через game_state_updates.
    
    Этот метод оставлен для будущих механик (например, tracking enemy HP в БД).
    В текущей версии НЕ модифицирует combat state напрямую.
    """
    # Логика убийства врагов ОТКЛЮЧЕНА - это делает Narrative Director
    # В будущем здесь может быть отслеживание HP врагов в БД
    pass
```

**Key principle:**
- **Narrative Director** = single source of truth for combat state
- **World State Agent** = persistence layer, does NOT modify combat logic
- Enemy defeat detection = LLM's responsibility (Narrative Director)

### Files Changed
- `app/agents/world_state.py` - Disabled automatic combat state modification
- `app/agents/narrative_director.py` - Added critical documentation in docstring
- `tests/test_world_state.py` - Updated tests to reflect new logic

---

## Bug #2: Markdown Parsing Errors

### Problem

**Symptom:**
```
WARNING - Markdown parsing failed: 
Telegram server says - Bad Request: can't parse entities: 
Can't find end of the entity starting at byte offset 984
```

**Root Cause:**
- Response Synthesizer's `_sanitize_markdown()` had basic logic but wasn't robust enough
- Unbalanced Markdown tags (`**`, `__`, `*`, `_`) caused Telegram API to reject messages
- Special characters at line starts caused issues

### Solution

**Enhanced `_sanitize_markdown()` method:**

```python
def _sanitize_markdown(self, text: str) -> str:
    """
    Sanitize text to prevent Markdown parsing errors.
    
    Improvements:
    1. Better ** (bold) balancing - splits by ** and checks pairs
    2. Better __ (underline) balancing 
    3. Separate handling for single * and _ after handling doubles
    4. JSON remnant removal (combat_state fragments)
    5. Backtick balancing
    6. Special character escaping at line starts
    """
```

**Key improvements:**
1. **Split-based balancing** instead of counting
2. **Temporary placeholders** to avoid conflicts (⚡BOLD⚡, ⚡UNDERLINE⚡)
3. **JSON cleanup** to remove combat state remnants from narrative
4. **Line-level escaping** for problematic characters

### Enhanced Error Logging

**Added detailed Markdown error tracking:**
```python
# In bot/handlers.py
try:
    await message.answer(final_message, parse_mode="Markdown")
except Exception as e:
    error_msg = str(e)
    logger.warning(
        f"Markdown parsing failed: {error_msg}. "
        f"Message length: {len(final_message)} chars. "
        f"Sending as plain text."
    )
    
    # Log problematic section if byte offset is mentioned
    if "byte offset" in error_msg:
        try:
            import re
            match = re.search(r'byte offset (\d+)', error_msg)
            if match:
                offset = int(match.group(1))
                # Log context around the problematic byte
                start = max(0, offset - 50)
                end = min(len(final_message), offset + 50)
                context = final_message[start:end]
                logger.warning(f"Problematic section (bytes {start}-{end}): {repr(context)}")
        except Exception:
            pass
```

### Files Changed
- `app/agents/response_synthesizer.py` - Enhanced `_sanitize_markdown()` logic
- `app/bot/handlers.py` - Added detailed error logging with byte offset context
- `tests/test_response_synthesizer.py` - All tests pass

---

## Additional Improvements

### Debug Logging

Added comprehensive debug logging in World State Agent:

```python
self.logger.debug(f"Initial state: in_combat={updated_state.get('in_combat')}, enemies={updated_state.get('enemies', [])}")

# After narrative updates
self.logger.debug(f"After narrative updates: in_combat={updated_state.get('in_combat')}, enemies={updated_state.get('enemies', [])}")

# After combat updates
self.logger.debug(f"After combat updates: in_combat={updated_state.get('in_combat')}, enemies={updated_state.get('enemies', [])}")
```

**Benefits:**
- Track combat state changes at each step
- Easy debugging of future issues
- Clear audit trail in logs

---

## Testing

### Unit Tests
```bash
uv run pytest tests/test_world_state.py -v
✅ 15 passed

uv run pytest tests/test_response_synthesizer.py -v
✅ 8 passed
```

### Full Test Suite
```bash
uv run pytest tests/ -v
✅ 93 passed, 1 warning
```

### Manual Testing Required

**Combat flow test:**
1. Create character
2. Start new conversation
3. Attack enemy → combat should START and CONTINUE
4. Attack again → combat should CONTINUE until Narrative Director decides to end it
5. Check logs for:
   - `Narrative Director: in_combat=True` ✅
   - `World State: After narrative updates: in_combat=True` ✅
   - `Orchestrator: New combat state: True` ✅ (not False!)

**Markdown test:**
1. Look for any "Markdown parsing failed" warnings
2. If found, check new detailed logs for byte offset context
3. Verify fallback to plain text works

---

## Architecture Impact

### Before (Broken)
```
Narrative Director → sets in_combat=True
    ↓
World State Agent → sees high damage → overrides in_combat=False ❌
```

### After (Fixed)
```
Narrative Director → sets in_combat=True (single source of truth)
    ↓
World State Agent → persists state WITHOUT modification ✅
```

### Design Principle

**Single Responsibility:**
- **Narrative Director** = Combat logic & enemy management (LLM-based)
- **World State Agent** = State persistence (deterministic DB operations)

**No overlap, clear boundaries.**

---

## Future Improvements (Sprint 4+)

### Enemy HP Tracking
When implementing persistent enemies:
```python
# In World State Agent
def _track_enemy_hp(self, enemy_id: UUID, damage: int):
    """Track enemy HP in database for persistent combat."""
    # Update enemies table in DB
    # Return True if enemy defeated
```

### Combat State Validation
Add validation layer to ensure Narrative Director output is consistent:
```python
def _validate_combat_state(self, state: dict) -> bool:
    """Validate combat state consistency."""
    # If in_combat=True, must have enemies
    # If enemies=[], in_combat must be False
    # etc.
```

---

## Lessons Learned

1. **Log analysis is critical** - manual test revealed bug that unit tests missed
2. **Single source of truth** - don't duplicate logic across agents
3. **Debug logging investment** - saves hours during debugging
4. **Markdown is fragile** - always sanitize LLM-generated text before Telegram API
5. **Test what you fix** - updated tests to prevent regression

---

## References

- Log analysis: Terminal output from `uv run start` (2025-11-07 18:16-18:18)
- Strategic plan: `docs/STRATEGIC_PLAN.md` - Multi-agent architecture
- API contracts: `docs/API_CONTRACTS.md` - Agent responsibilities
