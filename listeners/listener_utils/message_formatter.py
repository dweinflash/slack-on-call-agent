"""
Message formatting utilities for creating professional, snazzy Slack messages.

This module provides functions to format AI responses using Block Kit with:
- Professional formatting (headers, sections, dividers)
- Contextual emojis
- RAG citation support
- Short, succinct responses with follow-up questions
"""

from typing import List, Dict, Optional, Any


def shorten_response(text: str, max_length: int = 3000) -> tuple[str, bool]:
    """
    Shorten a response if it's too long, encouraging follow-up questions.

    Note: Increased max_length to 3000 to accommodate detailed incident resolution steps.

    Args:
        text: The response text to potentially shorten
        max_length: Maximum character length before shortening (default: 3000)

    Returns:
        Tuple of (shortened_text, was_shortened)
    """
    if len(text) <= max_length:
        return text, False

    # Find a good breaking point (end of sentence)
    break_point = text.rfind('. ', 0, max_length)
    if break_point == -1:
        break_point = text.rfind(' ', 0, max_length)

    if break_point == -1:
        break_point = max_length

    shortened = text[:break_point + 1].strip()
    return shortened, True


def format_rag_sources(sources: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Format RAG source citations as Block Kit blocks.

    Args:
        sources: List of source metadata dicts with 'filename' and optionally 'title'

    Returns:
        List of Block Kit blocks for displaying sources
    """
    if not sources:
        return []

    # Create bullet list of sources
    source_items = []
    for source in sources:
        filename = source.get('filename', 'Unknown')
        # Clean up filename - remove number prefix and extension
        clean_name = filename.replace('.md', '').replace('209731_', '')
        source_items.append(f"• {clean_name}")

    sources_text = "\n".join(source_items)

    return [
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":page_facing_up: *Referenced Knowledge Base Articles*\n{sources_text}"
                }
            ]
        }
    ]


def format_rag_response(
    response_text: str,
    sources: Optional[List[Dict[str, str]]] = None,
    include_followup: bool = False
) -> List[Dict[str, Any]]:
    """
    Format an AI response that used RAG context with citations.

    Args:
        response_text: The AI-generated response text
        sources: List of source metadata dicts
        include_followup: Whether to encourage follow-up questions (default: False for detailed responses)

    Returns:
        List of Block Kit blocks
    """
    blocks = []

    # Header for incident resolution
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": ":books: Knowledge Base Resolution",
            "emoji": True
        }
    })

    # Check if response needs shortening (using higher limit for technical content)
    shortened_text, was_shortened = shorten_response(response_text, max_length=3000)

    # Main response with mrkdwn for formatting
    # Split into chunks if needed (Slack has 3000 char limit per text block)
    if len(shortened_text) <= 3000:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": shortened_text
            }
        })
    else:
        # Split into multiple section blocks
        chunks = _split_into_chunks(shortened_text, 3000)
        for chunk in chunks:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": chunk
                }
            })

    # Add follow-up encouragement only if shortened
    if was_shortened:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Response was shortened. Ask for more details if needed!_ :mag:"
                }
            ]
        })

    # Add sources if available
    if sources:
        blocks.extend(format_rag_sources(sources))

    return blocks


def _split_into_chunks(text: str, max_chunk_size: int = 3000) -> List[str]:
    """
    Split text into chunks that fit within Slack's block text limits.

    Args:
        text: The text to split
        max_chunk_size: Maximum size per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # Find a good break point (paragraph, sentence, or word boundary)
        end_pos = min(current_pos + max_chunk_size, len(text))

        if end_pos < len(text):
            # Try to break at paragraph
            break_point = text.rfind('\n\n', current_pos, end_pos)
            if break_point == -1 or break_point <= current_pos:
                # Try to break at newline
                break_point = text.rfind('\n', current_pos, end_pos)
            if break_point == -1 or break_point <= current_pos:
                # Try to break at sentence
                break_point = text.rfind('. ', current_pos, end_pos)
            if break_point == -1 or break_point <= current_pos:
                # Break at word boundary
                break_point = text.rfind(' ', current_pos, end_pos)
            if break_point == -1 or break_point <= current_pos:
                # Last resort: hard break
                break_point = end_pos
            else:
                break_point += 1  # Include the period/newline
        else:
            break_point = end_pos

        chunks.append(text[current_pos:break_point].strip())
        current_pos = break_point

    return chunks


def format_ai_response(
    response_text: str,
    response_type: str = "general",
    include_emoji: bool = True
) -> List[Dict[str, Any]]:
    """
    Format a general AI response using Block Kit.

    Args:
        response_text: The AI-generated response text
        response_type: Type of response ('general', 'dm', 'error')
        include_emoji: Whether to include contextual emojis

    Returns:
        List of Block Kit blocks
    """
    blocks = []

    # Choose header emoji based on type
    emoji_map = {
        "general": ":robot_face:",
        "dm": ":speech_balloon:",
        "error": ":warning:"
    }
    emoji = emoji_map.get(response_type, ":robot_face:") if include_emoji else ""

    # Header
    header_text = f"{emoji} Bolty's Response" if emoji else "Bolty's Response"
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": header_text,
            "emoji": True
        }
    })

    # Check if response needs shortening
    shortened_text, was_shortened = shorten_response(response_text, max_length=3000)

    # Main response - split into chunks if needed
    if len(shortened_text) <= 3000:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": shortened_text
            }
        })
    else:
        chunks = _split_into_chunks(shortened_text, 3000)
        for chunk in chunks:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": chunk
                }
            })

    # Encourage follow-up if shortened
    if was_shortened:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Response shortened. Ask for more details!_ :mag:"
                }
            ]
        })

    return blocks


def format_error_message(error_text: str, error_type: str = "general") -> List[Dict[str, Any]]:
    """
    Format an error message with professional styling.

    Args:
        error_text: The error message text
        error_type: Type of error for contextual emoji

    Returns:
        List of Block Kit blocks
    """
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":warning: Oops! Something went wrong",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{error_text}```"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Try again or rephrase your question!_ :arrows_counterclockwise:"
                }
            ]
        }
    ]


def format_simple_message(text: str, emoji: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Format a simple text message with optional emoji.

    Args:
        text: Message text
        emoji: Optional emoji to prepend

    Returns:
        List of Block Kit blocks
    """
    formatted_text = f"{emoji} {text}" if emoji else text

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": formatted_text
            }
        }
    ]
