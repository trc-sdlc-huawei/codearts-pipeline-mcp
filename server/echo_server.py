import asyncio
import logging
from fastapi import FastAPI
from fastmcp import FastMCP

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__) # Get a logger for this module

# Create a FastAPI application instance
app = FastAPI(title="FastAPI app linked with MCP")

async def get_items_data_source_async() -> list[dict]:
    """Helper function to provide item data asynchronously."""
    logger.info("Executing get_items_data_source_async")
    await asyncio.sleep(0.01) # Simulate tiny async I/O
    return [{"id": "item_1", "name": "Item 1"}, {"id": "item_2", "name": "Item 2"}]

@app.get("/items", response_model=list[dict]) # Added response_model for clarity
async def http_get_items_endpoint():
    """FastAPI HTTP endpoint to get items."""
    logger.info("HTTP GET /items called")
    return await get_items_data_source_async()

async def get_pipelines_data_source_async() -> list[dict]:
    """Helper function to provide pipeline data asynchronously."""
    logger.info("Executing get_pipelines_data_source_async")
    await asyncio.sleep(0.01) # Simulate tiny async I/O
    return [{"id": "pipe_1", "name": "Pipeline 1 (MCP)"}, {"id": "pipe_2", "name": "Pipeline 2 (MCP)"}]

@app.get("/pipelines", response_model=list[dict]) # Added response_model for clarity
async def http_get_pipelines_endpoint():
    """FastAPI HTTP endpoint to get pipelines."""
    logger.info("HTTP GET /pipelines called")
    return await get_pipelines_data_source_async()

# Initialize FastMCP, linking it to your FastAPI app
mcp_instance = FastMCP.from_fastapi(app=app)

# Define MCP tools on the mcp_instance
@mcp_instance.tool()
async def list_codearts_pipelines() -> list[dict]:
    """
    Retrieves a list of available CodeArts pipelines.
    Use this tool when the user asks to list, show, or enumerate CodeArts pipelines,
    or asks any question about what CodeArts pipelines exist or are available.
    Returns a list of pipeline objects, each containing an 'id' and 'name'.
    This tool does not accept any input parameters.
    """
    logger.info("[MCP Server Tool] Attempting: list_codearts_pipelines")
    try:
        pipelines_data = await get_pipelines_data_source_async()
        logger.info(f"[MCP Server Tool] 'list_codearts_pipelines' SUCCEEDED, returning: {pipelines_data}")
        return pipelines_data
    except Exception as e:
        logger.error(f"[MCP Server Tool] 'list_codearts_pipelines' ERRORED: {type(e).__name__} - {e}", exc_info=True)
        return {"error": f"Tool list_codearts_pipelines failed: {type(e).__name__} - {str(e)}"}

@mcp_instance.tool()
async def list_items() -> list[dict]:
    """
    Retrieves a list of available general items.
    Use this tool when the user asks to list, show, or enumerate items.
    Returns a list of item objects, each containing an 'id' and 'name'.
    This tool does not accept any input parameters.
    (Note: Consider renaming this tool for more specificity if 'items' is too generic)
    """
    logger.info("[MCP Server Tool] Attempting: list_items")
    try:
        items_data = await get_items_data_source_async()
        logger.info(f"[MCP Server Tool] 'list_items' SUCCEEDED, returning: {items_data}")
        return items_data
    except Exception as e:
        logger.error(f"[MCP Server Tool] 'list_items' ERRORED: {type(e).__name__} - {e}", exc_info=True)
        return {"error": f"Tool list_items failed: {type(e).__name__} - {str(e)}"}

if __name__ == "__main__":
    logger.info("Starting server with mcp_instance.run() on http://0.0.0.0:8000/mcp")
    # For deeper debugging of HTTP/transport issues, you might try running Uvicorn directly:
    # import uvicorn
    # uvicorn.run(mcp_instance.http_app(), host="0.0.0.0", port=8000, log_level="trace")
    mcp_instance.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/mcp")
