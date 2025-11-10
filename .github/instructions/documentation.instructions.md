---
applyTo: '**/*.md'
---
# Documentation Rules & Navigation

## 📋 Core Principles

### DO NOT Create
- ❌ `BUGFIX_*.md` → Use `docs/development/CHANGELOG.md`
- ❌ `SPRINTX_WEEKY_*.md` → Use `docs/development/SPRINTX_PROGRESS.md`
- ❌ Temporary status files → Update existing tracking documents
- ❌ Duplicate documentation → Reference existing docs instead

### DO Update
- ✅ `docs/development/CHANGELOG.md` - All changes (features, fixes, refactors)
- ✅ `docs/development/SPRINT3_PROGRESS.md` - Current sprint status
- ✅ `docs/architecture/API_CONTRACTS.md` - Agent interface changes
- ✅ `docs/architecture/STRATEGIC_PLAN.md` - Long-term planning

## 📁 Documentation Structure

### `docs/architecture/` - System Design
- `API_CONTRACTS.md` - Agent communication interfaces (update when agents change)
- `STRATEGIC_PLAN.md` - Product roadmap and technical vision
- `HALFVEC_MIGRATION.md` - Vector embedding implementation strategy

### `docs/development/` - Active Work
- `CHANGELOG.md` - Complete change history (update with every change)
- `SPRINT3_PROGRESS.md` - Current sprint tracking (update weekly)
- `development-plan.md` - Sprint planning and task breakdown

### `docs/archive/` - Historical Records
- `sprint1/`, `sprint2/`, `sprint3/` - Completed sprint documentation
- `CHANGES_CREWAI.md` - Historical architecture decisions
- `MVP_PLAN_UPDATED.md` - Original MVP specification

### `docs/guides/` - Reference Materials
- `DOCUMENTATION_AUDIT_REPORT.md` - Documentation structure analysis

## 🔄 Workflow Guidelines

### When Adding Features
1. Implement code in `app/`
2. Add tests in `tests/`
3. Update `docs/development/CHANGELOG.md` with description
4. If agent interfaces change → Update `docs/architecture/API_CONTRACTS.md`
5. Update `docs/development/SPRINT3_PROGRESS.md` task status

### When Fixing Bugs
1. Fix code and add regression test
2. Document in `docs/development/CHANGELOG.md` under "Fixed" section
3. Reference issue/symptom in changelog entry

### When Refactoring
1. Make code changes
2. Update affected documentation references
3. Document in `docs/development/CHANGELOG.md` under "Changed" section
4. Update architecture docs if structure changes significantly

### When Completing Sprint Tasks
1. Mark task complete in `docs/development/SPRINT3_PROGRESS.md`
2. Summarize achievements in changelog
3. Move completed sprint docs to `docs/archive/sprintX/` when sprint ends

## 📝 Changelog Format

Use semantic versioning categories:
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Fixed** - Bug fixes
- **Removed** - Removed features
- **Security** - Security improvements

Example entry:
```markdown
## [2024-11-10]
### Added
- Memory retrieval with RAG pipeline in `app/memory/episodic.py`

### Fixed
- Combat state not resetting after enemy defeat (#42)
```

## 🔍 Finding Information

- **How agents work?** → `docs/architecture/API_CONTRACTS.md`
- **What's the plan?** → `docs/architecture/STRATEGIC_PLAN.md`
- **What changed recently?** → `docs/development/CHANGELOG.md`
- **Sprint progress?** → `docs/development/SPRINT3_PROGRESS.md`
- **Historical context?** → `docs/archive/sprintX/`
- **Vector embeddings?** → `docs/architecture/HALFVEC_MIGRATION.md`

## ⚠️ Anti-Patterns to Avoid

1. **Creating status files** - Use existing progress tracking
2. **Duplicating information** - Reference existing docs with links
3. **Outdated documentation** - Update docs when code changes
4. **Scattered information** - Consolidate related info in proper location
5. **Missing changelog entries** - Document every meaningful change