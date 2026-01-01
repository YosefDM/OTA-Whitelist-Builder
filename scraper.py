#!/usr/bin/env python3
"""
OTA Whitelist Builder - SerpApi Google Flights Scraper
Scrapes Google Flights via SerpApi to build a curated whitelist of trusted OTAs
"""

import json
import time
import logging
import re
from datetime import datetime
from typing import Dict, List, Set, Optional
from collections import defaultdict
from pathlib import Path
import requests


class OTAWhitelistBuilder:
    """Main class for scraping and building the OTA whitelist"""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the scraper with configuration"""
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.ota_data = defaultdict(lambda: {
            'count': 0,
            'first_seen': None,
            'last_seen': None,
            'routes': [],
            'is_airline': False,
            'normalized_name': None
        })
        self.raw_booking_data = []
        self.api_calls_made = 0

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}")
            print("Please copy config.example.json to config.json and add your API key")
            raise

    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.config['output']['logs']
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_routes(self, routes_file: str = "routes.json") -> List[Dict]:
        """Load routes from JSON file"""
        with open(routes_file, 'r') as f:
            data = json.load(f)
            return data['routes']

    def search_flights(self, route: Dict) -> Optional[List[Dict]]:
        """
        Step 1: Search for flights to get booking tokens
        For one-way flights, booking_token is returned directly
        """
        params = {
            'engine': 'google_flights',
            'api_key': self.config['serpapi']['api_key'],
            'departure_id': route['departure_id'],
            'arrival_id': route['arrival_id'],
            'outbound_date': route['outbound_date'],
            # Note: return_date is omitted for one-way flights
            'currency': self.config['scraping']['currency'],
            'hl': self.config['scraping']['hl'],
            'gl': self.config['scraping']['gl'],
            'type': self.config['scraping']['type'],  # Should be "2" for one-way
            'travel_class': self.config['scraping']['travel_class'],
            'adults': self.config['scraping']['adults']
        }

        try:
            self.logger.info(f"Searching flights for route {route['id']}: {route['description']}")
            response = requests.get(self.config['serpapi']['base_url'], params=params)
            response.raise_for_status()
            self.api_calls_made += 1

            data = response.json()

            # Extract flights with booking tokens
            flights = []
            for flight_list in ['best_flights', 'other_flights']:
                if flight_list in data:
                    flights.extend(data[flight_list])

            self.logger.info(f"Found {len(flights)} flights for route {route['id']}")
            return flights

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching flights for route {route['id']}: {e}")
            return None

    def get_return_flights(self, departure_token: str, route: Dict) -> Optional[List[Dict]]:
        """
        Step 2: Get return flights using departure token
        Returns list of return flights with booking_token
        """
        params = {
            'engine': 'google_flights',
            'api_key': self.config['serpapi']['api_key'],
            'departure_token': departure_token,
            'currency': self.config['scraping']['currency'],
            'hl': self.config['scraping']['hl']
        }

        try:
            self.logger.info(f"Getting return flights for route {route['id']}")
            response = requests.get(self.config['serpapi']['base_url'], params=params)
            response.raise_for_status()
            self.api_calls_made += 1

            data = response.json()

            # Extract return flights
            return_flights = []
            for flight_list in ['best_flights', 'other_flights']:
                if flight_list in data:
                    return_flights.extend(data[flight_list])

            self.logger.info(f"Found {len(return_flights)} return flight options for route {route['id']}")
            return return_flights

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting return flights for route {route['id']}: {e}")
            return None

    def get_booking_options(self, booking_token: str, route: Dict) -> Optional[Dict]:
        """
        Step 3: Get booking options using the booking token
        Returns booking options data with OTAs

        IMPORTANT: SerpApi requires flight parameters to be included with booking_token
        """
        params = {
            'engine': 'google_flights',
            'api_key': self.config['serpapi']['api_key'],
            'booking_token': booking_token,
            'departure_id': route['departure_id'],
            'arrival_id': route['arrival_id'],
            'outbound_date': route['outbound_date'],
            'currency': self.config['scraping']['currency'],
            'hl': self.config['scraping']['hl'],
            'gl': self.config['scraping']['gl'],
            'type': self.config['scraping']['type'],
            'travel_class': self.config['scraping']['travel_class'],
            'adults': self.config['scraping']['adults']
        }

        try:
            self.logger.info(f"Getting booking options for route {route['id']}")
            response = requests.get(self.config['serpapi']['base_url'], params=params)
            response.raise_for_status()
            self.api_calls_made += 1

            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting booking options for route {route['id']}: {e}")
            return None

    def extract_otas(self, booking_data: Dict, route: Dict):
        """
        Extract OTA names from booking options
        Updates self.ota_data with found OTAs
        """
        if 'booking_options' not in booking_data:
            self.logger.warning(f"No booking options found for route {route['id']}")
            return

        current_time = datetime.now().isoformat()

        for option in booking_data['booking_options']:
            # Handle both 'together' and separate tickets
            if 'together' in option:
                self._process_booking_option(option['together'], route, current_time)

            if option.get('separate_tickets', False):
                if 'departing' in option:
                    self._process_booking_option(option['departing'], route, current_time)
                if 'returning' in option:
                    self._process_booking_option(option['returning'], route, current_time)

    def _process_booking_option(self, option: Dict, route: Dict, current_time: str):
        """Process a single booking option"""
        ota_name = option.get('book_with', '')
        if not ota_name:
            return

        # Check if it's an airline
        is_airline = option.get('airline', False)

        # Skip airlines if configured to do so
        if is_airline and self.config['filters']['exclude_airlines']:
            self.logger.debug(f"Skipping airline: {ota_name}")
            return

        # Normalize the name
        normalized_name = self.normalize_ota_name(ota_name)

        # Update OTA data
        if self.ota_data[ota_name]['count'] == 0:
            self.ota_data[ota_name]['first_seen'] = current_time

        self.ota_data[ota_name]['count'] += 1
        self.ota_data[ota_name]['last_seen'] = current_time
        self.ota_data[ota_name]['is_airline'] = is_airline
        self.ota_data[ota_name]['normalized_name'] = normalized_name

        # Add route info
        route_info = {
            'route_id': route['id'],
            'description': route['description'],
            'category': route['category'],
            'price': option.get('price', None)
        }
        self.ota_data[ota_name]['routes'].append(route_info)

        self.logger.info(f"Found OTA: {ota_name} (airline: {is_airline}) on route {route['id']}")

    def normalize_ota_name(self, name: str) -> str:
        """
        Normalize OTA names to handle variations
        e.g., "British Airways" vs "britishairways.com"
        """
        if not self.config['filters']['normalize_names']:
            return name

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

    def scrape_all_routes(self, routes: List[Dict], limit: Optional[int] = None):
        """
        Main scraping loop - processes all routes
        For one-way flights, this is a 2-step process:
        1. Search flights → get booking_token
        2. Use booking_token → get booking options with OTAs
        """
        routes_to_process = routes[:limit] if limit else routes
        total_routes = len(routes_to_process)

        self.logger.info(f"Starting to scrape {total_routes} routes")
        self.logger.info(f"Estimated API calls: {total_routes * 2}")  # 2 calls per route for one-way

        for idx, route in enumerate(routes_to_process, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing route {idx}/{total_routes}: {route['description']}")
            self.logger.info(f"{'='*60}")

            # Step 1: Search for flights (one-way)
            flights = self.search_flights(route)
            if not flights:
                self.logger.warning(f"No flights found for route {route['id']}, skipping")
                continue

            # Get booking_token from first flight
            if 'booking_token' not in flights[0]:
                self.logger.warning(f"No booking_token found for route {route['id']}, skipping")
                continue

            booking_token = flights[0]['booking_token']

            # Rate limiting
            time.sleep(self.config['scraping']['rate_limit_delay'])

            # Step 2: Get booking options (with OTAs)
            booking_data = self.get_booking_options(booking_token, route)
            if not booking_data:
                self.logger.warning(f"No booking data found for route {route['id']}, skipping")
                continue

            # Store raw data
            self.raw_booking_data.append({
                'route': route,
                'booking_data': booking_data,
                'timestamp': datetime.now().isoformat()
            })

            # Step 3: Extract OTAs
            self.extract_otas(booking_data, route)

            # Progress update
            self.logger.info(f"Progress: {idx}/{total_routes} routes processed")
            self.logger.info(f"API calls made: {self.api_calls_made}")
            self.logger.info(f"Unique OTAs found so far: {len(self.ota_data)}")

        self.logger.info(f"\n{'='*60}")
        self.logger.info("Scraping completed!")
        self.logger.info(f"Total API calls made: {self.api_calls_made}")
        self.logger.info(f"Total unique OTAs found: {len(self.ota_data)}")
        self.logger.info(f"{'='*60}\n")

    def generate_whitelist(self) -> List[Dict]:
        """
        Generate the final OTA whitelist with filtering and sorting
        """
        whitelist = []
        min_freq = self.config['filters']['min_frequency']

        for ota_name, data in self.ota_data.items():
            if data['count'] >= min_freq:
                whitelist.append({
                    'name': ota_name,
                    'normalized_name': data['normalized_name'],
                    'frequency': data['count'],
                    'first_seen': data['first_seen'],
                    'last_seen': data['last_seen'],
                    'is_airline': data['is_airline'],
                    'routes_count': len(data['routes']),
                    'sample_routes': data['routes'][:5]  # First 5 routes as samples
                })

        # Sort by frequency (most common first)
        whitelist.sort(key=lambda x: x['frequency'], reverse=True)

        return whitelist

    def save_outputs(self, whitelist: List[Dict]):
        """Save outputs to JSON and CSV files"""
        # Save JSON whitelist
        json_file = self.config['output']['whitelist_json']
        with open(json_file, 'w') as f:
            json.dump({
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_routes_scraped': self.api_calls_made // 2,  # 2 calls per route (one-way)
                    'api_calls_made': self.api_calls_made,
                    'total_otas': len(whitelist),
                    'filters_applied': self.config['filters']
                },
                'whitelist': whitelist
            }, f, indent=2)
        self.logger.info(f"Saved JSON whitelist to {json_file}")

        # Save CSV whitelist
        csv_file = self.config['output']['whitelist_csv']
        with open(csv_file, 'w') as f:
            # Header
            f.write("Name,Normalized Name,Frequency,Is Airline,Routes Count,First Seen,Last Seen\n")
            # Data
            for ota in whitelist:
                f.write(f'"{ota["name"]}","{ota["normalized_name"]}",{ota["frequency"]},'
                       f'{ota["is_airline"]},{ota["routes_count"]},'
                       f'"{ota["first_seen"]}","{ota["last_seen"]}"\n')
        self.logger.info(f"Saved CSV whitelist to {csv_file}")

        # Save raw booking data
        raw_file = self.config['output']['raw_data']
        with open(raw_file, 'w') as f:
            json.dump(self.raw_booking_data, f, indent=2)
        self.logger.info(f"Saved raw booking data to {raw_file}")

    def print_summary(self, whitelist: List[Dict]):
        """Print a summary of the whitelist"""
        print("\n" + "="*80)
        print("OTA WHITELIST SUMMARY")
        print("="*80)
        print(f"Total OTAs found: {len(whitelist)}")
        print(f"Total routes scraped: {self.api_calls_made // 2}")  # 2 calls per route (one-way)
        print(f"Total API calls made: {self.api_calls_made}")
        print("\n" + "-"*80)
        print("TOP 20 OTAs BY FREQUENCY:")
        print("-"*80)
        print(f"{'Rank':<6}{'OTA Name':<40}{'Frequency':<12}{'Airline?':<10}")
        print("-"*80)

        for idx, ota in enumerate(whitelist[:20], 1):
            is_airline = "Yes" if ota['is_airline'] else "No"
            print(f"{idx:<6}{ota['name'][:38]:<40}{ota['frequency']:<12}{is_airline:<10}")

        print("="*80 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("OTA WHITELIST BUILDER - Google Flights Scraper via SerpApi")
    print("="*80 + "\n")

    # Initialize scraper
    try:
        scraper = OTAWhitelistBuilder("config.json")
    except Exception as e:
        print(f"Failed to initialize scraper: {e}")
        return

    # Load routes
    try:
        routes = scraper.load_routes("routes.json")
        print(f"Loaded {len(routes)} routes from routes.json\n")
    except Exception as e:
        print(f"Failed to load routes: {e}")
        return

    # Ask user for confirmation
    print(f"This will make approximately {len(routes) * 2} API calls to SerpApi.")
    print(f"With a 2-second delay between calls, this will take approximately {(len(routes) * 2 * 2) / 60:.1f} minutes.")
    response = input("\nDo you want to proceed? (yes/no): ")

    if response.lower() != 'yes':
        print("Scraping cancelled.")
        return

    # Scrape all routes
    scraper.scrape_all_routes(routes)

    # Generate whitelist
    whitelist = scraper.generate_whitelist()

    # Save outputs
    scraper.save_outputs(whitelist)

    # Print summary
    scraper.print_summary(whitelist)

    print("\nDone! Check the output files for the complete whitelist.")


if __name__ == "__main__":
    main()
