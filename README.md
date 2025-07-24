```markdown
# Backend Server Setup Guide

This guide will help you set up and run the backend server on your Windows computer.

## What You'll Need
- The zip file I gave you

## Step 1: Project Files
1. git clone the repo
2. Extract zip file to root of project

## Step 2: Install uv (Python Package Manager)
### Open PowerShell
1. Press `Win + X` and select **"Windows PowerShell"** or **"Terminal"**
2. Alternatively, press `Win + R`, type `powershell`, and press Enter

### Install uv
Copy and paste this command into PowerShell and press Enter:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Wait for the installation to complete, then close and reopen PowerShell.

### Verify Installation
Test that uv is working by running:
```powershell
uv --version
```
You should see a version number displayed.

## Step 3: Download and Install VS Code
1. Go to https://code.visualstudio.com/
2. Click **"Download for Windows"**
3. Run the downloaded installer and follow the setup wizard
4. Accept all default settings during installation

## Step 4: Set Up the Project
1. Open VS Code
2. Click **"File"** → **"Open Folder"**
3. Navigate to and select the project folder you extracted in Step 1
4. VS Code will open the project

### Install Project Dependencies
1. In VS Code, open the terminal: **"Terminal"** → **"New Terminal"**
2. Run this command:
```bash
uv sync
```
This will install all the required packages for the project.

## Step 5: Configure Python Interpreter
1. In VS Code, press `Ctrl + Shift + P` to open the command palette
2. Type "Python: Select Interpreter" and select it
3. Choose the interpreter that shows `.venv` in the path (this is the virtual environment uv created)

## Step 6: Run the Backend Server
1. Make sure you have the main Python file open (usually something like `main.py` or `app.py`)
2. Press **F5** to start the server
3. The server should start running and you'll see output in the terminal

## Troubleshooting
- If F5 doesn't work, make sure you have a Python file open and selected
- If you can't find the Python interpreter with `.venv`, try running `uv sync` again
- If you get permission errors, make sure you're running as administrator
