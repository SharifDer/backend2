### Setup Backend Server

```markdown
# Project Setup

```bash
uv sync
```



Create required directories and files:

```
mkdir .vscode
mkdir secrets
```

Add these files (I'll need to provide them):

**`.vscode/launch.json`** - VS Code debug configuration

**`secrets/`** directory with:
- `ggl_bucket_sa.json`
- `launch.json`
- `postgres_db.json`
- `secrets_firebase.json`
- `secrets_gmap.json`
- `secrets_llm.json`
- `secret_dev-s-locator-SA.json`
- `secret_LLM_api_key.json`
- `secret_stripe.json`

Run Backend Server
Press `F5` in VS Code

## MCP Server

Run MCP Server
```
f:/git/s_locator/my_middle_API/.venv/Scripts/python.exe f:/git/s_locator/my_middle_API/tool_bridge_mcp_server/mcp_server.py
```

Inspect MCP Server
```
mcp dev tool_bridge_mcp_server/mcp_server.py
```
