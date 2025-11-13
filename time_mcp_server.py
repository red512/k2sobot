#!/usr/bin/env python3
"""
Time MCP Server - Simplified for subprocess communication
"""
import sys
import json
from datetime import datetime

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
                        "name": "get_current_time",
                        "description": "Get the current date and time",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_timestamp",
                        "description": "Get the current Unix timestamp",
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
        
        if tool_name == "get_current_time":
            now = datetime.now()
            result = {
                "iso_format": now.isoformat(),
                "human_readable": now.strftime("%I:%M %p on %A, %B %d, %Y"),
                "time_only": now.strftime("%I:%M %p"),
                "date_only": now.strftime("%A, %B %d, %Y"),
                "day_of_week": now.strftime("%A")
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
        
        elif tool_name == "get_timestamp":
            timestamp = int(datetime.now().timestamp())
            result = {
                "unix_timestamp": timestamp,
                "description": "Seconds since January 1, 1970 00:00:00 UTC"
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