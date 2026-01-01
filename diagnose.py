#!/usr/bin/env python3
"""
Simple diagnostic tool to check API response
"""

import json
import requests
import sys

# Minimal test - you can pass API key as argument
api_key = sys.argv[1] if len(sys.argv) > 1 else input("Enter your SerpApi key: ")

params = {
    'engine': 'google_flights',
    'api_key': api_key,
    'departure_id': 'JFK',
    'arrival_id': 'LAX',
    'outbound_date': '2026-02-15',
    'return_date': '2026-02-22',
    'currency': 'USD',
    'hl': 'en'
}

print("Fetching flight data...")
response = requests.get('https://serpapi.com/search.json', params=params)
data = response.json()

# Save response
with open('sample_response.json', 'w') as f:
    json.dump(data, f, indent=2)
print("✓ Saved to sample_response.json")

# Analyze
print(f"\nTop-level keys: {list(data.keys())}")

if 'best_flights' in data and data['best_flights']:
    print(f"\nFound {len(data['best_flights'])} best_flights")
    print(f"First flight keys: {list(data['best_flights'][0].keys())}")

    if 'booking_token' in data['best_flights'][0]:
        print("✓ booking_token IS present")
        print(f"  Token preview: {data['best_flights'][0]['booking_token'][:60]}...")
    else:
        print("✗ booking_token is MISSING")
        print("\n  Available flight object:")
        print(json.dumps(data['best_flights'][0], indent=4)[:500])

if 'other_flights' in data and data['other_flights']:
    print(f"\nFound {len(data['other_flights'])} other_flights")
    if 'booking_token' in data['other_flights'][0]:
        print("✓ booking_token in other_flights")
    else:
        print("✗ booking_token missing from other_flights")

# Check for errors
if 'error' in data:
    print(f"\n❌ API Error: {data['error']}")

if 'search_metadata' in data:
    print(f"\nStatus: {data['search_metadata'].get('status', 'unknown')}")
