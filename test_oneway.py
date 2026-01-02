#!/usr/bin/env python3
"""
Test one-way flight to see the actual response structure
"""

import json
import requests
import sys

api_key = sys.argv[1] if len(sys.argv) > 1 else input("Enter your SerpApi key: ")

# Test one-way flight
params = {
    'engine': 'google_flights',
    'api_key': api_key,
    'departure_id': 'JFK',
    'arrival_id': 'LAX',
    'outbound_date': '2026-02-15',
    'type': '2',  # ONE WAY
    'currency': 'USD',
    'hl': 'en',
    'deep_search': 'true',
    'show_hidden': 'true'
}

print("Fetching ONE-WAY flight data...")
response = requests.get('https://serpapi.com/search.json', params=params)
data = response.json()

# Save response
with open('oneway_response.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✓ Saved to oneway_response.json\n")

# Check structure
print(f"Top-level keys: {list(data.keys())}\n")

if 'best_flights' in data and data['best_flights']:
    print(f"Found {len(data['best_flights'])} best_flights")
    print(f"First flight keys: {list(data['best_flights'][0].keys())}\n")

    # Check for booking_token
    if 'booking_token' in data['best_flights'][0]:
        print("✓ booking_token IS present in one-way flight")
        token = data['best_flights'][0]['booking_token']
        print(f"  Token preview: {token[:80]}...\n")

        # Try to use it
        print("Testing booking_token with booking options endpoint...")
        booking_params = {
            'engine': 'google_flights',
            'api_key': api_key,
            'booking_token': token,
            'departure_id': 'JFK',
            'arrival_id': 'LAX',
            'outbound_date': '2026-02-15',
            'type': '2',  # ONE WAY
            'currency': 'USD',
            'hl': 'en',
            'gl': 'us',
            'deep_search': 'true',
            'show_hidden': 'true'
        }

        booking_response = requests.get('https://serpapi.com/search.json', params=booking_params)
        print(f"Response status: {booking_response.status_code}")

        if booking_response.status_code == 200:
            print("✓ Booking options request successful!")
            booking_data = booking_response.json()

            if 'booking_options' in booking_data:
                print(f"✓ Found {len(booking_data['booking_options'])} booking options")
                if booking_data['booking_options']:
                    first_option = booking_data['booking_options'][0]
                    if 'together' in first_option:
                        print(f"  First OTA: {first_option['together'].get('book_with', 'N/A')}")
            else:
                print("✗ No booking_options in response")
                print(f"  Response keys: {list(booking_data.keys())}")
        else:
            print(f"✗ Booking options request failed: {booking_response.status_code}")
            print(f"  Error: {booking_response.text[:200]}")
    else:
        print("✗ booking_token is MISSING from one-way flight")
        print(f"  Available keys: {list(data['best_flights'][0].keys())}")

        # Check for departure_token instead
        if 'departure_token' in data['best_flights'][0]:
            print("  Note: departure_token is present (might need round-trip approach)")
else:
    print("No flights found in response")

if 'error' in data:
    print(f"\n❌ API Error: {data['error']}")
