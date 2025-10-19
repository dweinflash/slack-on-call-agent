from slack_bolt import Ack, Say, BoltContext
from logging import Logger
from ai.providers import get_provider_response
from slack_sdk import WebClient
from ..listener_utils.listener_constants import ERROR_PREFIX
from ..listener_utils.message_formatter import (
    format_rag_response,
    format_ai_response,
    format_error_message,
)

"""
Callback for handling the 'ask-bolty' command. It acknowledges the command, retrieves the user's ID and prompt,
checks if the prompt is empty, and responds with either an error message or the provider's response.
"""


def ask_callback(
    client: WebClient, ack: Ack, command, say: Say, logger: Logger, context: BoltContext
):
    try:
        ack()
        user_id = context["user_id"]
        channel_id = context["channel_id"]
        prompt = command["text"]

        if prompt == "":
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Looks like you didn't provide a prompt. Try again.",
            )
        else:
            # Get AI response
            result = get_provider_response(user_id, prompt)

            # Extract response components
            response_text = result.get("response", "")
            rag_sources = result.get("rag_sources", [])
            provider = result.get("provider", "")

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

            # Add formatted response blocks
            if rag_sources and provider.lower() == "anthropic":
                response_blocks = format_rag_response(response_text, rag_sources, include_followup=True)
            else:
                response_blocks = format_ai_response(response_text, response_type="general")

            blocks.extend(response_blocks)

            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Q: {prompt}\nA: {response_text}",  # Fallback text
                blocks=blocks,
            )
    except Exception as e:
        logger.error(e)
        error_blocks = format_error_message(str(e))
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"{ERROR_PREFIX}\n{e}",  # Fallback text
            blocks=error_blocks
        )
