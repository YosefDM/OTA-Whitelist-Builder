#!/usr/bin/env python3
"""
Example integration with Aviasales API using the OTA whitelist
This demonstrates how to filter Aviasales results to only show trusted OTAs
"""

import json
import re
from typing import List, Dict, Set


class OTAFilter:
    """Filter for Aviasales results based on OTA whitelist"""

    def __init__(self, whitelist_path: str = "ota_whitelist.json"):
        """Initialize with whitelist"""
        self.whitelist = self._load_whitelist(whitelist_path)
        self.trusted_otas = self._build_trusted_set()
        self.ota_metadata = self._build_metadata_dict()

    def _load_whitelist(self, path: str) -> List[Dict]:
        """Load the whitelist JSON"""
        with open(path, 'r') as f:
            data = json.load(f)
            return data['whitelist']

    def _build_trusted_set(self) -> Set[str]:
        """Build a set of normalized trusted OTA names"""
        return {ota['normalized_name'] for ota in self.whitelist}

    def _build_metadata_dict(self) -> Dict[str, Dict]:
        """Build a dictionary mapping normalized names to metadata"""
        return {
            ota['normalized_name']: {
                'original_name': ota['name'],
                'frequency': ota['frequency'],
                'is_airline': ota['is_airline']
            }
            for ota in self.whitelist
        }

    def normalize_name(self, name: str) -> str:
        """
        Normalize an OTA name (same logic as scraper)
        """
        # Remove common domains and extensions
        normalized = re.sub(r'\.(com|net|org|travel|co\.uk)$', '', name.lower())

        # Remove special characters and extra spaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Handle common variations
        replacements = {
            'booking com': 'booking',
            'priceline com': 'priceline',
            'expedia com': 'expedia',
            'kayak com': 'kayak',
            'cheapoair com': 'cheapoair',
            'orbitz com': 'orbitz',
            'travelocity com': 'travelocity',
            'hotwire com': 'hotwire'
        }

        for old, new in replacements.items():
            if old in normalized:
                normalized = normalized.replace(old, new)

        return normalized

    def is_trusted(self, ota_name: str) -> bool:
        """Check if an OTA is in the whitelist"""
        normalized = self.normalize_name(ota_name)
        return normalized in self.trusted_otas

    def get_ota_info(self, ota_name: str) -> Dict:
        """Get metadata about an OTA"""
        normalized = self.normalize_name(ota_name)
        return self.ota_metadata.get(normalized, {})

    def filter_aviasales_results(self, results: List[Dict]) -> List[Dict]:
        """
        Filter Aviasales API results to only include trusted OTAs

        Args:
            results: List of flight results from Aviasales API

        Returns:
            Filtered list containing only results from trusted OTAs
        """
        filtered = []

        for result in results:
            # Aviasales typically has a 'gate' or 'agency' field
            # Adjust based on actual API response structure
            agency = result.get('gate') or result.get('agency') or result.get('seller')

            if agency and self.is_trusted(agency):
                # Add whitelist metadata to the result
                result['whitelist_info'] = self.get_ota_info(agency)
                filtered.append(result)

        return filtered

    def filter_and_sort(self, results: List[Dict], sort_by: str = 'price') -> List[Dict]:
        """
        Filter and sort Aviasales results

        Args:
            results: List of flight results from Aviasales API
            sort_by: 'price', 'frequency', or 'trust'

        Returns:
            Filtered and sorted list
        """
        filtered = self.filter_aviasales_results(results)

        if sort_by == 'price':
            # Sort by price (assuming there's a 'price' field)
            filtered.sort(key=lambda x: x.get('price', float('inf')))

        elif sort_by == 'frequency':
            # Sort by OTA frequency (most common OTAs first)
            filtered.sort(
                key=lambda x: x.get('whitelist_info', {}).get('frequency', 0),
                reverse=True
            )

        elif sort_by == 'trust':
            # Sort by trust score (could be custom logic)
            # For now, using frequency as a proxy for trust
            filtered.sort(
                key=lambda x: x.get('whitelist_info', {}).get('frequency', 0),
                reverse=True
            )

        return filtered

    def get_stats(self, results: List[Dict]) -> Dict:
        """
        Get statistics about filtered vs unfiltered results

        Args:
            results: Original Aviasales results

        Returns:
            Dictionary with statistics
        """
        total = len(results)
        filtered = self.filter_aviasales_results(results)
        trusted_count = len(filtered)

        # Count by OTA
        ota_counts = {}
        for result in filtered:
            agency = result.get('gate') or result.get('agency') or result.get('seller')
            if agency:
                ota_counts[agency] = ota_counts.get(agency, 0) + 1

        return {
            'total_results': total,
            'trusted_results': trusted_count,
            'filtered_out': total - trusted_count,
            'filter_rate': f"{(trusted_count/total*100):.1f}%" if total > 0 else "N/A",
            'unique_trusted_otas': len(ota_counts),
            'ota_breakdown': ota_counts
        }


# Example usage
def example_usage():
    """Example of how to use the OTA filter"""

    # Initialize filter
    print("Initializing OTA filter...")
    filter = OTAFilter("ota_whitelist.json")

    print(f"Loaded whitelist with {len(filter.trusted_otas)} trusted OTAs\n")

    # Simulated Aviasales API results
    # In real usage, this would come from actual API call
    simulated_results = [
        {
            'id': 1,
            'origin': 'JFK',
            'destination': 'LAX',
            'price': 299,
            'gate': 'Expedia',
            'airline': 'Delta'
        },
        {
            'id': 2,
            'origin': 'JFK',
            'destination': 'LAX',
            'price': 289,
            'gate': 'SomeUnknownOTA',
            'airline': 'Delta'
        },
        {
            'id': 3,
            'origin': 'JFK',
            'destination': 'LAX',
            'price': 310,
            'gate': 'Booking.com',
            'airline': 'American'
        },
        {
            'id': 4,
            'origin': 'JFK',
            'destination': 'LAX',
            'price': 295,
            'gate': 'Priceline',
            'airline': 'United'
        },
        {
            'id': 5,
            'origin': 'JFK',
            'destination': 'LAX',
            'price': 285,
            'gate': 'ShadyBookings123',
            'airline': 'Delta'
        }
    ]

    # Filter results
    print("Filtering Aviasales results...")
    filtered_results = filter.filter_and_sort(simulated_results, sort_by='price')

    print(f"\nFiltered {len(simulated_results)} results -> {len(filtered_results)} trusted results\n")

    # Display filtered results
    print("="*80)
    print("TRUSTED FLIGHT OPTIONS (sorted by price)")
    print("="*80)

    for result in filtered_results:
        ota = result.get('gate')
        price = result.get('price')
        airline = result.get('airline')
        freq = result.get('whitelist_info', {}).get('frequency', 'N/A')

        print(f"\n${price} - {airline} via {ota}")
        print(f"  OTA Frequency Score: {freq}")

    # Get statistics
    stats = filter.get_stats(simulated_results)

    print("\n" + "="*80)
    print("FILTERING STATISTICS")
    print("="*80)
    print(f"Total results: {stats['total_results']}")
    print(f"Trusted results: {stats['trusted_results']}")
    print(f"Filtered out: {stats['filtered_out']}")
    print(f"Filter rate: {stats['filter_rate']}")
    print(f"Unique trusted OTAs: {stats['unique_trusted_otas']}")

    print("\nOTA Breakdown:")
    for ota, count in stats['ota_breakdown'].items():
        print(f"  {ota}: {count} results")

    # Test individual OTA checking
    print("\n" + "="*80)
    print("INDIVIDUAL OTA CHECKS")
    print("="*80)

    test_otas = ['Expedia', 'Booking.com', 'SomeUnknownOTA', 'expedia.com', 'KAYAK']

    for ota in test_otas:
        is_trusted = filter.is_trusted(ota)
        info = filter.get_ota_info(ota)
        status = "✓ TRUSTED" if is_trusted else "✗ NOT TRUSTED"

        print(f"\n{ota}: {status}")
        if is_trusted:
            print(f"  Original name: {info.get('original_name')}")
            print(f"  Frequency: {info.get('frequency')}")
            print(f"  Is airline: {info.get('is_airline')}")


if __name__ == "__main__":
    try:
        example_usage()
    except FileNotFoundError:
        print("\nError: ota_whitelist.json not found.")
        print("Please run scraper.py first to generate the whitelist.")
    except Exception as e:
        print(f"\nError: {e}")
