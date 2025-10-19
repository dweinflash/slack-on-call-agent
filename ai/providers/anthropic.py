from .base_provider import BaseAPIProvider
import anthropic
import os
import logging
import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..rag import retrieve_context

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
                # Log detailed tool info for debugging
                logger.info(f"Tool '{tool.name}': {tool.description}")
                logger.info(f"  Schema: {tool.inputSchema}")
            logger.info(f"Connected to {server_name} with {len(response.tools)} tools: {[t.name for t in response.tools]}")

        except Exception as e:
            logger.error(f"Error connecting to {server_name} MCP server: {e}")

    async def _initialize_mcp(self):
        """Initialize MCP connections to configured servers."""
        if self.mcp_initialized:
            return

        try:
            self.exit_stack = AsyncExitStack()
            with open("server_config.json", "r") as file:
                data = json.load(file)

            # Connect to all configured MCP servers
            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                # Expand environment variables in the config
                expanded_config = self._expand_env_vars(server_config)
                await self._connect_to_mcp_server(server_name, expanded_config)

            self.mcp_initialized = True
            logger.info(f"MCP initialized with {len(self.available_tools)} tools")
        except Exception as e:
            logger.error(f"Error initializing MCP: {e}")

    def _expand_env_vars(self, config):
        """Recursively expand environment variables in config."""
        import re

        if isinstance(config, dict):
            return {k: self._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Replace ${VAR_NAME} with environment variable value
            def replace_env_var(match):
                var_name = match.group(1)
                value = os.environ.get(var_name, "")
                if not value:
                    logger.warning(f"Environment variable {var_name} is not set")
                else:
                    logger.info(f"Expanded ${{{var_name}}} (length: {len(value)})")
                return value
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, config)
        else:
            return config

    async def _generate_with_tools(self, prompt: str, system_content: str, use_rag: bool = False, use_mcp: bool = False) -> dict:
        """
        Generate response with MCP tool support and RAG context.

        Args:
            prompt: User's prompt/question
            system_content: System prompt
            use_rag: Whether to retrieve and use RAG knowledge base (default: False)
            use_mcp: Whether to use MCP tools (default: False)

        Returns:
            Dictionary containing:
                - 'response': The AI-generated response text
                - 'rag_sources': List of source metadata dicts (empty if no RAG used)
        """

        # Conditionally initialize MCP tool support
        if use_mcp:
            await self._initialize_mcp()

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Conditionally retrieve RAG context based on use_rag flag
        rag_context = ""
        rag_sources = []

        if use_rag:
            logger.info(f"Retrieving RAG context for prompt: {prompt[:100]}...")
            rag_result = retrieve_context(prompt)
            rag_context = rag_result.get("context", "")
            rag_sources = rag_result.get("sources", [])
            logger.info(f"RAG context retrieved: {len(rag_context)} characters from {len(rag_sources)} sources")
        else:
            logger.info("RAG disabled for this query")

        # Inject RAG context into system prompt if available
        if rag_context:
            enhanced_system_content = f"""## Retrieved Knowledge Base Articles

The following knowledge base articles may be relevant to the user's query:

{rag_context}

## Instructions

{system_content}

When answering the user's question about incidents, alerts, or issues:
1. **Prioritize information from the retrieved knowledge base articles above**
2. **Keep your response BRIEF and HIGH-LEVEL** - do NOT reproduce detailed step-by-step instructions
3. **Structure your response clearly**:
   - Brief summary (2-3 sentences) of what the issue means
   - High-level resolution approach (3-5 bullet points of main actions)
   - Brief escalation guidance (1 sentence)
4. **Use Slack's mrkdwn formatting** to make it scannable:
   - Bold: *text* (single asterisks, NOT **text**)
   - Italic: _text_
   - Bullet points: • or -
   - Code: `text`
5. **Remind users** that detailed instructions, specific commands, and screenshots are available in the linked knowledge base articles
6. **Be direct and professional** - assume the user needs quick guidance, not a full runbook reproduction
7. **Target response length**: 500-1000 characters total

**CRITICAL FORMATTING**: This will be displayed in Slack. Use *single asterisks* for bold, NOT double. Slack's mrkdwn is different from standard markdown.

Remember: The user will see links to the full knowledge base articles below your response. Your job is to provide a quick summary and high-level direction, NOT to reproduce the entire runbook. Keep it concise."""
            logger.info("Enhanced prompt with RAG context")
        else:
            logger.warning("No RAG context retrieved - responding without knowledge base")
            enhanced_system_content = system_content

        messages = [{"role": "user", "content": prompt}]

        # Build API call parameters
        api_params = {
            "model": self.current_model,
            "system": enhanced_system_content,
            "messages": messages,
            "max_tokens": self.MODELS[self.current_model]["max_tokens"],
        }

        # Add tools if available
        if self.available_tools:
            api_params["tools"] = self.available_tools

        # Agentic loop to handle tool calls
        # Limit to 2 iterations to prevent token burnout
        max_iterations = 2
        iteration = 0

        while iteration < max_iterations:
            response = self.client.messages.create(**api_params)
            iteration += 1

            # Log token usage
            usage = response.usage
            logger.info(f"Iteration {iteration}: input_tokens={usage.input_tokens}, output_tokens={usage.output_tokens}")

            # Check if there are any tool uses in the response
            tool_uses = [content for content in response.content if content.type == 'tool_use']

            if not tool_uses:
                # No tool uses, we have the final response
                text_content = next((content.text for content in response.content if hasattr(content, 'text')), "")
                return {
                    "response": text_content,
                    "rag_sources": rag_sources
                }

            # Handle all tool calls in this turn
            logger.info(f"Processing {len(tool_uses)} tool calls in iteration {iteration}")
            messages.append({'role': 'assistant', 'content': response.content})

            tool_results = []
            for tool_use in tool_uses:
                session = self.sessions.get(tool_use.name)
                if session:
                    logger.info(f"Calling tool: {tool_use.name} with args: {tool_use.input}")
                    try:
                        result = await session.call_tool(tool_use.name, arguments=tool_use.input)

                        # Truncate large tool results to prevent token explosion
                        result_content = result.content
                        if isinstance(result_content, list):
                            # Handle array of content blocks
                            result_content = str(result_content)

                        max_result_length = 4000  # Limit each tool result to ~4k chars (~1k tokens)
                        if len(result_content) > max_result_length:
                            result_content = result_content[:max_result_length] + f"\n\n[... truncated {len(result_content) - max_result_length} characters ...]"
                            logger.warning(f"Truncated tool result for {tool_use.name} from {len(result.content)} to {max_result_length} chars")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result_content
                        })
                        logger.info(f"Tool {tool_use.name} succeeded (result length: {len(result_content)} chars)")
                    except Exception as e:
                        logger.error(f"Tool {tool_use.name} failed: {e}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })
                else:
                    logger.warning(f"No session found for tool: {tool_use.name}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"Error: Tool {tool_use.name} not available",
                        "is_error": True
                    })

            # Add all tool results to messages
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Update api_params with new messages for next iteration
            api_params["messages"] = messages

        # If we hit max iterations, return what we have
        logger.warning(f"Hit max iterations ({max_iterations}) in tool loop")
        # Try to get a response with the tool results we have
        try:
            final_response = self.client.messages.create(**api_params)
            text_content = next((content.text for content in final_response.content if hasattr(content, 'text')),
                              "I've gathered information but need to limit my analysis to stay within token limits. Please ask a more specific question.")
            return {
                "response": text_content,
                "rag_sources": rag_sources
            }
        except Exception as e:
            logger.error(f"Failed to get final response after max iterations: {e}")
            return {
                "response": "I've analyzed the code but encountered token limits. Please ask a more specific question about a particular file or component.",
                "rag_sources": rag_sources
            }

    def generate_response(self, prompt: str, system_content: str, use_rag: bool = False, use_mcp: bool = False) -> dict:
        """
        Generate a response to the user's prompt.

        Args:
            prompt: User's prompt/question
            system_content: System prompt
            use_rag: Whether to use RAG knowledge base retrieval (default: False)
            use_mcp: Whether to use MCP tools (default: False)

        Returns:
            Dictionary containing:
                - 'response': The AI-generated response text
                - 'rag_sources': List of source metadata dicts (empty if no RAG used)
        """
        try:
            # Run async MCP tool support
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._generate_with_tools(prompt, system_content, use_rag=use_rag, use_mcp=use_mcp))
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
