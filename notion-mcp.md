 Ready to code?                                                                         │
│                                                                                        │
│ Here is Claude's plan:                                                                 │
│ ╭────────────────────────────────────────────────────────────────────────────────────╮ │
│ │ MCP Notion Recipe Updater Implementation Plan                                      │ │
│ │                                                                                    │ │
│ │ Overview                                                                           │ │
│ │                                                                                    │ │
│ │ Add intelligent Notion recipe updating to Hey Chef using MCP (Model Context        │ │
│ │ Protocol) with audio feedback and change tracking.                                 │ │
│ │                                                                                    │ │
│ │ Core Features                                                                      │ │
│ │                                                                                    │ │
│ │ 1. MCP Integration                                                                 │ │
│ │                                                                                    │ │
│ │ - Install and configure Notion MCP server                                          │ │
│ │ - Connect to existing Notion setup (leveraging current notion_api.py)              │ │
│ │ - Enable Claude to read/write recipe pages in markdown format                      │ │
│ │                                                                                    │ │
│ │ 2. Audio Notification System                                                       │ │
│ │                                                                                    │ │
│ │ - Add custom notification sound (ding/chime) for Notion updates                    │ │
│ │ - Play immediately when Notion request detected                                    │ │
│ │ - Integrate with existing TTS system in src/audio/text_to_speech.py                │ │
│ │                                                                                    │ │
│ │ 3. LLM-Based Recipe Updater (Separate Thread)                                      │ │
│ │                                                                                    │ │
│ │ - Dedicated LLM instance with specialized system prompt                            │ │
│ │ - Input: Original recipe markdown + conversation context + specific update         │ │
│ │ - Output: Updated recipe markdown with intelligent placement                       │ │
│ │ - System prompt optimized for recipe editing and formatting preservation           │ │
│ │                                                                                    │ │
│ │ 4. Change Tracking & Session Cache                                                 │ │
│ │                                                                                    │ │
│ │ - Track all Notion updates in Streamlit session state                              │ │
│ │ - Store: timestamp, change description, recipe section, status                     │ │
│ │ - Enable end-of-session review: "What changes were made to my recipe?"             │ │
│ │ - Allow modifications: "Change that garlic timing to 45 seconds"                   │ │
│ │                                                                                    │ │
│ │ 5. Natural Language Integration                                                    │ │
│ │                                                                                    │ │
│ │ - No hardcoded phrases - LLM detects update requests naturally                     │ │
│ │ - Examples: "add this to my recipe", "save this timing", "update the ingredient    │ │
│ │ notes"                                                                             │ │
│ │ - Immediate confirmation: "Sure, I'll add that to your recipe..."                  │ │
│ │ - Background processing with audio feedback                                        │ │
│ │                                                                                    │ │
│ │ Implementation Steps                                                               │ │
│ │                                                                                    │ │
│ │ Phase 1: MCP Setup                                                                 │ │
│ │                                                                                    │ │
│ │ - Install Notion MCP server (official or ccabanillas/notion-mcp)                   │ │
│ │ - Create MCP configuration file for Claude Code                                    │ │
│ │ - Test basic read/write operations with existing recipes                           │ │
│ │                                                                                    │ │
│ │ Phase 2: Audio & UI Enhancement                                                    │ │
│ │                                                                                    │ │
│ │ - Add notification sound file to project                                           │ │
│ │ - Extend src/ui/app.py with audio notification function                            │ │
│ │ - Integrate with existing Streamlit interface                                      │ │
│ │                                                                                    │ │
│ │ Phase 3: Recipe Updater LLM                                                        │ │
│ │                                                                                    │ │
│ │ - Create separate LLM client for recipe updates                                    │ │
│ │ - Design specialized system prompt for markdown recipe editing                     │ │
│ │ - Implement context passing (original recipe + conversation + request)             │ │
│ │                                                                                    │ │
│ │ Phase 4: Change Tracking                                                           │ │
│ │                                                                                    │ │
│ │ - Add session state management for Notion changes                                  │ │
│ │ - Create change cache data structure                                               │ │
│ │ - Implement review and modification commands                                       │ │
│ │                                                                                    │ │
│ │ Phase 5: Integration & Testing                                                     │ │
│ │                                                                                    │ │
│ │ - Connect all components through existing voice interface                          │ │
│ │ - Test workflow: conversation → update request → audio feedback → Notion update    │ │
│ │ - Verify change tracking and review functionality                                  │ │
│ │                                                                                    │ │
│ │ Technical Architecture                                                             │ │
│ │                                                                                    │ │
│ │ File Structure                                                                     │ │
│ │                                                                                    │ │
│ │ src/                                                                               │ │
│ │ ├── mcp/                                                                           │ │
│ │ │   ├── __init__.py                                                                │ │
│ │ │   ├── notion_client.py      # MCP Notion integration                             │ │
│ │ │   └── recipe_updater.py     # LLM-based recipe updater                           │ │
│ │ ├── audio/                                                                         │ │
│ │ │   ├── notifications.py     # Audio notification system                           │ │
│ │ │   └── sounds/                                                                    │ │
│ │ │       └── notion_update.wav # Notification sound                                 │ │
│ │ └── ui/                                                                            │ │
│ │     └── app.py               # Enhanced with change tracking                       │ │
│ │                                                                                    │ │
│ │ Workflow                                                                           │ │
│ │                                                                                    │ │
│ │ 1. "Hey Chef" wake word detection                                                  │ │
│ │ 2. Speech-to-text via Whisper                                                      │ │
│ │ 3. LLM processes request, detects if Notion update needed                          │ │
│ │ 4. If Notion update: Play notification sound + "Sure, I'll add that..."            │ │
│ │ 5. Fetch current recipe via MCP                                                    │ │
│ │ 6. Recipe updater LLM processes: original + context + request → updated markdown   │ │
│ │ 7. Write updated recipe back to Notion via MCP                                     │ │
│ │ 8. Cache change in session state                                                   │ │
│ │ 9. Continue with cooking response if additional question asked                     │ │
│ │                                                                                    │ │
│ │ End-of-Session Features                                                            │ │
│ │                                                                                    │ │
│ │ - "What changes were made?" → Review all cached changes                            │ │
│ │ - "Change that timing to X" → Modify specific cached change + update Notion        │ │
│ │ - Full audit trail of recipe evolution during cooking session                      │ │
│ │                                                                                    │ │
│ │ Benefits                                                                           │ │
│ │                                                                                    │ │
│ │ - Natural language integration (no hardcoded phrases)                              │ │
│ │ - Immediate audio feedback for Notion operations                                   │ │
│ │ - Intelligent recipe placement using LLM                                           │ │
│ │ - Full change tracking and modification capability                                 │ │
│ │ - Minimal impact on conversation speed for normal cooking questions                │ │
│ │ - Builds up recipes with real cooking insights over time        