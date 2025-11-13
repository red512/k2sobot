"""
Time-related tools
Provides current time, dates, and timestamps
"""
from datetime import datetime


def get_current_time():
    """
    Get the current time and date in multiple formats
    
    Returns:
        dict: Contains time, date, day, and full timestamp
        
    Example:
        >>> get_current_time()
        {
            'time': '10:45 PM',
            'date': 'Wednesday, November 12, 2025',
            'day': 'Wednesday',
            'full': '10:45 PM on Wednesday, November 12, 2025'
        }
    """
    now = datetime.now()
    return {
        "time": now.strftime("%I:%M %p"),
        "date": now.strftime("%A, %B %d, %Y"),
        "day": now.strftime("%A"),
        "full": now.strftime("%I:%M %p on %A, %B %d, %Y")
    }


def get_timestamp():
    """
    Get the current Unix timestamp
    
    Returns:
        dict: Unix timestamp and description
        
    Example:
        >>> get_timestamp()
        {
            'timestamp': 1699833900,
            'description': 'Seconds since January 1, 1970 00:00:00 UTC'
        }
    """
    return {
        "timestamp": int(datetime.now().timestamp()),
        "description": "Seconds since January 1, 1970 00:00:00 UTC"
    }