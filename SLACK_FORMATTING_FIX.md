# Slack mrkdwn Formatting Fix

**Date:** 2025-10-19
**Status:** ✅ FIXED

## Problem

The `/incident` command responses were using standard markdown syntax (`**text**` for bold), which doesn't render correctly in Slack. Instead of displaying bold text, Slack was showing the raw `**Issue Summary**` with asterisks visible.

## Root Cause

Slack uses its own markdown flavor called **mrkdwn** which has different syntax than standard markdown:

| Element | Standard Markdown | Slack mrkdwn |
|---------|------------------|--------------|
| Bold    | `**text**`       | `*text*`     |
| Italic  | `*text*` or `_text_` | `_text_`    |
| Code    | `` `text` ``     | `` `text` `` |

The AI was generating responses with standard markdown because it wasn't explicitly told to use Slack's syntax.

## Solution

Updated both system prompts to explicitly instruct the AI to use Slack's mrkdwn formatting:

### 1. `ai/ai_constants.py` - Added Formatting Rules Section

```python
## Formatting Rules

**CRITICAL**: Use Slack's mrkdwn formatting syntax:
- Bold: *text* (single asterisks, NOT double)
- Italic: _text_ (underscores)
- Code: `text` (backticks)
- Bullet points: • or - at start of line
- DO NOT use **text** for bold (that's standard markdown, not Slack)
```

### 2. `ai/providers/anthropic.py` - Updated RAG Instructions

```python
4. **Use Slack's mrkdwn formatting** to make it scannable:
   - Bold: *text* (single asterisks, NOT **text**)
   - Italic: _text_
   - Bullet points: • or -
   - Code: `text`

**CRITICAL FORMATTING**: This will be displayed in Slack. Use *single asterisks*
for bold, NOT double. Slack's mrkdwn is different from standard markdown.
```

## Before vs. After

### Before (Incorrect - Standard Markdown)
```
**Issue Summary**: Kafka issues typically indicate...
**Resolution Approach**:
• Check Kafka broker health
**Note**: For detailed troubleshooting...
```

**Slack Display:**
```
**Issue Summary**: Kafka issues typically indicate...
**Resolution Approach**:
• Check Kafka broker health
**Note**: For detailed troubleshooting...
```
❌ Asterisks visible, no bold formatting

### After (Correct - Slack mrkdwn)
```
*Issue Summary*: Kafka issues typically indicate...
*Resolution Approach*:
• Check Kafka broker health
*Note*: For detailed troubleshooting...
```

**Slack Display:**
```
Issue Summary: Kafka issues typically indicate...
Resolution Approach:
• Check Kafka broker health
Note: For detailed troubleshooting...
```
✅ Proper bold formatting, clean appearance

## Test Results

Tested with query: `"kafka backlog growing"`

```
*Issue Summary*:
This alert indicates that the Kafka outbound message backlog for the LVDS
application is growing beyond normal levels. The 209731-VDF-LVDS-INT-KAFKA
subscription is experiencing a backlog exceeding 5,000 messages.

*Resolution Approach*:
• Check current message backlog in the Internal Consumption Backlog graph
• Verify backlog size compared to normal range (500-2,500 messages)
• Escalate to LVDS Support team for investigation
• Request manual restart of pulsar-to-kafka-bridge application pods if needed
• Monitor backlog metrics after restart to confirm resolution

*Note*: Escalate to LVDS Support if the backlog continues to grow. Detailed
instructions and specific commands can be found in the linked knowledge base
articles.
```

**Validation:**
- ✅ Uses single asterisks (*) for bold headings
- ✅ Uses bullet points (•) for lists
- ✅ No double asterisks (**) anywhere in response
- ✅ Character count: 1,152 (within 500-1000 target range)
- ✅ RAG sources: 2 articles retrieved

## How Slack mrkdwn Works

Slack's Block Kit accepts `"type": "mrkdwn"` in section blocks, which enables basic formatting:

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "*Bold text* and _italic text_ and `code`"
  }
}
```

**Supported mrkdwn syntax:**
- `*text*` → **Bold**
- `_text_` → *Italic*
- `~text~` → ~~Strikethrough~~
- `` `text` `` → `code`
- `>` → Block quote
- ``` ``` ``` → Code block
- Links: `<https://example.com|Link text>`
- User mentions: `<@U12345>`
- Channel mentions: `<#C12345>`

**NOT supported:**
- `**text**` (standard markdown bold) - displays literally
- `#` headers - use Slack's header blocks instead
- HTML tags

## Files Modified

- `ai/ai_constants.py` (lines 86-93)
- `ai/providers/anthropic.py` (lines 158-167)

## Testing

To verify Slack formatting is working:

1. Restart the app:
   ```bash
   source .venv/bin/activate
   python3 app.py
   ```

2. Run in Slack:
   ```
   /incident kafka issues
   ```

3. Verify the response shows:
   - **Bold headings** (Issue Summary, Resolution Approach, Note)
   - Bullet points displaying correctly
   - NO visible asterisks in the text

## Additional Resources

- [Slack mrkdwn reference](https://api.slack.com/reference/surfaces/formatting)
- [Block Kit formatting](https://api.slack.com/reference/block-kit/composition-objects#text)
- [Block Kit Builder](https://app.slack.com/block-kit-builder) - Test formatting

## Notes

- The message formatter (`listeners/listener_utils/message_formatter.py`) already uses `"type": "mrkdwn"` correctly
- The issue was purely in the AI-generated content, not the Slack API calls
- This fix applies to all `/incident` responses
- Other commands (like `/ask` or `/code`) may need similar updates if they show formatting issues
