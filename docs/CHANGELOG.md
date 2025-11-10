# CHANGELOG & Technical Fix Log

Consolidated record of important fixes, migrations, and architectural decisions (replaces individual BUGFIX_*.md and MARKDOWN_FIX.md files).

## 2025-11 Sprint 3 Fixes & Changes

### Enemy Damage Application
Issue: Damage sometimes not applied.
Fix: Apply damage earlier in orchestrator; single HP mutation path.

### Enemy Counterattack Display
Issue: Missing or malformed enemy retaliation.
Fix: Structured `enemy_attacks` list passed through agents.

### Combat State Markdown Consistency
Issue: Inconsistent emoji/line breaks.
Fix: Centralized formatting template + sanitization.

### Session Restore
Issue: Lost continuity after restart.
Fix: DB-first load of character/session/world state in handlers.

### JSON Output Leakage
Issue: Raw JSON fragments in narrative.
Fix: Dual-stage parsing & stripping before synthesis.

### Markdown Parsing Failures
Issue: Telegram formatting errors.
Fix: Escaping + normalization layer.

### Halfvec Migration
Change: vector -> halfvec(2560) for embeddings.
Benefit: ~50% storage reduction, improved query performance.

### CrewAI Deferral
Decision: Keep custom orchestrator for lower complexity/latency; revisit in Sprint 4.

## Deprecated Individual Files (Removed)
BUGFIX_COMBAT_STATE_MARKDOWN.md, BUGFIX_ENEMY_COUNTERATTACK_DISPLAY.md, BUGFIX_ENEMY_DAMAGE.md, BUGFIX_JSON_OUTPUT.md, BUGFIX_SESSION_RESTORE.md, MARKDOWN_FIX.md

## Next Documentation Improvements
- Automate changelog append via commit hook
- Link test cases to each fix
- Add semantic version tags