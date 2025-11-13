"""
Joke-related tools
Provides programming and tech jokes
"""
import random


# Centralized joke database
JOKES = [
    {
        "setup": "Why do programmers prefer dark mode?",
        "punchline": "Because light attracts bugs!"
    },
    {
        "setup": "Why did the developer go broke?",
        "punchline": "Because he used up all his cache!"
    },
    {
        "setup": "How many programmers does it take to change a light bulb?",
        "punchline": "None. It's a hardware problem!"
    },
    {
        "setup": "Why do Java developers wear glasses?",
        "punchline": "Because they don't C#!"
    },
    {
        "setup": "What's a programmer's favorite hangout place?",
        "punchline": "Foo Bar!"
    },
    {
        "setup": "Why did the Kubernetes pod go to therapy?",
        "punchline": "It had too many container issues!"
    },
    {
        "setup": "What do you call a developer who doesn't comment their code?",
        "punchline": "A job security expert!"
    },
    {
        "setup": "Why was the JavaScript developer sad?",
        "punchline": "Because he didn't Node how to Express himself!"
    }
]


def get_random_joke():
    """
    Get a random programming joke
    
    Returns:
        dict: Contains setup and punchline
        
    Example:
        >>> get_random_joke()
        {
            'setup': 'Why do programmers prefer dark mode?',
            'punchline': 'Because light attracts bugs!'
        }
    """
    return random.choice(JOKES)
