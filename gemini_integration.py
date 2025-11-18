import os
import logging
import google.generativeai as genai
from google.generativeai.types import content_types

# Import tool registry for automatic tool discovery
from tools.registry import discover_and_get_tools, get_function_map, execute_tool

logger = logging.getLogger(__name__)

# Configure once at module level
_model = None

def is_gemini_available():
    """Check if Gemini API key is configured"""
    api_key = os.environ.get('GEMINI_API_KEY')
    return api_key is not None and api_key.strip() != ""

def get_gemini_model_with_tools():
    """Get or create Gemini model instance with tools"""
    global _model
    if _model is None:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        
        # Automatically discover all available tools
        tools = discover_and_get_tools()

        _model = genai.GenerativeModel('gemini-2.5-flash-lite', tools=tools)
        logger.info(f"✅ Initialized Gemini with {len(tools)} tools")
    
    return _model

def execute_function_call(function_call):
    """Execute the function that Gemini wants to call"""
    function_name = function_call.name
    function_args = dict(function_call.args) if function_call.args else {}

    logger.info(f"🔧 {function_name}({function_args})")

    # Use the registry to execute the tool
    return execute_tool(function_name, **function_args)
    
def chat_with_gemini(user_message, user_id=None, max_tokens=1000):
    """Chat with Gemini using native function calling with conversation history"""
    try:
        if not is_gemini_available():
            return "Gemini API key is not configured. Please set GEMINI_API_KEY environment variable."

        model = get_gemini_model_with_tools()

        # Get conversation history if user_id is provided
        history = []
        if user_id:
            from shared_state import get_conversation_history
            history = get_conversation_history(user_id)

        chat = model.start_chat(history=history)

        logger.info(f"📝 User message: {user_message}")

        # Send user message
        response = chat.send_message(user_message)
        
        # Check if Gemini wants to call a function
        function_calls = []
        for part in response.parts:
            if fn := part.function_call:
                function_calls.append(fn)
        
        if function_calls:
            # Execute all function calls
            for function_call in function_calls:
                function_name = function_call.name
                
                # Execute the function
                result = execute_function_call(function_call)
                
                logger.info(f"✅ Function result: {result}")

                # Ensure result is properly formatted for Gemini API
                # If result is a list, convert it to a dict with a meaningful key
                if isinstance(result, list):
                    formatted_result = {"items": result}
                elif not isinstance(result, dict):
                    # For strings, numbers, etc., wrap in a dict
                    formatted_result = {"value": result}
                else:
                    # Already a dict, use as-is
                    formatted_result = result

                # Send result back to Gemini for formatting
                response = chat.send_message(
                    content_types.to_content({
                        "parts": [{
                            "function_response": {
                                "name": function_name,
                                "response": formatted_result
                            }
                        }]
                    })
                )
                
                # Add tool footer
                try:
                    final_response = response.text
                    if "_🔧 Tool used:" not in final_response:
                        final_response += f"\n\n_🔧 Tool used: `{function_name}`_"

                    # Save conversation history
                    if user_id:
                        from shared_state import add_to_conversation_history
                        add_to_conversation_history(user_id, "user", user_message)
                        add_to_conversation_history(user_id, "model", final_response)

                    return final_response
                except Exception as e:
                    logger.warning(f"Could not get response.text: {e}")
                    # Fallback to a formatted response using the tool's output
                    if isinstance(result, dict) and "output" in result:
                        fallback_response = f"{result['output']}\n\n_🔧 Tool used: `{function_name}`_"
                    else:
                        fallback_response = f"Here's the result:\n\n{result}\n\n_🔧 Tool used: `{function_name}`_"

                    # Save conversation history
                    if user_id:
                        from shared_state import add_to_conversation_history
                        add_to_conversation_history(user_id, "user", user_message)
                        add_to_conversation_history(user_id, "model", fallback_response)

                    return fallback_response

        # No function call, just return text
        try:
            final_response = response.text

            # Save conversation history
            if user_id:
                from shared_state import add_to_conversation_history
                add_to_conversation_history(user_id, "user", user_message)
                add_to_conversation_history(user_id, "model", final_response)

            return final_response
        except Exception as e:
            logger.warning(f"Could not get response.text for direct response: {e}")
            fallback_response = "I understand your request but couldn't generate a proper response. Please try rephrasing your question."

            # Save conversation history
            if user_id:
                from shared_state import add_to_conversation_history
                add_to_conversation_history(user_id, "user", user_message)
                add_to_conversation_history(user_id, "model", fallback_response)

            return fallback_response
        
    except Exception as e:
        logger.error(f"Error communicating with Gemini: {e}", exc_info=True)
        error_response = f"Sorry, I encountered an error: {str(e)}"

        # Save conversation history even for errors
        if user_id:
            from shared_state import add_to_conversation_history
            add_to_conversation_history(user_id, "user", user_message)
            add_to_conversation_history(user_id, "model", error_response)

        return error_response