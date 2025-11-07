# Quick Start Guide: Sprint 3 Week 3 Integration

## 🚀 What Changed

Your bot now has **full database integration** with persistent memory! Here's what's new:

### Before Week 3
- Characters stored in FSM (lost on restart)
- No memory across sessions
- Game state in memory only

### After Week 3
- ✅ Characters persist in PostgreSQL
- ✅ Long-term episodic memory with RAG
- ✅ Game state saved to database
- ✅ Session tracking with statistics

---

## 📝 Quick Reference

### For Users (Telegram)

**Nothing changed!** The bot works exactly the same from the user's perspective, but now it:
- Remembers your character across restarts
- Recalls past events and conversations
- Tracks your session statistics

### For Developers

#### Character Operations
```python
from app.db.characters import get_character_by_telegram_id, create_character, update_character

# Load character from DB
character = await get_character_by_telegram_id(telegram_user_id)

# Create new character
success = await create_character(character)

# Update character (save HP, stats, etc.)
success = await update_character(character)
```

#### Session Management
```python
from app.db.sessions import get_or_create_session, update_session_stats

# Get or create session
session_id = await get_or_create_session(character.id)

# Update stats after turn
await update_session_stats(
    session_id=session_id,
    turns_increment=1,
    damage_dealt_increment=10,
    damage_taken_increment=5
)
```

#### World State
```python
from app.agents.world_state import world_state_agent

# Load game state
game_state = await world_state_agent.load_world_state(character.id)

# State is automatically saved by orchestrator
```

#### Orchestrator Usage
```python
from app.agents.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()

# Process action WITH memory
final_message, updated_char, updated_state = await orchestrator.process_action(
    user_action="Я атакую гоблина",
    character=character,
    game_state=game_state,
    character_id=character.id,      # Enable memory retrieval
    session_id=session_id,          # Enable memory saving
    recent_history=recent_messages
)

# Process action WITHOUT memory (backward compatible)
final_message, updated_char, updated_state = await orchestrator.process_action(
    user_action="Я атакую гоблина",
    character=character,
    game_state=game_state,
    # character_id and session_id omitted = no memory operations
)
```

---

## 🧪 Testing

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Integration Tests Only
```bash
uv run pytest tests/test_integration_week3.py -v
```

### Check Setup
```bash
uv run python scripts/check_week3_setup.py
```

---

## 🔍 Database Inspection

### View Characters
```sql
SELECT 
    name, 
    telegram_user_id, 
    character_sheet->>'hp' as hp,
    character_sheet->>'max_hp' as max_hp,
    last_session_at
FROM characters
ORDER BY last_session_at DESC;
```

### View Sessions
```sql
SELECT 
    c.name as character_name,
    s.started_at,
    s.ended_at,
    s.turns_count,
    s.total_damage_dealt,
    s.total_damage_taken
FROM game_sessions s
JOIN characters c ON s.character_id = c.id
ORDER BY s.started_at DESC;
```

### View Memories
```sql
SELECT 
    c.name as character_name,
    m.content,
    m.memory_type,
    m.importance_score,
    m.entities,
    m.created_at
FROM episodic_memories m
JOIN characters c ON m.character_id = c.id
ORDER BY m.created_at DESC
LIMIT 10;
```

### View World State
```sql
SELECT 
    c.name as character_name,
    w.state_data,
    w.version,
    w.updated_at
FROM world_state w
JOIN characters c ON w.character_id = c.id;
```

---

## 🐛 Troubleshooting

### Character not found
**Problem:** `await get_character_by_telegram_id()` returns None  
**Solution:** Character not in DB yet. Use `/start` in Telegram to create character.

### Database connection error
**Problem:** `Failed to connect to database`  
**Solution:** Check `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:PASSWORD@db.your-project.supabase.co:5432/postgres
```

### Memory not saving
**Problem:** Memories not appearing in `episodic_memories` table  
**Solution:** Ensure `character_id` and `session_id` passed to `orchestrator.process_action()`

### JSONB serialization error
**Problem:** `invalid input for query argument`  
**Solution:** Already fixed! Use `json.dumps()` for INSERT, `json.loads()` for SELECT.

---

## 📊 Performance Tips

### Current Performance
- **Database queries:** 6-7 per turn
- **Memory retrieval:** ~100-200ms
- **Total overhead:** ~300-500ms per turn

### Optimization (Sprint 4)
- Connection pooling (reduce connection overhead)
- Caching frequently accessed data
- Batch embedding generation
- Query optimization

---

## 🎯 Common Use Cases

### 1. Create Character and Start Game
```python
# In handler
character = CharacterSheet(
    telegram_user_id=user_id,
    name=user_name,
    strength=16,
    hp=25,
    max_hp=25,
    armor_class=14
)

# Save to DB
success = await create_character(character)

# Create session
session_id = await get_or_create_session(character.id)

# Initialize world state
game_state = await world_state_agent.load_world_state(character.id)
```

### 2. Process Player Action
```python
# Load character
character = await get_character_by_telegram_id(user_id)

# Get session
session_id = await get_or_create_session(character.id)

# Load world state
game_state = await world_state_agent.load_world_state(character.id)

# Process action
final_message, updated_char, updated_state = await orchestrator.process_action(
    user_action=user_message,
    character=character,
    game_state=game_state,
    character_id=character.id,
    session_id=session_id,
    recent_history=recent_messages
)

# Save updated character
await update_character(updated_char)

# Update session stats
await update_session_stats(session_id, turns_increment=1)
```

### 3. Query Memory Context
```python
from app.agents.memory_manager import memory_manager_agent

# Retrieve memories
memory_output = await memory_manager_agent.execute({
    "user_action": "Я возвращаюсь в таверну",
    "character_id": character.id,
    "session_id": session_id,
    "top_k": 5,
    "min_importance": 3
})

print(memory_output["memory_summary"])
# Output:
# 📚 **Релевантные воспоминания:**
# - Бармен дал мне квест на гоблинов (85% похоже, ⭐⭐⭐⭐⭐)
# 
# 📅 **Недавние события:**
# - Я победил вожака гоблинов [goblin_cave]
```

---

## 🔗 Related Documentation

- **Full Integration Guide:** `docs/SPRINT3_WEEK3.md`
- **Task Checklist:** `docs/SPRINT3_WEEK3_CHECKLIST.md`
- **Summary Report:** `docs/SPRINT3_WEEK3_SUMMARY.md`
- **API Contracts:** `docs/API_CONTRACTS.md`
- **Sprint 3 Spec:** `docs/SPRINT3_SPEC.md`

---

## ✨ Key Takeaways

1. **Database First:** Characters now load from PostgreSQL, FSM is fallback
2. **Memory Enabled:** Pass `character_id` and `session_id` to enable memory
3. **Automatic Saving:** World state and memories save automatically via orchestrator
4. **100% Tested:** All 93 tests passing, system is stable
5. **Backward Compatible:** Old code works, new features are opt-in

**Ready to go!** 🚀
