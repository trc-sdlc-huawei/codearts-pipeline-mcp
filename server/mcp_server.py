import asyncio
import logging
from fastapi import FastAPI
from fastmcp import FastMCP
import httpx

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__) # Get a logger for this module

# Token for authentication
import os
TOKEN = os.getenv("CODEARTS_AUTH_TOKEN")
if not TOKEN:
    raise RuntimeError("CODEARTS_AUTH_TOKEN environment variable is not set. Please set it to your CodeArts API token.")


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

# Initialize FastMCP, linking it to your FastAPI app
mcp_instance = FastMCP.from_fastapi(app=app)

@mcp_instance.tool()
async def mcp0_codearts_get_pipelines(project_id: str) -> dict:
    """
    Get list of CodeArts pipelines for a given project ID.
    Args:
        project_id (str): The project ID to query pipelines for.
    Returns:
        dict: The pipelines list or error message.
    """
    logger.info(f"[MCP Tool] mcp0_codearts_get_pipelines called with project_id={project_id}")
    url = f"https://cloudpipeline-ext.ap-southeast-3.myhuaweicloud.com/v5/{project_id}/api/pipelines/list"
    headers = {"x-auth-token": TOKEN}
    body = {}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            pipelines = response.json()
            return pipelines
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        logger.error(f"General error: {type(e).__name__} - {e}")
        return {"error": f"General error: {type(e).__name__} - {str(e)}"}

@mcp_instance.tool()
async def mcp0_codearts_create_pipeline(name: str, project_id: str) -> dict:
    """
    Create a CodeArts pipeline for a given project ID.
    Args:
        name (str): The name of the pipeline.
        project_id (str): The project ID for the pipeline.
    Returns:
        dict: The creation status or error message.
    """
    logger.info(f"[MCP Tool] mcp0_codearts_create_pipeline called with name={name}, project_id={project_id}")
    url = f"https://cloudpipeline-ext.ap-southeast-3.myhuaweicloud.com/v5/{project_id}/api/pipelines"
    headers = {"x-auth-token": TOKEN, "Content-Type": "application/json"}

    pipelineDefinition = "eyJzdGFnZXMiOlt7Im5hbWUiOiJTdGFnZV8xIiwic2VxdWVuY2UiOiIwIiwiam9icyI6W3siaWQiOiIiLCJpZGVudGlmaWVyX29sZCI6bnVsbCwic3RhZ2VfaW5kZXgiOm51bGwsInR5cGUiOm51bGwsIm5hbWUiOiJOZXcgSm9iIiwiYXN5bmMiOm51bGwsImlkZW50aWZpZXIiOiJKT0JfSlhKd3ciLCJzZXF1ZW5jZSI6MCwiY29uZGl0aW9uIjoiJHt7IGRlZmF1bHQoKSB9fSIsInN0cmF0ZWd5Ijp7InNlbGVjdF9zdHJhdGVneSI6InNlbGVjdGVkIn0sInRpbWVvdXQiOiIiLCJyZXNvdXJjZSI6bnVsbCwic3RlcHMiOltdLCJzdGFnZV9pZCI6IjE3NDcwMzEyMzUzNzciLCJwaXBlbGluZV9pZCI6IjJmNWVkYzYxYjlhMjQxN2JhZGZlZjU1Mjg3Njc3NTBkIiwidW5maW5pc2hlZF9zdGVwcyI6bnVsbCwiY29uZGl0aW9uX3RhZyI6bnVsbCwiZXhlY190eXBlIjoiQUdFTlRMRVNTX0pPQiIsImRlcGVuZHNfb24iOltdLCJyZXVzYWJsZV9qb2JfaWQiOm51bGx9XSwiaWRlbnRpZmllciI6IjE3NDcwMzEyMzUzNzc1NTFhYmM5MS00NGE1LTQ4OTgtOWZiYi01YWUxMjBjOWM2ODgiLCJwcmUiOlt7InJ1bnRpbWVfYXR0cmlidXRpb24iOm51bGwsIm11bHRpX3N0ZXBfZWRpdGFibGUiOjAsIm9mZmljaWFsX3Rhc2tfdmVyc2lvbiI6bnVsbCwibmFtZSI6bnVsbCwidGFzayI6Im9mZmljaWFsX2RldmNsb3VkX2F1dG9UcmlnZ2VyIiwiYnVzaW5lc3NfdHlwZSI6bnVsbCwiaW5wdXRzIjpudWxsLCJlbnYiOm51bGwsInNlcXVlbmNlIjowLCJpZGVudGlmaWVyIjpudWxsLCJlbmRwb2ludF9pZHMiOm51bGx9XSwicG9zdCI6bnVsbCwiZGVwZW5kc19vbiI6W10sInJ1bl9hbHdheXMiOmZhbHNlLCJwaXBlbGluZV9pZCI6IjJmNWVkYzYxYjlhMjQxN2JhZGZlZjU1Mjg3Njc3NTBkIn1dfQ=="
    json_data = {"name": name, "definition": pipelineDefinition}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=json_data, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        logger.error(f"General error: {type(e).__name__} - {e}")
        return {"error": f"General error: {type(e).__name__} - {str(e)}"}

if __name__ == "__main__":
    logger.info("Starting server with mcp_instance.run() on http://0.0.0.0:8000/mcp")
    # For deeper debugging of HTTP/transport issues, you might try running Uvicorn directly:
    # import uvicorn
    # uvicorn.run(mcp_instance.http_app(), host="0.0.0.0", port=8000, log_level="trace")
    mcp_instance.run(transport="streamable-http", host="0.0.0.0", port=8000, path="/mcp")
