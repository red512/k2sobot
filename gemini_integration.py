import os
import logging
import json
import google.generativeai as genai
from mcp_client import get_mcp_client
from tool_instructions import get_tool_instruction

logger = logging.getLogger(__name__)

# Configure once at module level
_model = None

def is_gemini_available():
    """Check if Gemini API key is configured"""
    api_key = os.environ.get('GEMINI_API_KEY')
    return api_key is not None and api_key.strip() != ""

def get_gemini_model():
    """Get or create Gemini model instance"""
    global _model
    if _model is None:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel('gemini-2.5-flash-lite')
    return _model

def chat_with_gemini(user_message, max_tokens=1000):
    """Send a message to Gemini and get response (without MCP tools)"""
    try:
        if not is_gemini_available():
            return "Gemini API key is not configured. Please set GEMINI_API_KEY environment variable."

        model = get_gemini_model()

        response = model.generate_content(
            user_message,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            )
        )

        if response.text:
            return response.text
        else:
            return "Sorry, I couldn't generate a response. Please try again."

    except Exception as e:
        logger.error(f"Error communicating with Gemini: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def chat_with_mcp(user_message, max_tokens=1000):
    """
    Chat with Gemini that can call MCP tools
    """
    try:
        if not is_gemini_available():
            return "Gemini API key is not configured."
        
        mcp = get_mcp_client()
        
        # Check if any servers are registered
        servers = mcp.list_servers()
        if not servers:
            logger.warning("⚠️ No MCP servers available, using regular chat")
            return chat_with_gemini(user_message, max_tokens)
        
        # Get available MCP tools
        try:
            all_tools = mcp.list_all_tools()
            if not any(all_tools.values()):
                logger.warning("⚠️ No tools available from MCP servers")
                return chat_with_gemini(user_message, max_tokens)
        except Exception as e:
            logger.error(f"❌ Failed to list MCP tools: {e}")
            return chat_with_gemini(user_message, max_tokens)
        
        # Build tools description with examples
        tools_description = "Available tools:\n\n"
        for server, tools in all_tools.items():
            if tools:
                tools_description += f"Server: {server}\n"
                for tool in tools:
                    tools_description += f"  - {tool['name']}: {tool['description'][:150]}...\n"
                tools_description += "\n"
        
        # IMPROVED: More explicit system prompt
        system_prompt = f"""You are K2SObot with access to tools. You MUST use tools when appropriate.

{tools_description}

CRITICAL RULES - FOLLOW EXACTLY:
1. If user asks "what time is it" or "current time" → YOU MUST USE the time server get_current_time tool
2. If user asks for a "joke" or "make me laugh" → YOU MUST USE the joke server get_random_joke tool
3. When you use a tool, respond with ONLY this exact JSON format (no other text):
{{"use_tool": true, "server": "time", "tool": "get_current_time", "arguments": {{}}}}

Example:
User: "What time is it?"
You: {{"use_tool": true, "server": "time", "tool": "get_current_time", "arguments": {{}}}}

User: "Tell me a joke"  
You: {{"use_tool": true, "server": "joke", "tool": "get_random_joke", "arguments": {{}}}}

NOW RESPOND TO THIS USER MESSAGE:
User: {user_message}

Your response (JSON if using tool, otherwise natural text):"""
        
        model = get_gemini_model()
        response = model.generate_content(
            system_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more consistent tool usage
            )
        )
        
        response_text = response.text.strip()
        logger.info(f"📝 Gemini raw response: {response_text[:200]}")
        
        # Check if Gemini wants to call a tool
        try:
            # Remove markdown code blocks if present
            cleaned_response = response_text
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
            
            # Look for JSON
            if "{" in cleaned_response and "use_tool" in cleaned_response:
                json_start = cleaned_response.find("{")
                json_end = cleaned_response.rfind("}") + 1
                json_str = cleaned_response[json_start:json_end]
                
                logger.info(f"📋 Extracted JSON: {json_str}")
                
                tool_request = json.loads(json_str)
                
                if tool_request.get("use_tool") is True:
                    server = tool_request.get("server", "").strip()
                    tool = tool_request.get("tool", "").strip()
                    arguments = tool_request.get("arguments", {})
                    
                    # Validate server exists
                    if server not in mcp.list_servers():
                        logger.error(f"❌ Invalid server '{server}'. Available: {mcp.list_servers()}")
                        return f"Sorry, I tried to check the time but the service isn't available right now."
                    
                    logger.info(f"🔧 Calling MCP tool: {server}.{tool} with {arguments}")
                    
                    try:
                        # Call the MCP tool
                        tool_result = mcp.call_tool(server, tool, arguments)
                        logger.info(f"✅ Tool result received: {tool_result[:100]}...")
                        
                        # Get custom instructions
                        custom_instruction = get_tool_instruction(server, tool)
                        
                        # Format the result with tool info
                        format_prompt = f"""The user asked: {user_message}

I called the {tool} tool from the {server} server and got this result:
{tool_result}

{custom_instruction}

Now provide a friendly, natural response based on this information. Use emojis appropriately.

DO NOT mention the tool name in your response - I will add it at the end."""
                        
                        final_response = model.generate_content(
                            format_prompt,
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=max_tokens,
                                temperature=0.7,
                            )
                        )
                        
                        # Add tool info footer
                        response_text = final_response.text.strip()
                        response_text += f"\n\n_🔧 Tool used: `{server}.{tool}`_"
                        
                        return response_text
                        
                    except Exception as e:
                        logger.error(f"❌ Tool call failed: {e}")
                        return f"Sorry, I tried to get that information but encountered an issue. Please try again!"
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"No valid tool call in response: {e}")
            pass
        
        # If we get here, Gemini didn't use a tool when it should have
        # Check if the query clearly needed a tool
        user_lower = user_message.lower()
        if any(word in user_lower for word in ["time", "what time", "current time", "clock"]):
            logger.warning("⚠️ Gemini didn't use time tool when it should have - forcing it")
            # Force call the tool
            try:
                tool_result = mcp.call_tool("time", "get_current_time", {})
                result_json = json.loads(tool_result)
                return f"The current time is: {result_json.get('human_readable', result_json.get('time_only', 'unavailable'))} 🕐\n\n_🔧 Tool used: `time.get_current_time` (auto-detected)_"
            except Exception as e:
                logger.error(f"Failed to force time tool: {e}")
                return "Sorry, I'm having trouble accessing the time right now."
        
        elif any(word in user_lower for word in ["joke", "funny", "laugh", "humor"]):
            logger.warning("⚠️ Gemini didn't use joke tool when it should have - forcing it")
            # Force call the joke tool
            try:
                tool_result = mcp.call_tool("joke", "get_random_joke", {})
                result_json = json.loads(tool_result)
                return f"{result_json.get('setup', '')}\n\n{result_json.get('punchline', '')} 😄\n\n_🔧 Tool used: `joke.get_random_joke` (auto-detected)_"
            except Exception as e:
                logger.error(f"Failed to force joke tool: {e}")
                return "Sorry, I can't think of a joke right now!"
        
        # Normal response without tool calling
        return response_text
        
    except Exception as e:
        logger.error(f"Error in MCP chat: {e}", exc_info=True)
        return f"Sorry, I encountered an error: {str(e)}"