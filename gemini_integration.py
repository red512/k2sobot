import os
import logging
import google.generativeai as genai

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
        _model = genai.GenerativeModel('gemini-2.5-flash-lite')  # Use free tier model
    return _model

def chat_with_gemini(user_message, max_tokens=1000):
    """Send a message to Gemini and get response"""
    try:
        if not is_gemini_available():
            return "Gemini API key is not configured. Please set GEMINI_API_KEY environment variable."

        model = get_gemini_model()

        # Generate response with safety settings
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