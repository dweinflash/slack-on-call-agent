from .base_provider import BaseAPIProvider
import anthropic
import os
import logging
import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnthropicAPI(BaseAPIProvider):
    MODELS = {
        "claude-3-5-sonnet-20240620": {
            "name": "Claude 3.5 Sonnet",
            "provider": "Anthropic",
            "max_tokens": 4096,  # or 8192 with the header anthropic-beta: max-tokens-3-5-sonnet-2024-07-15
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet",
            "provider": "Anthropic",
            "max_tokens": 4096,
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "provider": "Anthropic",
            "max_tokens": 4096,
        },
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "provider": "Anthropic",
            "max_tokens": 4096,
        },
    }

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.exit_stack = None
        self.available_tools = []
        self.sessions = {}
        self.mcp_initialized = False

    def set_model(self, model_name: str):
        if model_name not in self.MODELS.keys():
            raise ValueError("Invalid model")
        self.current_model = model_name

    def get_models(self) -> dict:
        if self.api_key is not None:
            return self.MODELS
        else:
            return {}

    async def _connect_to_mcp_server(self, server_name, server_config):
        """Connect to an MCP server and register its tools."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()

            # List available tools from the server
            response = await session.list_tools()
            for tool in response.tools:
                self.sessions[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            logger.info(f"Connected to {server_name} with tools: {[t.name for t in response.tools]}")

        except Exception as e:
            logger.error(f"Error connecting to {server_name} MCP server: {e}")

    async def _initialize_mcp(self):
        """Initialize MCP connection to filesystem server."""
        if self.mcp_initialized:
            return

        try:
            self.exit_stack = AsyncExitStack()
            with open("server_config.json", "r") as file:
                data = json.load(file)

            # Connect to filesystem server
            servers = data.get("mcpServers", {})
            if "filesystem" in servers:
                await self._connect_to_mcp_server("filesystem", servers["filesystem"])

            self.mcp_initialized = True
        except Exception as e:
            logger.error(f"Error initializing MCP: {e}")

    async def _generate_with_tools(self, prompt: str, system_content: str) -> str:
        """Generate response with MCP tool support."""
        await self._initialize_mcp()

        self.client = anthropic.Anthropic(api_key=self.api_key)
        messages = [{"role": "user", "content": prompt}]

        # Build API call parameters
        api_params = {
            "model": self.current_model,
            "system": system_content,
            "messages": messages,
            "max_tokens": self.MODELS[self.current_model]["max_tokens"],
        }

        # Add tools if available
        if self.available_tools:
            api_params["tools"] = self.available_tools

        response = self.client.messages.create(**api_params)

        # Handle tool use
        for content in response.content:
            if content.type == 'tool_use':
                session = self.sessions.get(content.name)
                if session:
                    result = await session.call_tool(content.name, arguments=content.input)
                    # For simplicity, just return the first text response after tool use
                    # Could extend this to handle multiple tool calls if needed
                    messages.append({'role': 'assistant', 'content': response.content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
                        }]
                    })
                    # Get final response
                    final_response = self.client.messages.create(**{**api_params, "messages": messages})
                    return final_response.content[0].text

        return response.content[0].text

    def generate_response(self, prompt: str, system_content: str) -> str:
        try:
            # Run async MCP tool support
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._generate_with_tools(prompt, system_content))
            finally:
                loop.close()
        except anthropic.APIConnectionError as e:
            logger.error(f"Server could not be reached: {e.__cause__}")
            raise e
        except anthropic.RateLimitError as e:
            logger.error(f"A 429 status code was received. {e}")
            raise e
        except anthropic.AuthenticationError as e:
            logger.error(f"There's an issue with your API key. {e}")
            raise e
        except anthropic.APIStatusError as e:
            logger.error(
                f"Another non-200-range status code was received: {e.status_code}"
            )
            raise e
