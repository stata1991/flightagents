#!/usr/bin/env python3
import re

def test_extract_origin(message: str):
    """Test origin extraction"""
    # Look for "from X to Y" pattern - handle multi-word cities
    from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)"
    match = re.search(from_to_pattern, message.lower())
    if match:
        origin = match.group(1).strip().title()
        destination = match.group(2).strip().title()
        print(f"Origin: '{origin}'")
        print(f"Destination: '{destination}'")
        return origin, destination
    
    # Look for "go from X" pattern
    go_from_pattern = r"go\s+from\s+([a-zA-Z\s]+)"
    match = re.search(go_from_pattern, message.lower())
    if match:
        origin = match.group(1).strip().title()
        print(f"Origin: '{origin}'")
        return origin, None
    
    print("No origin found")
    return None, None

# Test cases
test_messages = [
    "from dallas to las vegas",
    "I want to go from dallas to las vegas for 5 days with my family",
    "go from dallas to las vegas",
    "travel from new york to los angeles"
]

for message in test_messages:
    print(f"\nTesting: '{message}'")
    origin, destination = test_extract_origin(message)
    print(f"Result: origin='{origin}', destination='{destination}'") 