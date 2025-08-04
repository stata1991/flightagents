#!/usr/bin/env python3
import re
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def _extract_origin(message: str):
    """Extract origin from message"""
    # Look for "from X to Y" pattern - handle multi-word cities
    from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)"
    match = re.search(from_to_pattern, message.lower())
    if match:
        return match.group(1).strip().title()
    
    # Look for "go from X" pattern
    go_from_pattern = r"go\s+from\s+([a-zA-Z\s]+)"
    match = re.search(go_from_pattern, message.lower())
    if match:
        return match.group(1).strip().title()
    
    return None

def _extract_destination(message: str):
    """Extract destination from message"""
    # Look for "from X to Y" pattern - handle multi-word cities
    from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)"
    match = re.search(from_to_pattern, message.lower())
    if match:
        return match.group(2).strip().title()
    
    # Look for "go to X" pattern
    go_to_pattern = r"go\s+to\s+([a-zA-Z\s]+)"
    match = re.search(go_to_pattern, message.lower())
    if match:
        return match.group(1).strip().title()
    
    # Look for destination keywords
    destination_keywords = ["visit", "travel to", "explore"]
    for keyword in destination_keywords:
        if keyword in message.lower():
            # Extract the word after the keyword
            pattern = rf"{keyword}\s+([a-zA-Z\s]+)"
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).strip().title()
    
    return None

# Test the functions directly
test_message = "from dallas to las vegas"
print(f"Testing message: '{test_message}'")
origin = _extract_origin(test_message)
destination = _extract_destination(test_message)
print(f"Origin: {origin}")
print(f"Destination: {destination}")

test_message2 = "I want to go from dallas to las vegas for 5 days with my family"
print(f"\nTesting message: '{test_message2}'")
origin2 = _extract_origin(test_message2)
destination2 = _extract_destination(test_message2)
print(f"Origin: {origin2}")
print(f"Destination: {destination2}") 