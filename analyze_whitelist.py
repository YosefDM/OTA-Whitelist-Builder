#!/usr/bin/env python3
"""
Utility script to analyze and visualize the OTA whitelist
"""

import json
from collections import Counter, defaultdict
from typing import Dict, List


def load_whitelist(filepath: str = "ota_whitelist.json") -> Dict:
    """Load the whitelist JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_frequency_distribution(whitelist: List[Dict]):
    """Analyze and print frequency distribution"""
    frequencies = [ota['frequency'] for ota in whitelist]

    print("\n" + "="*80)
    print("FREQUENCY DISTRIBUTION ANALYSIS")
    print("="*80)
    print(f"Total OTAs: {len(whitelist)}")
    print(f"Average frequency: {sum(frequencies) / len(frequencies):.2f}")
    print(f"Median frequency: {sorted(frequencies)[len(frequencies)//2]}")
    print(f"Max frequency: {max(frequencies)}")
    print(f"Min frequency: {min(frequencies)}")

    # Frequency brackets
    brackets = {
        '50+': sum(1 for f in frequencies if f >= 50),
        '40-49': sum(1 for f in frequencies if 40 <= f < 50),
        '30-39': sum(1 for f in frequencies if 30 <= f < 40),
        '20-29': sum(1 for f in frequencies if 20 <= f < 30),
        '10-19': sum(1 for f in frequencies if 10 <= f < 20),
        '5-9': sum(1 for f in frequencies if 5 <= f < 10),
        '1-4': sum(1 for f in frequencies if 1 <= f < 5)
    }

    print("\nFrequency Brackets:")
    for bracket, count in brackets.items():
        bar = "█" * count
        print(f"  {bracket:>6}: {bar} ({count})")


def analyze_by_category(whitelist: List[Dict]):
    """Analyze OTA distribution across route categories"""
    category_otas = defaultdict(set)

    for ota in whitelist:
        for route in ota.get('sample_routes', []):
            category = route.get('category', 'Unknown')
            category_otas[category].add(ota['name'])

    print("\n" + "="*80)
    print("OTA COVERAGE BY ROUTE CATEGORY")
    print("="*80)

    for category in sorted(category_otas.keys()):
        otas = category_otas[category]
        print(f"\n{category} ({len(otas)} unique OTAs):")
        print(f"  {', '.join(sorted(list(otas))[:10])}")
        if len(otas) > 10:
            print(f"  ... and {len(otas) - 10} more")


def find_category_specific_otas(whitelist: List[Dict]):
    """Find OTAs that appear only in specific categories"""
    ota_categories = defaultdict(set)

    for ota in whitelist:
        for route in ota.get('sample_routes', []):
            category = route.get('category', 'Unknown')
            ota_categories[ota['name']].add(category)

    print("\n" + "="*80)
    print("CATEGORY-SPECIFIC OTAs")
    print("="*80)

    # OTAs appearing in only one category
    single_category = {
        ota: list(cats)[0]
        for ota, cats in ota_categories.items()
        if len(cats) == 1
    }

    if single_category:
        print("\nOTAs appearing in only ONE category:")
        for ota, category in sorted(single_category.items()):
            print(f"  {ota}: {category}")
    else:
        print("\nNo OTAs are category-specific (all appear in multiple categories)")

    # Most versatile OTAs
    print("\nMost Versatile OTAs (appearing in most categories):")
    versatile = sorted(ota_categories.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for ota, cats in versatile:
        print(f"  {ota}: {len(cats)} categories")


def identify_premium_vs_budget(whitelist: List[Dict]):
    """Identify OTAs by premium vs budget route presence"""
    budget_routes = {'Budget Carriers', 'Regional'}

    ota_types = defaultdict(lambda: {'budget': 0, 'premium': 0, 'total': 0})

    for ota in whitelist:
        for route in ota.get('sample_routes', []):
            category = route.get('category', 'Unknown')
            ota_types[ota['name']]['total'] += 1

            if any(b in category for b in budget_routes):
                ota_types[ota['name']]['budget'] += 1
            else:
                ota_types[ota['name']]['premium'] += 1

    print("\n" + "="*80)
    print("PREMIUM vs BUDGET OTA ANALYSIS")
    print("="*80)

    # Calculate ratios
    budget_focused = []
    premium_focused = []
    balanced = []

    for ota, counts in ota_types.items():
        if counts['total'] < 5:  # Skip OTAs with too few samples
            continue

        budget_ratio = counts['budget'] / counts['total']

        if budget_ratio > 0.7:
            budget_focused.append((ota, budget_ratio))
        elif budget_ratio < 0.3:
            premium_focused.append((ota, budget_ratio))
        else:
            balanced.append((ota, budget_ratio))

    print(f"\nBudget-Focused OTAs (>70% budget routes):")
    for ota, ratio in sorted(budget_focused, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {ota}: {ratio*100:.1f}% budget")

    print(f"\nPremium-Focused OTAs (>70% premium routes):")
    for ota, ratio in sorted(premium_focused, key=lambda x: x[1])[:10]:
        print(f"  {ota}: {(1-ratio)*100:.1f}% premium")

    print(f"\nBalanced OTAs:")
    print(f"  Total: {len(balanced)} OTAs serve both budget and premium routes")


def detect_duplicates(whitelist: List[Dict]):
    """Detect potential duplicate OTAs with similar normalized names"""
    normalized_groups = defaultdict(list)

    for ota in whitelist:
        normalized_groups[ota['normalized_name']].append(ota['name'])

    print("\n" + "="*80)
    print("POTENTIAL DUPLICATES (same normalized name)")
    print("="*80)

    duplicates_found = False
    for norm_name, names in normalized_groups.items():
        if len(names) > 1:
            duplicates_found = True
            print(f"\n{norm_name}:")
            for name in names:
                freq = next(ota['frequency'] for ota in whitelist if ota['name'] == name)
                print(f"  - {name} (frequency: {freq})")

    if not duplicates_found:
        print("\nNo duplicates found - all OTA names are unique after normalization")


def export_simple_list(whitelist: List[Dict], output_file: str = "ota_simple_list.txt"):
    """Export a simple text list of OTA names"""
    with open(output_file, 'w') as f:
        f.write("# OTA Whitelist - Simple List\n")
        f.write(f"# Generated from {len(whitelist)} OTAs\n\n")

        for ota in whitelist:
            f.write(f"{ota['name']}\n")

    print(f"\nExported simple list to {output_file}")


def main():
    """Main analysis function"""
    print("\n" + "="*80)
    print("OTA WHITELIST ANALYSIS TOOL")
    print("="*80)

    try:
        data = load_whitelist()
        whitelist = data['whitelist']
        metadata = data['metadata']

        print(f"\nWhitelist generated at: {metadata['generated_at']}")
        print(f"Routes scraped: {metadata['total_routes_scraped']}")
        print(f"API calls made: {metadata['api_calls_made']}")
        print(f"Total OTAs: {metadata['total_otas']}")

        # Run analyses
        analyze_frequency_distribution(whitelist)
        analyze_by_category(whitelist)
        find_category_specific_otas(whitelist)
        identify_premium_vs_budget(whitelist)
        detect_duplicates(whitelist)

        # Export simple list
        export_simple_list(whitelist)

        print("\n" + "="*80)
        print("Analysis complete!")
        print("="*80 + "\n")

    except FileNotFoundError:
        print("\nError: ota_whitelist.json not found.")
        print("Please run scraper.py first to generate the whitelist.")
    except Exception as e:
        print(f"\nError during analysis: {e}")


if __name__ == "__main__":
    main()
