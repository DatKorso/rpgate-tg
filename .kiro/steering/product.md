# Product Overview

## RPGate Telegram Bot

AI-powered Game Master Telegram bot that conducts fantasy RPG adventures with game mechanics.

### Core Concept
An intelligent bot that acts as a Game Master, running D&D-style RPG sessions through Telegram. Players interact in natural language, and the bot handles narrative storytelling, dice rolling, combat resolution, and character management.

### Current Status
- **Sprint 1:** ✅ Complete - Basic bot with LLM integration
- **Sprint 2:** ✅ Complete - Multi-agent system with game mechanics
- **Sprint 3:** 🔄 In Progress - Memory system with RAG and database persistence

### Key Features
- Multi-agent AI system (Rules Arbiter, Narrative Director, Response Synthesizer)
- D&D-inspired game mechanics (d20 system, character sheets, combat)
- Character creation with classes (Warrior, Ranger, Mage, Rogue)
- LLM-based intent detection for automatic action resolution
- Game state management (combat tracking, HP, inventory)
- Formatted responses with Markdown and emojis

### Architecture
- **Multi-agent system:** Specialized agents handle different aspects (rules, narrative, synthesis)
- **FSM state management:** Aiogram 3.x for conversation states
- **LLM provider:** OpenRouter for flexible model access (primarily Grok)
- **Future:** PostgreSQL + pgvector for long-term memory (Sprint 3)

### Localization
- **UI/UX:** Russian (all bot messages and player-facing prompts)
- **Code:** English (code, documentation, comments)
- **Prompts:** Centralized in `app/config/prompts.py` (Russian)
