"""
Custom instructions for how the LLM should use each MCP tool
These instructions guide Gemini on how to format and present tool results
"""

TOOL_INSTRUCTIONS = {
    "joke": {
        "get_random_joke": """
When telling a joke:
1. Build up anticipation with a friendly intro: "Here's a good one for you!" or "Oh, I've got a great one!"
2. Present the setup on its own line
3. Add a brief pause (blank line)
4. Deliver the punchline enthusiastically
5. Add a happy emoji: 😄, 🤣, or 😂
6. Engage the user: Ask if they want another joke or if that helped lighten the mood

Example format:
"Here's a good one! 😊

Why do programmers prefer dark mode?

Because light attracts bugs! 😄

Want to hear another one?"

Keep it upbeat and fun!
        """,
        
        "get_joke_by_index": """
When delivering a specific joke:
1. Acknowledge their request: "Here's joke #X as requested!"
2. Present the setup
3. Add spacing (blank line)
4. Deliver the punchline
5. Add emoji 😄
6. Offer more: "Want to try another number between 1-8?"

Be friendly and accommodating.
        """,
        
        "count_jokes": """
When telling the count:
1. Make it conversational: "I've got X programming jokes in my collection!"
2. Be enthusiastic: Use 🎭 or 😄 emoji
3. Offer to share: "Want to hear one? Just ask!"
4. Optional: Mention they can ask for a specific joke by number

Keep it light and inviting.
        """
    },
    
    "time": {
        "get_current_time": """
When presenting time:
1. Start clearly: "The current time is..."
2. Format nicely: Include day of week if available, e.g., "2:30 PM on Friday, January 17, 2025"
3. Add context based on time:
   - Morning (6-11am): "Good morning!" or "Early start!"
   - Afternoon (12-5pm): "Afternoon!" or "Midday!"
   - Evening (6-9pm): "Evening time!" or "Getting late!"
   - Night (10pm-5am): "Burning the midnight oil!" or "Late night coding?"
4. Use appropriate emoji: 🕐, ⏰, 🌅, 🌆, 🌃
5. Be conversational and friendly

Example:
"The current time is 2:30 PM on Friday, January 17, 2025 🕐

Almost the weekend! 🎉"
        """,
        
        "get_timestamp": """
When showing timestamp:
1. Explain clearly: "The current Unix timestamp is..."
2. Show the number prominently
3. Add helpful context: "This represents the number of seconds since January 1, 1970 (UTC)"
4. Use emoji: ⏱️ or 🕐
5. Offer to show human-readable time if they need it

Example:
"The current Unix timestamp is: 1705507845 ⏱️

That's the number of seconds since January 1, 1970. Need this in a more readable format?"
        """
    }
}

def get_tool_instruction(server: str, tool: str) -> str:
    """
    Get custom instruction for a specific tool
    
    Args:
        server: The MCP server name (e.g., "joke", "time")
        tool: The tool name (e.g., "get_random_joke")
    
    Returns:
        Custom instruction string, or empty string if not found
    """
    return TOOL_INSTRUCTIONS.get(server, {}).get(tool, "")