import streamlit as st
import asyncio
import json # Added for parsing tool arguments and debug printing
from openai import AsyncOpenAI # Using the official async client
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# --- Configuration ---
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo" # Simpler, endpoint is inferred by client

# --- MCP Connection Management ---
async def async_connect_mcp_server(target_address: str):
    print(f"[DEBUG MCP] Attempting to connect. User provided server_address: {target_address}")
    if not target_address or not target_address.startswith(("http://", "https://")):
        return None, "MCP Server Address must be a valid HTTP/HTTPS URL.", [], []

    print(f"[DEBUG MCP] Using provided target address: {target_address}")
    try:
        print(f"[DEBUG MCP] Attempting to establish HTTP connection with streamablehttp_client to: {target_address}")
        async with streamablehttp_client(target_address) as (read_stream, write_stream, info):
            print("[DEBUG MCP] HTTP connection established. read_stream, write_stream, info obtained.")
            print(f"[DEBUG MCP] Info from streamablehttp_client: {info}")
            print("[DEBUG MCP] Creating ClientSession.")
            async with ClientSession(read_stream, write_stream) as session:
                print("[DEBUG MCP] ClientSession created. Attempting to initialize session...")
                await session.initialize()
                print("[DEBUG MCP] Session initialized successfully.")

                # Attempt to list tools using the newly discovered list_tools() method
                tool_schemas = []
                try:
                    mcp_tools_result = await session.list_tools()
                    print(f"[DEBUG MCP] list_tools() result: {mcp_tools_result}")
                    if hasattr(mcp_tools_result, 'tools') and mcp_tools_result.tools:
                        tool_schemas = mcp_tools_result.tools
                        print(f"[DEBUG MCP] Fetched tool schemas: {tool_schemas}")
                    else:
                        print("[DEBUG MCP] No tool schemas found in list_tools() result object or it's empty.")
                except Exception as e_lt:
                    print(f"[DEBUG MCP] Error calling session.list_tools(): {e_lt}")
                
                # Attempt to list resources
                resources_list = []
                print("[DEBUG MCP] Attempting to list resources...")
                mcp_resources_result = await session.list_resources()
                print(f"[DEBUG MCP] list_resources result: {mcp_resources_result}")
                if hasattr(mcp_resources_result, 'resources') and mcp_resources_result.resources is not None:
                    resources_list = mcp_resources_result.resources
                    print(f"[DEBUG MCP] Extracted resources (from object.resources): {resources_list}")
                else:
                    print("[DEBUG MCP] No resources found or unexpected format for mcp_resources_result.")
                
                print("[DEBUG MCP] Connection, tool and resource listing successful.")
                return None, f"Successfully connected to MCP Server at {target_address}.", resources_list, tool_schemas
    except Exception as e:
        print(f"[DEBUG MCP] EXCEPTION during MCP connection/initialization: {type(e).__name__}: {e}")
        import traceback
        print("[DEBUG MCP] Traceback:")
        traceback.print_exc()
        return None, f"Failed to connect to MCP Server at {target_address}: {e}", [], []

async def async_read_mcp_resource(server_address, resource_uri: str):
    try:
        print(f"[DEBUG MCP] Attempting to read resource: {resource_uri}")
        async with streamablehttp_client(server_address) as (read_stream, write_stream, info):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                content = await session.read_resource(uri=resource_uri)
                if isinstance(content, bytes):
                    content = content.decode()
                print(f"[DEBUG MCP] Read resource content: {content if content else '<empty>'}")
                return content if content else "Resource is empty or content could not be decoded."
    except Exception as e:
        print(f"[DEBUG MCP] Error reading MCP resource {resource_uri}: {e}")
        return f"Error reading resource {resource_uri}: {e}"

# --- OpenAI Interaction Logic ---
# Helper function to format MCP tool schemas for OpenAI
def format_mcp_tools_for_openai(mcp_tools):
    if not mcp_tools:
        return []
    openai_tools = []
    for tool in mcp_tools:
        parameters = tool.inputSchema
        if not isinstance(parameters, dict): # Ensure inputSchema is a dict
            parameters = {"type": "object", "properties": {}}
        
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description.strip() if tool.description else "",
                "parameters": parameters
            }
        })
    return openai_tools

async def handle_chat_message(prompt_text: str):
    """Handles the user's chat message, interacts with OpenAI and MCP tools."""
    st.session_state.messages.append({"role": "user", "content": prompt_text})

    client = AsyncOpenAI(api_key=st.session_state.openai_api_key) # Add base_url if not default
    
    openai_tool_list = []
    if "mcp_tool_schemas" in st.session_state and st.session_state.mcp_tool_schemas:
        openai_tool_list = format_mcp_tools_for_openai(st.session_state.mcp_tool_schemas)
        if openai_tool_list:
            print(f"[DEBUG CHAT] Passing these tools to OpenAI: {json.dumps(openai_tool_list, indent=2)}")

    def get_message_history_for_openai(messages):
        # If the last message is a user message, send up to the last assistant/user exchange for context
        # If the last message is a tool call, use get_last_tool_call_block
        if not messages:
            return []
        # If the last message is a user message
        if messages[-1]['role'] == 'user':
            # Optionally, include more history for context (here, just the last exchange)
            # Find previous assistant message (if any)
            idx = None
            for i in range(len(messages) - 2, -1, -1):
                if messages[i]['role'] == 'assistant':
                    idx = i
                    break
            if idx is not None:
                return messages[idx:]
            else:
                return [messages[-1]]
        # If the last message is a tool message, use the last tool call block
        else:
            # Reuse the previous helper
            def get_last_tool_call_block(messages):
                idx = None
                for i in range(len(messages) - 1, -1, -1):
                    m = messages[i]
                    if m.get('role') == 'assistant' and m.get('tool_calls'):
                        idx = i
                        break
                if idx is None:
                    return messages
                tool_msgs = []
                j = idx + 1
                while j < len(messages) and messages[j].get('role') == 'tool':
                    tool_msgs.append(messages[j])
                    j += 1
                return messages[idx:j]
            return get_last_tool_call_block(messages)

    try:
        if openai_tool_list:
            response = await client.chat.completions.create(
                model=st.session_state.openai_model,
                messages=get_message_history_for_openai(st.session_state.messages),
                tools=openai_tool_list,
                tool_choice="auto"
            )
        else: # No MCP tools to pass
            response = await client.chat.completions.create(
                model=st.session_state.openai_model,
                messages=get_message_history_for_openai(st.session_state.messages)
            )

        response_message = response.choices[0].message

        # Step 2: check if the model wanted to call a function
        if response_message.tool_calls:
            print(f"[DEBUG CHAT] OpenAI response contains tool_calls: {response_message.tool_calls}")
            # Convert ChatCompletionMessage to dict before appending
            assistant_message_dict = {
                "role": response_message.role, 
                "content": response_message.content or "", # Ensure content is string
                "tool_calls": [
                    {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in response_message.tool_calls
                ]
            }
            st.session_state.messages.append(assistant_message_dict)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args_json = tool_call.function.arguments
                tool_call_id = tool_call.id
                
                try:
                    function_args = json.loads(function_args_json)
                except json.JSONDecodeError:
                    print(f"[ERROR MCP] Failed to parse JSON arguments for tool {function_name}: {function_args_json}")
                    # Send error back to LLM
                    st.session_state.messages.append({
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": function_name,
                        "content": f"Error: Could not parse arguments for tool {function_name}. Arguments received: {function_args_json}",
                    })
                    continue # Skip to next tool call or to re-prompting LLM

                print(f"[DEBUG MCP] Calling MCP tool: {function_name} with args: {function_args}")
                
                async with streamablehttp_client(st.session_state.mcp_server_address) as (read_stream, write_stream, info):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        mcp_tool_response = await session.call_tool(
                            name=function_name,
                            arguments=function_args
                        )
                        # Process mcp_tool_response: it could be a complex object or simple data
                        # For now, assume it's JSON serializable or has a 'content' attribute
                        if hasattr(mcp_tool_response, 'content'):
                            tool_call_result_content = str(mcp_tool_response.content)
                        elif isinstance(mcp_tool_response, (dict, list)):
                            tool_call_result_content = json.dumps(mcp_tool_response)
                        elif mcp_tool_response is None:
                            tool_call_result_content = "Tool executed successfully but returned no content."
                        else:
                            tool_call_result_content = str(mcp_tool_response)
                        print(f"[DEBUG MCP] MCP tool '{function_name}' returned: {tool_call_result_content}")
                st.session_state.messages.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_call_result_content,
                })
            
            # Get a new response from the LLM based on the tool's response
            print("[DEBUG CHAT] Getting new response from LLM after tool execution...")

            def get_last_tool_call_block(messages):
                # Find the last assistant message with tool_calls
                idx = None
                for i in range(len(messages) - 1, -1, -1):
                    m = messages[i]
                    if m.get('role') == 'assistant' and m.get('tool_calls'):
                        idx = i
                        break
                if idx is None:
                    return messages  # fallback: send all (shouldn't happen)
                # Now gather all tool messages that immediately follow
                tool_msgs = []
                j = idx + 1
                while j < len(messages) and messages[j].get('role') == 'tool':
                    tool_msgs.append(messages[j])
                    j += 1
                return messages[:idx+1] + tool_msgs

            processed_messages_for_api = get_last_tool_call_block(st.session_state.messages)
            second_response = await client.chat.completions.create(
                model=st.session_state.openai_model,
                messages=processed_messages_for_api # Only send valid OpenAI tool-call sequence
                # No 'tools' or 'tool_choice' here for the summarizing call
            )
            assistant_final_response = second_response.choices[0].message
            final_assistant_dict = {
                "role": assistant_final_response.role,
                "content": assistant_final_response.content or "" # Ensure content is string
            }
            st.session_state.messages.append(final_assistant_dict)

        else: # No tool calls, just a regular message
            # Convert ChatCompletionMessage to dict before appending
            assistant_message_dict = {
                "role": response_message.role,
                "content": response_message.content or "" # Ensure content is string
            }
            st.session_state.messages.append(assistant_message_dict)

    except Exception as e:
        print(f"[ERROR CHAT] Error during OpenAI call or tool processing: {e}")
        st.session_state.messages.append({"role": "assistant", "content": f"An error occurred: {e}"})

    # Rerun to update the UI with the new messages
    st.rerun()


# --- Streamlit UI Setup ---
def main():
    st.set_page_config(layout="wide", page_title="OpenAI Chat with MCP")
    st.title("🤖 OpenAI Chat & 🔌 MCP Client")

    # Initialize session state variables
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = DEFAULT_OPENAI_MODEL
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mcp_server_address" not in st.session_state:
        st.session_state.mcp_server_address = "http://localhost:8000/mcp" # Default
    if "mcp_connection_status" not in st.session_state:
        st.session_state.mcp_connection_status = "Not Connected"
    
    if "mcp_resources" not in st.session_state:
        st.session_state.mcp_resources = []
    if "mcp_tool_schemas" not in st.session_state:
        st.session_state.mcp_tool_schemas = []
    if "selected_mcp_resource_uri" not in st.session_state:
        st.session_state.selected_mcp_resource_uri = ""

    # --- Sidebar for Configuration ---
    with st.sidebar:
        st.header("⚙️ Configurations")
        st.subheader("OpenAI API")
        st.session_state.openai_api_key = st.text_input("API Key", value=st.session_state.openai_api_key, type="password")
        st.session_state.openai_model = st.text_input("Model", value=st.session_state.openai_model)

        st.subheader("MCP Server")
        st.session_state.mcp_server_address = st.text_input("Server Address (e.g., http://localhost:8000/mcp)", value=st.session_state.mcp_server_address)

        if st.button("Connect to MCP Server"):
            if st.session_state.mcp_server_address:
                # Run the async connection function
                session, status_msg, resources, tool_schemas = asyncio.run(async_connect_mcp_server(st.session_state.mcp_server_address))
                st.session_state.mcp_session = session
                st.session_state.mcp_connection_status = status_msg
                st.session_state.mcp_resources = resources
                st.session_state.mcp_tool_schemas = tool_schemas # Store fetched tool schemas
                if session:
                    st.success(status_msg)
                    if tool_schemas:
                        st.write(f"Discovered {len(tool_schemas)} MCP tools.")
                    if resources:
                        st.write(f"Discovered {len(resources)} MCP resources.")
                else:
                    st.error(status_msg)
            else:
                st.warning("Please enter MCP Server Address.")
        
        st.markdown(f"**MCP Status:** {st.session_state.mcp_connection_status}")

        if st.session_state.mcp_resources:
            st.subheader("MCP Resources")
            resource_options = {
                (item.name if hasattr(item, 'name') and item.name else str(item.uri)): str(item.uri) 
                for item in st.session_state.mcp_resources if hasattr(item, 'uri')
            }
            display_options = ["<Select a resource>"] + list(resource_options.keys())
            
            selected_resource_name = st.selectbox(
                "Available Resources", 
                options=display_options,
                index=0 # Default to "<Select a resource>"
            )
            
            if selected_resource_name != "<Select a resource>":
                st.session_state.selected_mcp_resource_uri = resource_options[selected_resource_name]
                if st.button("Read Resource Content"):
                    if st.session_state.selected_mcp_resource_uri:
                        st.info(f"Reading: {st.session_state.selected_mcp_resource_uri}")
                        # Run async read resource
                        content = asyncio.run(async_read_mcp_resource(st.session_state.mcp_server_address, st.session_state.selected_mcp_resource_uri))
                        st.text_area("Resource Content:", value=content, height=200)
                    else:
                        st.warning("No resource URI selected to read.")
            else:
                st.session_state.selected_mcp_resource_uri = ""

    # --- Main Chat Interface ---
    for msg in st.session_state.messages:
        if msg["role"] == "tool": # Skip displaying raw tool messages, or format them if desired
            # For example, you could show a small notification that a tool was used
            # st.chat_message("assistant", avatar="🛠️").write(f"Tool {msg['name']} was called.")
            pass 
        else:
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Enter your message here..."):
        if not st.session_state.openai_api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        else:
            # Run the async message handler
            asyncio.run(handle_chat_message(prompt))

if __name__ == "__main__":
    main()
