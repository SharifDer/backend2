
# Guide 1: Model Context Protocol (MCP) Server Guide with Data Handles Architecture

## Table of Contents

- [What is MCP and Why Should You Care?](#what-is-mcp-and-why-should-you-care)
- [The Revolution: Before vs After MCPs](#the-revolution-before-vs-after-mcps)
- [How MCP Works: The Complete Flow](#how-mcp-works-the-complete-flow)
- [Data Handles Architecture](#data-handles-architecture)
- [Docker Container Communication](#docker-container-communication)
- [Implementation Details](#implementation-details)
- [Performance Benefits](#performance-benefits)
- [Session Management](#session-management)

---

## What is MCP and Why Should You Care?

The Model Context Protocol (MCP) is a revolutionary way to connect AI models to external tools and services. Instead of manually coding every AI interaction, MCP allows AI models to **autonomously discover and orchestrate tools** to solve complex business location problems.

## The Revolution: Before vs After MCPs

### ❌ Without MCP (Traditional Approach)

```python
# You manually code every step of AI interaction
async def analyze_riyadh_for_logistics_hub():
    # Step 1: You manually fetch POI data
    poi_data = await fetch_dataset({
        "country_name": "Saudi Arabia",
        "city_name": "Riyadh", 
        "boolean_query": "warehouse OR logistics OR distribution_center",
        "action": "full data"
    })
    
    # Step 2: You manually call distance calculations  
    distances = await load_distance_drive_time_polygon({
        "source": {"lat": 24.7136, "lng": 46.6753},
        "destination": {"lat": 24.7500, "lng": 46.7000}
    })
    
    # Step 3: You manually format for AI
    prompt = f"Here's Riyadh logistics data: {poi_data}..."
    
    # Step 4: You manually interpret AI response
    ai_response = await openai.chat.completions.create(
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Step 5: You manually parse and act on response
    if "need demographic data" in ai_response:
        demo_data = await fetch_intelligence_by_viewport(riyadh_viewport)
        # Repeat the whole process...
    
    # Result: 500+ lines of orchestration code for complex workflows
```

### ✅ With MCP (AI Takes Control)

```python
# AI Agent automatically decides what tools to use!
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

# Setup Tool Bridge connection
tool_bridge = MCPServerHTTP(url='http://localhost:8001/sse')
ai_agent = Agent('claude-3-5-sonnet', mcp_servers=[tool_bridge])

# This single line can produce comprehensive analysis
result = await ai_agent.run(
    "Analyze Dammam, Saudi Arabia for opening a new distribution center. "
    "Consider logistics access, competitor locations, demographics, and traffic patterns."
)

# The AI Agent automatically:
# 1. Discovers available tools from your Tool Bridge
# 2. Decides it needs POI data → calls saudi_location_intelligence_fetcher
# 3. Realizes it needs route analysis → calls geospatial_route_calculator 
# 4. Determines it needs demographics → calls population_viewport_analyzer
# 5. Synthesizes all data into actionable business insights
# 6. Presents a complete analysis WITHOUT you coding the orchestration!
```

## How MCP Works: The Complete Flow

### 1. 🚀 Conversation Initialization

```python
User Text Input
      ↓
🤖 AI Agent (Single LLM)
   - Understands user intent
   - Calls MCP Server to get available tools
      ↓
📋 MCP Server (Tool Bridge Container)
   - Returns tool definitions/schemas
   - NO LLM here - just a registry/router
      ↓
🤖 AI Agent (Same LLM)
   - Selects appropriate tool
   - Calls the tool with parameters
      ↓
🔧 Tool Implementation (Tool Bridge Container)
   - Tool = Smart wrapper around endpoints
   - Logic determines which endpoints to call
   - NO LLM needed - just code logic
      ↓
🌐 FastAPI Endpoints
   - /fetch_dataset
   - /process_llm_query  
      ↓
📊 Results back to AI Agent
```

### 2. 🧠 Runtime Tool Discovery
Every conversation, the AI Agent discovers tools fresh:

```python
# This happens at RUNTIME, not build time
async with ai_agent.run_mcp_servers() as session:
    # 🔄 RIGHT HERE - AI Agent calls Tool Bridge's list_tools()
    available_tools = await tool_bridge.list_tools()
    
    # AI Agent reads ALL tool descriptions fresh each time
    for tool in available_tools:
        ai_context.add_tool(
            name=tool.name,
            description=tool.description,  # ← Read at runtime!
            schema=tool.inputSchema        # ← Read at runtime!
        )
    
    # Now AI Agent has tool knowledge for this conversation
    result = await ai_agent.run("Find gas stations in Jeddah")
```

### 3. 🎯 AI Decision Making Process

```
User: "Find the best location for a logistics hub in Riyadh"

🤖 AI Agent's Internal Reasoning:
1. Parse Intent: "logistics hub" + "Riyadh" + "location analysis" 
2. Check Available Tools: Scan tool descriptions for relevant capabilities
   ├── "saudi_location_intelligence_fetcher" mentions "site selection" ✅
   ├── "geospatial_route_calculator" mentions "logistics planning" ✅  
   └── "population_accessibility_scorer" mentions "location rating" ✅
3. Plan Execution: Follow learned business analysis patterns
4. Execute Tools: Call tools in intelligent sequence
5. Synthesize Results: Combine all data into actionable insights
```

### 4. 🔄 Memory and Persistence

| **What** | **When** | **Where** | **Persistence** |
|----------|----------|-----------|-----------------|
| Tool Descriptions | Runtime (every conversation) | Tool Bridge Response | None - Fresh each time |
| Tool Schemas | Runtime (every conversation) | Tool Bridge Response | None - Fresh each time |
| Reasoning Patterns | Pre-trained (model weights) | AI Agent | Permanent |
| Conversation Memory | Runtime (during conversation) | AI Agent Context | Deleted after conversation |
| Tool Results | Runtime (during conversation) | AI Agent Context | Deleted after conversation |

## Data Handles Architecture

### Overall Architecture - Data Handles Flow

```python
┌─────────────────┐                    ┌─────────────────┐                    ┌─────────────────┐
│                 │                    │   Tool Bridge   │                    │  FastAPI App    │
│   AI Agent      │                    │   Container     │                    │   Container     │
│  (PydanticAI)   │                    │   Port: 8001    │                    │   Port: 8000    │
│                 │                    │ + JSON Storage  │                    │                 │
│                 │                    │                 │                    │                 │
└─────────────────┘                    └─────────────────┘                    └─────────────────┘
         │                                       │                                       │
         │ 1. Connect via MCP Protocol          │                                       │
         │    (HTTP+SSE to port 8001)           │                                       │
         ├──────────────────────────────────────►│                                       │
         │                                       │                                       │
         │ 2. User Query:                        │                                       │
         │    "Analyze Jeddah for warehouse"     │                                       │
         ├──────────────────────────────────────►│                                       │
         │                                       │                                       │
         │                                       │ 3. Tool Bridge decides: need data    │
         │                                       │    Calls: saudi_location_fetcher     │
         │                                       │                                       │
         │                                       │ 4. HTTP POST to FastAPI Container    │
         │                                       ├──────────────────────────────────────►│
         │                                       │   /fastapi/fetch_dataset              │
         │                                       │                                       │
         │                                       │ 5. Store data in temp JSON file      │
         │                                       │◄──────────────────────────────────────┤
         │                                       │   /tmp/session_abc123/               │
         │                                       │   real_estate_jeddah.json            │
         │                                       │                                       │
         │ 6. MCP Response: DATA HANDLE          │                                       │
         │    (NOT the actual data)              │                                       │
         │◄──────────────────────────────────────┤                                       │
         │   {                                   │                                       │
         │     "data_handle": "real_estate_      │                                       │
         │       jeddah_20241206_abc123",        │                                       │
         │     "summary": {count: 50000},        │                                       │
         │     "expires_at": "2024-12-06T18:00"  │                                       │
         │   }                                   │                                       │
         │                                       │                                       │
         │ 7. AI Agent calls analysis with handle│                                       │
         │    "analyze_warehouse_locations"       │                                       │
         ├──────────────────────────────────────►│                                       │
         │   {                                   │                                       │
         │     "real_estate_handle": "real_      │ 8. Analysis tool reads JSON file     │
         │       estate_jeddah_20241206_abc123", │    /tmp/session_abc123/              │
         │     "criteria": {...}                 │    real_estate_jeddah.json           │
         │   }                                   │                                       │
         │                                       │                                       │
         │ 9. MCP Response: Final Analysis       │                                       │
         │    (Processed insights, not raw data) │                                       │
         │◄──────────────────────────────────────┤                                       │
```

### Data Validation Flow with Temporary JSON Storage

```python
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   all_types/    │       │   Tool Bridge   │       │  FastAPI App    │
│                 │       │   Container     │       │   Container     │
│ ReqFetchDataset │◄──────┤ 1. Import       │       │                 │
│ ResFetchDataset │       │    your models  │       │                 │
│ DataHandle      │       │                 │       │                 │
│ SessionInfo     │       │ 2. Generate     │       │                 │
│                 │       │    tool schema: │       │                 │
│                 │       │    ReqFetch     │       │                 │
│                 │       │    Dataset.     │       │                 │
│                 │       │    model_json   │       │                 │
│                 │       │    _schema()    │       │                 │
│                 │       │                 │       │                 │
│                 │       │ 3. AI Agent     │       │                 │
│                 │       │    calls tool   │       │                 │
│                 │       │    via MCP      │       │                 │
│                 │       │                 │       │                 │
│                 │       │ 4. Validate:    │◄──────┤ 5. Your existing │
│                 │       │    ReqFetch     │       │    validation   │
│                 │       │    Dataset.     │       │                 │
│                 │       │    model_       │       │ 6. Return        │
│                 │       │    validate()   │       │    ResFetch     │
│                 │       │         │       │       │    Dataset      │
│                 │       │         ▼       │       │                 │
│                 │       │ 5. HTTP POST ───┼──────►│ 7. Your         │
│                 │       │    to FastAPI   │       │    fetch_dataset│
│                 │       │                 │       │    function     │
│                 │       │ 6. STORE DATA   │       │                 │
│                 │       │    in JSON:     │       │ 8. Returns      │
│                 │       │    /tmp/session_│       │    ResFetch     │
│                 │       │    abc123/      │       │    Dataset      │
│                 │       │    real_estate_ │       │                 │
│                 │       │    jeddah.json  │       │                 │
│                 │       │         │       │       │                 │
│                 │       │         ▼       │       │                 │
│                 │       │ 7. Return HANDLE│       │                 │
│                 │       │    not data:    │       │                 │
│                 │       │    DataHandle   │       │                 │
│                 │       │    model        │       │                 │
│                 │       │         │       │       │                 │
│                 │       │         ▼       │       │                 │
│                 │       │ 8. Stream handle│       │                 │
│                 │       │    to AI Agent  │       │                 │
│                 │       │    via SSE      │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘

Key Changes:
✅ Tools store large datasets in temporary JSON files
✅ AI Agent only receives lightweight handles + summaries  
✅ Analysis tools read data from JSON files using handles
✅ Zero context pollution - AI Agent context stays clean
✅ Session-based cleanup - temp files auto-deleted
```

### Timeline: When Things Happen with Data Handles

#### Build Time
```python
📅 BUILD TIME
├── Three separate Docker containers built
├── all_types/ includes new DataHandle and SessionInfo models
├── Tool Bridge has /tmp/sessions/ directory for JSON storage
├── Your existing Pydantic models work unchanged
└── No AI Agent-Tool Bridge connection yet
```

#### Conversation Start (Runtime)
```python
🚀 CONVERSATION START (Runtime)
├── 1. User creates PydanticAI AI Agent with Tool Bridge servers
├── 2. ai_agent.run_mcp_servers() called
├── 3. AI Agent connects to Tool Bridge via HTTP+SSE (port 8001)
├── 4. Tool Bridge creates unique session: /tmp/sessions/abc123/
├── 5. AI Agent calls bridge.list_tools() via MCP protocol
├── 6. Tool Bridge returns tool definitions (FRESH each time)
├── 7. AI Agent loads tool descriptions into conversation context
└── 8. Ready to process user requests
```

#### During Conversation (Runtime) - Data Handles Flow
```python
💭 DURING CONVERSATION (Runtime) - DATA HANDLES FLOW
├── 9. User asks: "Analyze Jeddah for warehouse location"
├── 10. AI Agent calls: saudi_location_intelligence_fetcher
├── 11. Tool Bridge calls FastAPI, gets full dataset
├── 12. Tool Bridge STORES data in JSON: /tmp/sessions/abc123/real_estate_jeddah.json
├── 13. Tool Bridge returns HANDLE to AI Agent:
│    {
│      "data_handle": "real_estate_jeddah_20241206_abc123",
│      "summary": {"count": 50000, "avg_price": 2500},
│      "schema": {"lat": "float", "lng": "float", "price": "int"},
│      "file_path": "/tmp/sessions/abc123/real_estate_jeddah.json"
│    }
├── 14. AI Agent decides: need warehouse data too
├── 15. AI Agent calls: warehouse_rental_fetcher  
├── 16. Tool Bridge stores warehouse data, returns another handle
├── 17. AI Agent calls: analyze_warehouse_locations with BOTH handles:
│    {
│      "real_estate_handle": "real_estate_jeddah_20241206_abc123",
│      "warehouse_handle": "warehouse_jeddah_20241206_def456", 
│      "criteria": {"max_distance_to_port": 50}
│    }
├── 18. Analysis tool reads BOTH JSON files using handles
├── 19. Analysis tool processes data server-side, returns insights
├── 20. AI Agent synthesizes final answer (NO raw data in context!)
└── 21. Process repeats with existing handles for follow-up questions
```

#### Conversation End
```python
💀 CONVERSATION END
├── Session cleanup: rm -rf /tmp/sessions/abc123/
├── All handles expire and become invalid
├── AI Agent context cleared (was already lightweight!)
└── Next conversation gets fresh session ID
```

## Docker Container Communication

### Dedicated Container Architecture with Shared Pydantic Models

```python
project/
├── fastapi-app/               # Your existing FastAPI backend
│   └──all_types/
│       ├── __init__.py
│       ├── request_dtypes.py      # ReqFetchDataset, ReqPrdcerLyrMapData, etc.
│       ├── response_dtypes.py     # ResFetchDataset, ResLyrMapData, etc.
│       ├── internal_types.py      # UserId, LayerInfo, UserCatalogInfo, etc.
│       └── data_handles.py        # NEW: DataHandle, SessionInfo models
│   └──tool_bridge_mcp_server/     # Tool Bridge (separate container)
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── main.py               # Tool Bridge server
│       └── tools/
│           ├── __init__.py
│           ├── data_fetcher.py
│           ├── market_analyzer.py
│           └── site_optimizer.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── fastapi_app.py        # Your main FastAPI file
│   ├── data_fetcher.py       # Your existing data fetcher
│   └── ... (existing FastAPI code)
└── docker-compose.yml
```

### Container Communication Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Docker Network: app-network                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐                ┌─────────────────────────┐     │
│  │    fastapi-container    │                │   tool-bridge-container │     │
│  │                         │                │                         │     │
│  │  🐍 Your FastAPI App    │                │  🤖 MCP Server          │     │
│  │  📊 data_fetcher.py     │                │  🔧 Tool Definitions    │     │
│  │  🗄️  Your Database      │                │  🌐 HTTP Client         │     │
│  │  🔌 Your Endpoints      │                │  📡 MCP Protocol        │     │
│  │                         │                │  💾 JSON Storage:       │     │
│  │  Port: 8000            │◄──────────────┤  /tmp/sessions/         │     │
│  │                         │ Standard HTTP  │                         │     │
│  │  Volumes:               │                │  Environment:           │     │
│  │  ./all_types:/app/     │                │  FASTAPI_BASE_URL=      │     │
│  │  all_types             │                │  http://fastapi-        │     │
│  │                         │                │  container:8000         │     │
│  │                         │                │                         │     │
│  │                         │                │  Port: 8001 (MCP)      │     │
│  │                         │                │                         │     │
│  │                         │                │  Volumes:               │     │
│  │                         │                │  ./all_types:/app/     │     │
│  │                         │                │  all_types             │     │
│  │                         │                │  ./tmp:/tmp            │     │
│  │                         │                │                         │     │
│  └─────────────────────────┘                └─────────────────────────┘     │
│                                                         │                   │
└─────────────────────────────────────────────────────────┼───────────────────┘
                                                          │
                                    ┌─────────────────────▼───────────────────┐
                                    │            AI Agent                     │
                                    │         (Your Computer)                 │
                                    │                                         │
                                    │  🤖 PydanticAI Agent                   │
                                    │  📡 MCP Protocol Client                │
                                    │  🔗 Data Handle Manager                │
                                    │                                         │
                                    │  Connection:                            │
                                    │  • HTTP+SSE: http://localhost:8001     │
                                    │  • JSON-RPC over persistent stream     │
                                    │  • Real-time bidirectional comms       │
                                    │  • Lightweight handle-based context    │
                                    │                                         │
                                    └─────────────────────────────────────────┘
```

### Communication Flow with Data Handles
1. AI Agent ──MCP Protocol (HTTP+SSE)──► Tool Bridge Container (port 8001)
2. Tool Bridge ──Standard HTTP──► FastAPI Container (port 8000)
3. Tool Bridge ──Store Data──► /tmp/sessions/abc123/data.json
4. Tool Bridge ──Return Handle──► AI Agent (lightweight context)
5. AI Agent ──Handle-based Analysis──► Tool Bridge reads JSON files
6. Both containers share your existing Pydantic models via ./all_types volume
7. Docker internal DNS: fastapi-container:8000, tool-bridge-container:8001
8. AI Agent uses port mapping: localhost:8001 → tool-bridge-container:8001

## Implementation Details

### Tool Discovery & Decision Flow with Handles

```python
                           ┌─────────────────────────────────────┐
                           │         AI Agent Brain              │
                           │                                     │
                           │  🧠 Pre-trained Knowledge:          │
                           │  • Business analysis patterns       │
                           │  • Data handle orchestration        │
                           │  • Multi-step workflow planning     │
                           │                                     │
                           └─────────────────┬───────────────────┘
                                            │
                                            │ User Query
                                            ▼
                           ┌─────────────────────────────────────┐
                           │       AI Agent Reasoning            │
                           │                                     │
                           │  "Analyze Jeddah warehouse" needs:  │
                           │  1. Real estate data → Handle A     │
                           │  2. Warehouse data → Handle B       │
                           │  3. Analysis with A + B → Insights  │
                           │                                     │
                           │  Context stays CLEAN - only handles │
                           │  and summaries, never raw data!     │
                           │                                     │
                           └─────────────────┬───────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────────┐
                           │         Execution Flow              │
                           │                                     │
                           │  Step 1: Call data_fetcher         │
                           │  ├── Returns: Handle A + Summary    │
                           │  └── AI Agent context: 200 tokens   │
                           │                                     │
                           │  Step 2: Call warehouse_fetcher     │
                           │  ├── Returns: Handle B + Summary    │
                           │  └── AI Agent context: 400 tokens   │
                           │                                     │
                           │  Step 3: Call analyzer(A, B)       │
                           │  ├── Reads JSON files server-side   │
                           │  ├── Returns: Business insights     │
                           │  └── AI Agent context: 600 tokens   │
                           │                                     │
                           │  🎯 WITHOUT handles: 2M+ tokens!    │
                           │  ✅ WITH handles: <1K tokens!       │
                           │                                     │
                           └─────────────────────────────────────┘
```

### Type Safety Throughout with Handle Management

```python
# tool-bridge/tools/saudi_data_fetcher.py
from all_types.request_dtypes import ReqFetchDataset
from all_types.response_dtypes import ResFetchDataset
from all_types.data_handles import DataHandle, SessionInfo

class SaudiLocationIntelligenceTool:
    def get_tool_definition(self) -> Tool:
        return Tool(
            name="saudi_location_intelligence_fetcher",
            description="Fetch POI, real estate, and demographic data for Saudi Arabia locations - returns lightweight handle",
            # ✅ Uses your existing Pydantic schema automatically!
            inputSchema=ReqFetchDataset.model_json_schema()
        )
    
    async def execute(self, arguments: dict) -> list[TextContent]:
        # ✅ Validate input using your existing Pydantic model
        validated_request = ReqFetchDataset.model_validate(arguments)
        
        # Call your existing FastAPI endpoint with validated data
        response = await self.http_client.post(
            f"{self.fastapi_url}/fastapi/fetch_dataset",
            json={
                "message": "Fetching Saudi location data via MCP",
                "request_info": {},
                "request_body": validated_request.model_dump()
            }
        )
        
        # ✅ Validate response using your existing Pydantic model
        validated_response = ResFetchDataset.model_validate(response.json()["data"])
        
        # 🔑 NEW: Store data and create handle instead of returning raw data
        data_handle = await self.store_data_and_create_handle(
            data=validated_response,
            data_type="real_estate",
            location="saudi_arabia",
            session_id=self.session_id
        )
        
        # ✅ Return handle instead of massive dataset
        return [TextContent(
            type="text", 
            text=f"Saudi location data fetched and stored. Handle: {data_handle.data_handle}. "
                 f"Summary: {data_handle.summary['count']} records covering {data_handle.summary['districts']} districts."
        )]
```

### How AI Agent Learns Your Tools with Data Handles

```python
def get_tool_definition(self) -> Tool:
    return Tool(
        name="saudi_location_intelligence_fetcher",
        
        # 🧠 AI Agent reads this to understand WHEN to use the tool
        description="""
        Fetch comprehensive location data for Saudi Arabia including Points of Interest (POI), 
        real estate properties, demographic information, and traffic patterns.
        
        🎯 Use this tool when you need to:
        - Analyze business competition in Saudi cities (Riyadh, Jeddah, Dammam)
        - Find nearby amenities like gas stations, restaurants, mosques
        - Gather market research data for site selection in KSA
        - Understand local business landscape in Saudi regions
        - Research foot traffic and accessibility in Saudi locations
        
        ⚡ PERFORMANCE NOTE: This tool returns a lightweight data handle instead of raw data,
        keeping your context clean and fast while preserving full dataset access for analysis tools.
        
        🔗 OUTPUT: Returns DataHandle object with summary statistics and data reference.
        Use the returned handle with analysis tools for processing.
        
        This tool is essential for Saudi Arabia location analysis, market research, 
        competitive intelligence, and business planning tasks. Supports Arabic and English queries.
        """,
        
        # 🎯 AI Agent reads the schema to understand HOW to use the tool
        inputSchema=ReqFetchDataset.model_json_schema()
    )
```

## Performance Benefits

### Context Efficiency Comparison

```python
# ❌ WITHOUT Data Handles (Your Current Flow)
AI Agent Context:
├── Tool schemas: 2,000 tokens
├── Real estate data: 800,000 tokens (1M records)  
├── Warehouse data: 300,000 tokens (100K records)
├── Analysis results: 5,000 tokens
└── TOTAL: 1,107,000 tokens 💸💸💸

# ✅ WITH Data Handles (Proposed Architecture)  
AI Agent Context:
├── Tool schemas: 2,000 tokens
├── Real estate handle + summary: 100 tokens
├── Warehouse handle + summary: 100 tokens  
├── Analysis results: 5,000 tokens
└── TOTAL: 7,200 tokens ⚡✅

# 🚀 Result: 99.4% reduction in context usage!
```

### Updated Workflow Benefits

```python
# User Request: "Compare 5 Saudi cities for logistics hub"

# Without Handles: AI Agent context explodes
cities_data = 5_000_000_tokens  # 5 cities × 1M tokens each
# = Context overflow, massive costs, slow processing

# With Handles: AI Agent stays efficient  
city_handles = 500_tokens      # 5 handles × 100 tokens each
# = Fast, cheap, scalable to any number of cities
```

## Session Management

```python
# Session Lifecycle with Temporary JSON Storage

📁 /tmp/sessions/
├── abc123/                    # Session ID (UUID)
│   ├── real_estate_jeddah.json     # Handle: real_estate_jeddah_20241206_abc123
│   ├── warehouse_jeddah.json       # Handle: warehouse_jeddah_20241206_def456  
│   ├── demographics_jeddah.json    # Handle: demographics_jeddah_20241206_ghi789
│   └── session_metadata.json       # Created at, expires at, handle registry
├── def456/                    # Different user session
│   └── ...
└── cleanup_job.py            # Periodic cleanup of expired sessions

# Handle Format
{
  "data_handle": "real_estate_jeddah_20241206_abc123",
  "session_id": "abc123", 
  "data_type": "real_estate",
  "location": "jeddah",
  "created_at": "2024-12-06T10:00:00Z",
  "expires_at": "2024-12-06T18:00:00Z",
  "file_path": "/tmp/sessions/abc123/real_estate_jeddah.json",
  "summary": {
    "record_count": 50000,
    "avg_price": 2500,
    "districts": ["Downtown", "Industrial", "Residential"]
  },
  "schema": {
    "lat": "float", 
    "lng": "float", 
    "price": "int",
    "type": "string"
  }
}
```

