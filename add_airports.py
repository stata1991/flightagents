#!/usr/bin/env python3
"""
Add important Yellowstone-area airports to major_airports_filtered.json
"""

import json

# Important Yellowstone-area airports to add
new_airports = [
    {
        "column_1": "BZN",
        "airport_name": "Bozeman Yellowstone International Airport",
        "city_name": "Bozeman, MT",
        "country_name": "United States"
    },
    {
        "column_1": "JAC",
        "airport_name": "Jackson Hole Airport",
        "city_name": "Jackson, WY",
        "country_name": "United States"
    },
    {
        "column_1": "COD",
        "airport_name": "Yellowstone Regional Airport",
        "city_name": "Cody, WY",
        "country_name": "United States"
    },
    {
        "column_1": "LVM",
        "airport_name": "Mission Field Airport",
        "city_name": "Livingston, MT",
        "country_name": "United States"
    }
]

# Load existing database
with open('major_airports_filtered.json', 'r') as f:
    airports_data = json.load(f)

# Add new airports at the beginning
airports_data = new_airports + airports_data

# Save updated database
with open('major_airports_filtered.json', 'w') as f:
    json.dump(airports_data, f, indent=2)

print(f"Added {len(new_airports)} airports to database")
print("New total: {len(airports_data)} airports")
print("\nAdded airports:")
for airport in new_airports:
    print(f"  {airport['column_1']}: {airport['airport_name']}")
