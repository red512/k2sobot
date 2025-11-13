#!/usr/bin/env python3
"""
Joke MCP Server - Simplified for subprocess communication
"""
import sys
import json
import random

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

def handle_request(request):
    """Handle a single JSON-RPC request"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id", 1)
    
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "get_random_joke",
                        "description": "Get a random programming joke",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_joke_by_index",
                        "description": "Get a specific joke by index (0-7)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "index": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 7
                                }
                            },
                            "required": ["index"]
                        }
                    },
                    {
                        "name": "count_jokes",
                        "description": "Get the total number of jokes",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "get_random_joke":
            joke = random.choice(JOKES)
            result = {
                "setup": joke["setup"],
                "punchline": joke["punchline"]
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result)}
                    ]
                }
            }
        
        elif tool_name == "get_joke_by_index":
            index = arguments.get("index", 0)
            if 0 <= index < len(JOKES):
                joke = JOKES[index]
                result = {
                    "setup": joke["setup"],
                    "punchline": joke["punchline"],
                    "index": index
                }
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(result)}
                        ]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Index must be 0-{len(JOKES)-1}"}
                }
        
        elif tool_name == "count_jokes":
            result = {
                "total_jokes": len(JOKES)
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result)}
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"}
    }

def main():
    """Main loop - read from stdin, write to stdout"""
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": 0,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()