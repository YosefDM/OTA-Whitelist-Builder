#!/usr/bin/env python3
"""
Quick start script for OTA Whitelist Builder
Runs a small test with just a few routes to verify setup
"""

import json
import sys
from pathlib import Path


def check_config():
    """Check if config.json exists and has API key"""
    if not Path("config.json").exists():
        print("❌ config.json not found")
        print("\nPlease create config.json:")
        print("  1. cp config.example.json config.json")
        print("  2. Edit config.json and add your SerpApi API key")
        return False

    with open("config.json", 'r') as f:
        config = json.load(f)

    api_key = config.get('serpapi', {}).get('api_key', '')

    if not api_key or api_key == "YOUR_SERPAPI_KEY_HERE":
        print("❌ SerpApi API key not configured")
        print("\nPlease edit config.json and add your API key")
        print("Get a free API key at: https://serpapi.com/users/sign_up")
        return False

    print("✓ Configuration file found")
    print(f"✓ API key configured: {api_key[:10]}...")
    return True


def check_dependencies():
    """Check if required Python packages are installed"""
    try:
        import requests
        print("✓ Required packages installed")
        return True
    except ImportError:
        print("❌ Required packages not installed")
        print("\nPlease run: pip install -r requirements.txt")
        return False


def run_test():
    """Run a quick test with 3 routes"""
    print("\n" + "="*80)
    print("RUNNING QUICK TEST (3 routes)")
    print("="*80 + "\n")

    # Import here so we can check dependencies first
    from scraper import OTAWhitelistBuilder

    # Create a test config with just 3 routes
    scraper = OTAWhitelistBuilder("config.json")

    # Load and limit routes
    routes = scraper.load_routes("routes.json")
    test_routes = routes[:3]  # Just first 3 routes

    print(f"Testing with {len(test_routes)} routes:")
    for route in test_routes:
        print(f"  - {route['description']}")

    print(f"\nThis will make approximately {len(test_routes) * 2} API calls")
    print("Estimated time: ~30 seconds\n")

    response = input("Continue with test? (yes/no): ")
    if response.lower() != 'yes':
        print("Test cancelled")
        return

    # Run scraper
    scraper.scrape_all_routes(test_routes)

    # Generate whitelist
    whitelist = scraper.generate_whitelist()

    # Save outputs
    scraper.save_outputs(whitelist)

    # Print summary
    scraper.print_summary(whitelist)

    print("\n✓ Quick test completed successfully!")
    print("\nNext steps:")
    print("  1. Check ota_whitelist.json and ota_whitelist.csv")
    print("  2. Run 'python scraper.py' to process all 65 routes")
    print("  3. Run 'python analyze_whitelist.py' to analyze results")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("OTA WHITELIST BUILDER - QUICK START")
    print("="*80 + "\n")

    print("Checking setup...\n")

    # Check configuration
    if not check_config():
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check routes file
    if not Path("routes.json").exists():
        print("❌ routes.json not found")
        sys.exit(1)

    print("✓ routes.json found")

    print("\n✓ All checks passed!\n")

    # Run test
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
