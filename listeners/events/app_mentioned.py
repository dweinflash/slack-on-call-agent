from ai.providers import get_provider_response
from logging import Logger
from slack_sdk import WebClient
from slack_bolt import Say
from ..listener_utils.listener_constants import (
    DEFAULT_LOADING_TEXT,
    MENTION_WITHOUT_TEXT,
    ERROR_PREFIX,
)
from ..listener_utils.parse_conversation import parse_conversation
from ..listener_utils.message_formatter import (
    format_rag_response,
    format_ai_response,
    format_error_message,
    format_simple_message,
)

"""
Handles the event when the app is mentioned in a Slack channel, retrieves the conversation context,
and generates an AI response if text is provided, otherwise sends a default response
"""


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    waiting_message = None
    try:
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts")
        user_id = event.get("user")
        text = event.get("text")

        if thread_ts:
            conversation = client.conversations_replies(
                channel=channel_id, ts=thread_ts, limit=10
            )["messages"]
        else:
            conversation = client.conversations_history(channel=channel_id, limit=10)[
                "messages"
            ]
            thread_ts = event["ts"]

        conversation_context = parse_conversation(conversation[:-1])

        if text:
            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            result = get_provider_response(user_id, text, conversation_context, use_rag=False)

            # Extract response components
            response_text = result.get("response", "")
            rag_sources = result.get("rag_sources", [])
            provider = result.get("provider", "")

            # Format with Block Kit based on whether RAG was used
            if rag_sources and provider.lower() == "anthropic":
                blocks = format_rag_response(response_text, rag_sources)
            else:
                blocks = format_ai_response(response_text, response_type="general")

            client.chat_update(
                channel=channel_id,
                ts=waiting_message["ts"],
                text=response_text,  # Fallback text for notifications
                blocks=blocks
            )
        else:
            waiting_message = say(text=MENTION_WITHOUT_TEXT, thread_ts=thread_ts)

    except Exception as e:
        logger.error(e)
        error_blocks = format_error_message(str(e))
        if waiting_message:
            client.chat_update(
                channel=channel_id,
                ts=waiting_message["ts"],
                text=f"{ERROR_PREFIX}\n{e}",  # Fallback text
                blocks=error_blocks
            )
