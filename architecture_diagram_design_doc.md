# Project Architecture Design Document

## Architecture Diagram

```
+-------+         +------------------+         +-----------+         +-----+
| User  | <--->   | Client Interface | <--->   | MCP Server| <--->   | LLM |
+-------+         +------------------+         +-----------+         +-----+
    |                   |                        |                     |
    | 1. User Input     |                        |                     |
    |------------------>|                        |                     |
    |                   | 2. Sends Request       |                     |
    |                   |----------------------->|                     |
    |                   |                        | 3. Calls LLM/Tools  |
    |                   |                        |-------------------->|
    |                   |                        |<--------------------|
    |                   | 4. Response            |                     |
    |                   |<-----------------------|                     |
    | 5. Output         |                        |                     |
    |<------------------|                        |                     |
```

**Entities:**
- **User**: The end user interacting with the system.
- **Client Interface**: Web UI, Streamlit app, or API client.
- **MCP Server**: FastAPI server, exposing endpoints via MCP, integrating with LLM and cloud services.
- **LLM**: Large Language Model, providing AI-powered responses or automation.

---

## Implementation & Framework/SDK Usage

- **FastAPI**: Main backend framework for REST and async endpoints.
- **FastMCP SDK**: Exposes endpoints as MCP tools, enabling LLM orchestration and tool usage.
- **LLM (Large Language Model)**: Used for intelligent automation, task execution, or chat.
- **Streamlit** (if present): For rapid UI prototyping or dashboard.
- **httpx**: For async HTTP requests to external APIs (e.g., CodeArts Pipeline).
- **Uvicorn**: ASGI server to run FastAPI app.
- **requests**: For synchronous HTTP requests (if needed).
- **Authentication**: Secured via environment variable for API tokens.
- **Logging**: For monitoring and debugging.

---

## Explanation Points for Presentation

- Modular system: client interface can be web UI, CLI, or API consumer.
- MCP Server orchestrates business logic, integrates with LLM and cloud services.
- LLM enables automation, smart responses, and advanced features.
- Extensible and cloud-ready: new tools or endpoints can be added easily.
- Secure and scalable due to FastAPI’s async nature and token-based auth.

---

## How to Use
- Display this document as a slide or printout.
- Copy the diagram and bullet points into your PowerPoint slide if needed.
- Use the architecture diagram to explain the flow and modularity.
