from slack_bolt import Ack, Say, BoltContext
from logging import Logger
from ai.providers import get_provider_response
from ai.ai_constants import CODE_ANALYSIS_SYSTEM_CONTENT
from slack_sdk import WebClient
from ..listener_utils.listener_constants import DEFAULT_LOADING_TEXT, ERROR_PREFIX
from ..listener_utils.message_formatter import (
    format_code_response,
    format_error_message,
)

"""
Callback for handling the '/code' command for code analysis and system design questions.
Uses MCP tools (GitHub server) instead of RAG for technical code queries.
"""


def code_callback(
    client: WebClient, ack: Ack, command, say: Say, logger: Logger, context: BoltContext
):
    waiting_message = None
    try:
        ack()
        user_id = context["user_id"]
        channel_id = context["channel_id"]
        prompt = command["text"]

        if prompt == "":
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=":mag: Please provide a code-related question. Example: `/code explain the authentication flow`",
            )
        else:
            # Post initial message with the query and loading indicator
            initial_blocks = [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_quote",
                            "elements": [{"type": "text", "text": prompt}],
                        }
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": DEFAULT_LOADING_TEXT
                    }
                }
            ]

            waiting_message = client.chat_postMessage(
                channel=channel_id,
                text=f"Q: {prompt}\n{DEFAULT_LOADING_TEXT}",
                blocks=initial_blocks
            )

            # Get AI response with code analysis system prompt (disable RAG, enable MCP for code queries)
            result = get_provider_response(
                user_id, prompt, context=[], system_content=CODE_ANALYSIS_SYSTEM_CONTENT, use_rag=False, use_mcp=True
            )

            # Extract response components
            response_text = result.get("response", "")
            # Note: rag_sources should be empty for code queries
            rag_sources = result.get("rag_sources", [])

            # Create blocks with prompt quote
            blocks = [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_quote",
                            "elements": [{"type": "text", "text": prompt}],
                        }
                    ],
                }
            ]

            # Format code analysis response
            response_blocks = format_code_response(response_text)
            blocks.extend(response_blocks)

            # Truncate fallback text if needed
            fallback_text = f"Q: {prompt}\nA: {response_text}"
            if len(fallback_text) > 3000:
                fallback_text = fallback_text[:2997] + "..."

            # Update the waiting message with the response
            client.chat_update(
                channel=channel_id,
                ts=waiting_message["ts"],
                text=fallback_text,
                blocks=blocks,
            )
    except Exception as e:
        logger.error(e)
        error_blocks = format_error_message(str(e))

        if waiting_message:
            # Update the waiting message with error
            client.chat_update(
                channel=channel_id,
                ts=waiting_message["ts"],
                text=f"{ERROR_PREFIX}\n{e}",
                blocks=error_blocks
            )
        else:
            # Post new error message if we haven't posted anything yet
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"{ERROR_PREFIX}\n{e}",
                blocks=error_blocks
            )
