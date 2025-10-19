from slack_bolt import Ack, Say, BoltContext
from logging import Logger
from ai.providers import get_provider_response
from ai.ai_constants import INCIDENT_RESPONSE_SYSTEM_CONTENT
from slack_sdk import WebClient
from ..listener_utils.listener_constants import RAG_LOADING_TEXT, ERROR_PREFIX
from ..listener_utils.message_formatter import (
    format_rag_response,
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

            # Get AI response with incident response system prompt (enable RAG for incidents)
            logger.info(f"Requesting incident response for user {user_id} with query: '{prompt[:100]}'")
            logger.info("RAG is ENABLED for this request")

            result = get_provider_response(
                user_id, prompt, context=[], system_content=INCIDENT_RESPONSE_SYSTEM_CONTENT, use_rag=True
            )

            # Extract response components
            response_text = result.get("response", "")
            rag_sources = result.get("rag_sources", [])
            provider = result.get("provider", "")

            # Log for debugging
            logger.info(f"Incident response - Provider: {provider}, RAG sources: {len(rag_sources)}")
            if rag_sources:
                logger.info("RAG sources retrieved:")
                for idx, source in enumerate(rag_sources, 1):
                    logger.info(f"  {idx}. {source.get('filename', 'Unknown')}")
            else:
                logger.warning(f"⚠️  NO RAG SOURCES RETRIEVED for query: '{prompt}'")

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

            # For /incident commands, ALWAYS use Knowledge Base formatting
            # (RAG should be enabled, but use KB formatting regardless)
            if len(rag_sources) > 0:
                # RAG found sources - use Knowledge Base Resolution format with citations
                response_blocks = format_rag_response(response_text, rag_sources, include_followup=False)
            else:
                # No sources found, but still use Knowledge Base format (without citations)
                logger.warning("No RAG sources found for incident query - using KB format anyway")
                response_blocks = format_rag_response(response_text, sources=[], include_followup=False)

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
