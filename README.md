# MCP Server Project

## Overview
This project implements an MCP (Model Context Protocol) server using FastAPI and FastMCP, designed to integrate with an LLM and cloud services (such as Huawei CodeArts Pipeline). It also supports a client interface for user interaction.

---

## Architecture
- **User** interacts with the **Client Interface** (web UI, Streamlit, or API client)
- **Client Interface** sends requests to the **LLM** (Large Language Model)
- **LLM** interprets intent and triggers **MCP Tools** on the **MCP Server** if needed
- **MCP Server** (FastAPI + FastMCP) executes tools, integrates with cloud APIs, and returns results to the LLM

---

## Requirements

### MCP Server
- **Python 3.9+**
- **Dependencies:**
  - fastapi
  - fastmcp
  - httpx
  - uvicorn
  - requests
  - streamlit (if using Streamlit UI)
- **Environment Variable:**
  - `CODEARTS_AUTH_TOKEN` (for authenticating with Huawei CodeArts Pipeline)

### Client App (chat_app.py)
- Streamlit-based web UI for chatting with the LLM and invoking MCP tools
- Connects to the MCP Server and lists available tools/resources
- Handles chat messages, triggers LLM, and MCP tool calls

#### Requirements
- Python 3.9+
- Dependencies:
  - streamlit
  - openai
  - mcp (client)

#### Setup & Run
1. Install dependencies (already in requirements.txt):
   ```bash
   pip install -r requirements.txt
   ```
2. Run the client app:
   ```bash
   streamlit run client/chat_app.py
   ```
3. In the web UI, enter the MCP Server address (e.g., http://localhost:8000/mcp) and connect.
4. Start chatting, sending prompts, and invoking tools via the interface.

#### Notes
- Requires access to an LLM (e.g., OpenAI API key if using OpenAI).
- The client app will auto-discover available MCP tools from the server.

### LLM
- Any Large Language Model that supports tool-calling via MCP (e.g., OpenAI, local LLMs, etc.)

---

## Installation
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set the required environment variable:
   ```bash
   export CODEARTS_AUTH_TOKEN=your_token_here  # On Windows, use 'set' instead of 'export'
   ```

---

## Running the MCP Server
```bash
uvicorn server.mcp_server:app --reload
```

Or, if using the FastMCP runner:
```bash
python server/mcp_server.py
```

---

## Usage
- Use the client interface to send prompts or commands.
- The LLM will interpret the request and trigger MCP tools if needed.
- Results will be returned to the client interface.

---

## Notes
- Ensure your `CODEARTS_AUTH_TOKEN` is valid for accessing Huawei CodeArts Pipeline APIs.
- The architecture is modular and can be extended with more MCP tools or endpoints.
- For UI, you can use Streamlit or any other web framework.
