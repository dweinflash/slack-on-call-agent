"""
Message formatting utilities for creating professional, snazzy Slack messages.

This module provides functions to format AI responses using Block Kit with:
- Professional formatting (headers, sections, dividers)
- Contextual emojis
- RAG citation support
- Short, succinct responses with follow-up questions
"""

from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Slack limits
MAX_BLOCKS_PER_MESSAGE = 50
MAX_TEXT_LENGTH_PER_BLOCK = 3000


def limit_blocks(blocks: List[Dict[str, Any]], max_blocks: int = MAX_BLOCKS_PER_MESSAGE) -> List[Dict[str, Any]]:
    """
    Limit the number of blocks to Slack's maximum.

    Args:
        blocks: List of Block Kit blocks
        max_blocks: Maximum number of blocks allowed (default: 50)

    Returns:
        Truncated list of blocks with warning if needed
    """
    if len(blocks) <= max_blocks:
        return blocks

    logger.warning(f"Truncating {len(blocks)} blocks to {max_blocks} (Slack limit)")

    # Keep header and first blocks, add truncation notice
    truncated = blocks[:max_blocks - 1]
    truncated.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":warning: _Response truncated due to length. Ask for specific details if needed._"
            }
        ]
    })

    return truncated


def shorten_response(text: str, max_length: int = 2500) -> tuple[str, bool]:
    """
    Shorten a response if it's too long, encouraging follow-up questions.

    Note: Reduced to 2500 to prevent Slack msg_too_long errors when combined with blocks.

    Args:
        text: The response text to potentially shorten
        max_length: Maximum character length before shortening (default: 2500)

    Returns:
        Tuple of (shortened_text, was_shortened)
    """
    if len(text) <= max_length:
        return text, False

    # Find a good breaking point (end of sentence)
    break_point = text.rfind('. ', 0, max_length)
    if break_point == -1:
        break_point = text.rfind('\n', 0, max_length)
    if break_point == -1:
        break_point = text.rfind(' ', 0, max_length)

    if break_point == -1:
        break_point = max_length

    shortened = text[:break_point + 1].strip()
    return shortened, True


def format_rag_sources(sources: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Format RAG source citations as Block Kit blocks with clickable buttons.

    Args:
        sources: List of source metadata dicts with 'filename' and 'url'

    Returns:
        List of Block Kit blocks for displaying sources with View Article buttons
    """
    if not sources:
        return []

    blocks = [{"type": "divider"}]

    # Header for referenced articles
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":page_facing_up: *Referenced Knowledge Base Articles*"
            }
        ]
    })

    # Add each source with a clickable button
    for source in sources:
        filename = source.get('filename', 'Unknown')
        url = source.get('url', '')

        # Clean up filename - remove number prefix and extension
        clean_name = filename.replace('.md', '').replace('209731_', '')

        # Create section with article name and button
        section_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"• *{clean_name}*"
            }
        }

        # Add button if URL is available
        if url:
            section_block["accessory"] = {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📄 View Article",
                    "emoji": True
                },
                "url": url,
                "style": "primary"
            }

        blocks.append(section_block)

    return blocks


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
    shortened_text, was_shortened = shorten_response(response_text, max_length=2500)

    # Main response with mrkdwn for formatting
    # Split into chunks if needed (Slack has 3000 char limit per text block)
    if len(shortened_text) <= 2500:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": shortened_text
            }
        })
    else:
        # Split into multiple section blocks
        chunks = _split_into_chunks(shortened_text, 2500)
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

    return limit_blocks(blocks)


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
        "general": ":gear:",
        "dm": ":busts_in_silhouette:",
        "error": ":warning:"
    }
    emoji = emoji_map.get(response_type, ":gear:") if include_emoji else ""

    # Header
    header_text = f"{emoji} LVDS On-Call Agent" if emoji else "LVDS On-Call Agent"
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": header_text,
            "emoji": True
        }
    })

    # Check if response needs shortening
    shortened_text, was_shortened = shorten_response(response_text, max_length=2500)

    # Main response - split into chunks if needed
    if len(shortened_text) <= 2500:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": shortened_text
            }
        })
    else:
        chunks = _split_into_chunks(shortened_text, 2500)
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

    return limit_blocks(blocks)


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


def format_code_response(
    response_text: str,
    include_emoji: bool = True
) -> List[Dict[str, Any]]:
    """
    Format a code analysis response using Block Kit.

    Args:
        response_text: The AI-generated code analysis response
        include_emoji: Whether to include emoji in header

    Returns:
        List of Block Kit blocks
    """
    blocks = []

    # Header for code analysis
    header_text = ":computer: Code Analysis" if include_emoji else "Code Analysis"
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": header_text,
            "emoji": True
        }
    })

    # Check if response needs shortening
    shortened_text, was_shortened = shorten_response(response_text, max_length=2500)

    # Main response - split into chunks if needed
    if len(shortened_text) <= 2500:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": shortened_text
            }
        })
    else:
        chunks = _split_into_chunks(shortened_text, 2500)
        for chunk in chunks:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": chunk
                }
            })

    # Add context footer for code analysis
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":information_source: _Analyzed using MCP tools_"
            }
        ]
    })

    return limit_blocks(blocks)


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
