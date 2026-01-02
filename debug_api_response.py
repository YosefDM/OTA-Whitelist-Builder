#!/usr/bin/env python3
"""
Debug script to inspect actual SerpApi response structure
"""

import json
import requests


def debug_single_route():
    """Test a single route and print the full response"""

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Test with a simple route
    params = {
        'engine': 'google_flights',
        'api_key': config['serpapi']['api_key'],
        'departure_id': 'JFK',
        'arrival_id': 'LAX',
        'outbound_date': '2026-02-15',
        'return_date': '2026-02-22',
        'currency': 'USD',
        'hl': 'en',
        'gl': 'us',
        'deep_search': 'true',
        'show_hidden': 'true',
        'type': '1',
        'travel_class': '1',
        'adults': '1'
    }

    print("Making API request...")
    response = requests.get('https://serpapi.com/search.json', params=params)
    data = response.json()

    # Save full response
    with open('debug_response.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("\n" + "="*80)
    print("API RESPONSE STRUCTURE")
    print("="*80)

    # Print top-level keys
    print("\nTop-level keys:")
    for key in data.keys():
        print(f"  - {key}")

    # Check for flights
    if 'best_flights' in data:
        print(f"\nbest_flights: {len(data['best_flights'])} flights")
        if data['best_flights']:
            print("\nFirst best_flight keys:")
            for key in data['best_flights'][0].keys():
                print(f"  - {key}")

            # Check for booking_token
            if 'booking_token' in data['best_flights'][0]:
                print("\n✓ booking_token found!")
                print(f"  Sample: {data['best_flights'][0]['booking_token'][:50]}...")
            else:
                print("\n✗ booking_token NOT found in best_flights[0]")
                print("\nFull first flight object:")
                print(json.dumps(data['best_flights'][0], indent=2))

    if 'other_flights' in data:
        print(f"\nother_flights: {len(data['other_flights'])} flights")
        if data['other_flights']:
            print("\nFirst other_flight keys:")
            for key in data['other_flights'][0].keys():
                print(f"  - {key}")

            if 'booking_token' in data['other_flights'][0]:
                print("\n✓ booking_token found!")
            else:
                print("\n✗ booking_token NOT found in other_flights[0]")

    # Check search metadata
    if 'search_metadata' in data:
        print("\nSearch metadata:")
        print(f"  Status: {data['search_metadata'].get('status')}")
        print(f"  ID: {data['search_metadata'].get('id')}")

    print("\n" + "="*80)
    print("Full response saved to debug_response.json")
    print("="*80 + "\n")

    # Try with deep_search
    print("\nTrying with deep_search=true...")
    params['deep_search'] = 'true'

    response = requests.get('https://serpapi.com/search.json', params=params)
    data_deep = response.json()

    with open('debug_response_deep.json', 'w') as f:
        json.dump(data_deep, f, indent=2)

    if 'best_flights' in data_deep and data_deep['best_flights']:
        if 'booking_token' in data_deep['best_flights'][0]:
            print("✓ booking_token found with deep_search!")
        else:
            print("✗ booking_token still not found with deep_search")
            print("\nKeys in first flight with deep_search:")
            for key in data_deep['best_flights'][0].keys():
                print(f"  - {key}")

    print("\nDeep search response saved to debug_response_deep.json\n")


if __name__ == "__main__":
    try:
        debug_single_route()
    except FileNotFoundError:
        print("Error: config.json not found")
        print("Please set up your configuration first")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
