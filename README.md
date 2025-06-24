### Setup Backend Server

# Installing uv on Windows - Recommended Method

## Prerequisites

- Windows 10 or Windows 11
- PowerShell (comes pre-installed with Windows)
- Internet connection

## Installation Steps

### Step 1: Open PowerShell
1. Press `Win + X` and select **"Windows PowerShell"** or **"Terminal"**
2. Alternatively, press `Win + R`, type `powershell`, and press Enter

### Step 2: Run the Installation Command
Copy and paste this command into PowerShell and press Enter:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 3: Wait for Installation
The installer will automatically:
- Download the latest version of uv
- Install it to your system
- Configure your PATH environment variable

### Step 4: Verify Installation
Close and reopen PowerShell, then run:

```powershell
uv --version
```

You should see output showing the installed version of uv.

### Step 5: Test Basic Functionality
Run this command to see the help menu:

```powershell
uv --help
```

That's it! uv is now installed and ready to use as a single tool to replace pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, and more.

## Quick Start
```powershell
# Create a virtual environment
uv venv

# Activate it
.venv\Scripts\activate

# Install a package
uv pip install requests
```

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
