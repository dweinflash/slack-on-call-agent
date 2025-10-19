from slack_bolt import Ack, Say, BoltContext
from logging import Logger
from ai.providers import get_provider_response
from ai.ai_constants import INCIDENT_RESPONSE_SYSTEM_CONTENT
from slack_sdk import WebClient
from ..listener_utils.listener_constants import RAG_LOADING_TEXT, ERROR_PREFIX
from ..listener_utils.message_formatter import (
    format_rag_response,
    format_ai_response,
    format_error_message,
)

"""
Callback for handling the '/incident' command for incident response and troubleshooting.
Uses RAG knowledge base to provide resolution steps from documentation.
"""


def incident_callback(
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
                text=":rotating_light: Please describe the incident or alert. Example: `/incident kafka backlog is growing`",
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
                        "text": RAG_LOADING_TEXT
                    }
                }
            ]

            waiting_message = client.chat_postMessage(
                channel=channel_id,
                text=f"Q: {prompt}\n{RAG_LOADING_TEXT}",
                blocks=initial_blocks
            )

            # Get AI response with incident response system prompt (includes RAG)
            result = get_provider_response(
                user_id, prompt, context=[], system_content=INCIDENT_RESPONSE_SYSTEM_CONTENT
            )

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

            # Format with RAG citations if available
            if rag_sources and provider.lower() == "anthropic":
                response_blocks = format_rag_response(response_text, rag_sources, include_followup=False)
            else:
                response_blocks = format_ai_response(response_text, response_type="general")

            blocks.extend(response_blocks)

            # Truncate fallback text if needed (Slack has 40k char limit for text field)
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
