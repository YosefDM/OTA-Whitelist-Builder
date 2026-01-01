# OTA Whitelist Builder

A Python tool to build a curated whitelist of trusted Online Travel Agencies (OTAs) by scraping Google Flights via SerpApi. This whitelist can be used to filter Aviasales API results in SMSPilot or similar flight search applications.

## Overview

This tool scrapes Google Flights booking options across 65 diverse flight routes to identify legitimate OTAs that appear in Google's flight search results. By analyzing booking options from multiple route categories (domestic US, international, budget carriers, etc.), it creates a comprehensive whitelist of trusted travel booking platforms.

## Features

- **Comprehensive Route Coverage**: 65 carefully selected routes across multiple categories:
  - US Domestic (major hubs, secondary markets, regional)
  - US to Europe (major and secondary cities)
  - US to Asia
  - Budget carrier routes
  - International-to-international

- **Two-Step Scraping Process**:
  1. Flight search to obtain booking tokens
  2. Booking options retrieval to extract OTA names

- **Intelligent Data Processing**:
  - OTA name normalization (handles variations like "Booking.com" vs "booking")
  - Airline filtering (excludes direct airline bookings)
  - Frequency tracking (identifies most common OTAs)
  - Metadata collection (first seen, last seen, route coverage)

- **Multiple Output Formats**:
  - JSON with full metadata
  - CSV for spreadsheet analysis
  - Raw booking data for further analysis

## Requirements

- Python 3.7+
- SerpApi account with API key ([sign up for free](https://serpapi.com/users/sign_up))
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd OTA-Whitelist-Builder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
cp config.example.json config.json
```

4. Edit `config.json` and add your SerpApi API key:
```json
{
  "serpapi": {
    "api_key": "YOUR_SERPAPI_KEY_HERE",
    ...
  }
}
```

## Usage

### Basic Usage

Run the scraper with default settings (all 65 routes):

```bash
python scraper.py
```

The script will:
1. Load routes from `routes.json`
2. Display estimated API calls and time
3. Ask for confirmation
4. Scrape all routes
5. Generate whitelist files

### Configuration Options

Edit `config.json` to customize behavior:

```json
{
  "scraping": {
    "currency": "USD",           // Currency for prices
    "hl": "en",                  // Language
    "gl": "us",                  // Country
    "rate_limit_delay": 2,       // Seconds between API calls
    "max_retries": 3,            // Retry failed requests
    "retry_delay": 5             // Delay before retry
  },
  "filters": {
    "exclude_airlines": true,    // Filter out direct airline bookings
    "min_frequency": 1,          // Minimum appearances to include in whitelist
    "normalize_names": true      // Normalize OTA names
  },
  "output": {
    "whitelist_json": "ota_whitelist.json",
    "whitelist_csv": "ota_whitelist.csv",
    "raw_data": "raw_booking_data.json",
    "logs": "scraping_logs.txt"
  }
}
```

## Output Files

### 1. `ota_whitelist.json`

Complete whitelist with metadata:

```json
{
  "metadata": {
    "generated_at": "2026-01-01T12:00:00",
    "total_routes_scraped": 65,
    "api_calls_made": 130,
    "total_otas": 45
  },
  "whitelist": [
    {
      "name": "Expedia",
      "normalized_name": "expedia",
      "frequency": 48,
      "first_seen": "2026-01-01T12:05:00",
      "last_seen": "2026-01-01T14:30:00",
      "is_airline": false,
      "routes_count": 48,
      "sample_routes": [...]
    },
    ...
  ]
}
```

### 2. `ota_whitelist.csv`

Spreadsheet-friendly format:

```csv
Name,Normalized Name,Frequency,Is Airline,Routes Count,First Seen,Last Seen
Expedia,expedia,48,False,48,2026-01-01T12:05:00,2026-01-01T14:30:00
Booking.com,booking,45,False,45,2026-01-01T12:06:00,2026-01-01T14:31:00
...
```

### 3. `raw_booking_data.json`

Complete raw data from SerpApi for further analysis:

```json
[
  {
    "route": {...},
    "booking_data": {...},
    "timestamp": "2026-01-01T12:05:00"
  },
  ...
]
```

### 4. `scraping_logs.txt`

Detailed logs of the scraping process.

## Route Categories

The 65 routes are distributed across these categories:

| Category | Count | Description |
|----------|-------|-------------|
| US Domestic - Major Hubs | 15 | JFK-LAX, ORD-SFO, ATL-SEA, etc. |
| US Domestic - Secondary | 15 | PHX-LAS, MCO-EWR, MSP-PDX, etc. |
| US to Europe - Major | 15 | JFK-LHR, EWR-CDG, BOS-FCO, etc. |
| US to Europe - Secondary | 15 | SFO-FRA, MIA-MUC, ATL-BCN, etc. |
| US to Asia | 10 | LAX-NRT, SFO-BKK, JFK-HKG, etc. |
| Budget Carriers | 10 | Spirit, Frontier, Southwest routes |
| Regional | 10 | Alaska Airlines, JetBlue, regional jets |
| International-International | 5 | LHR-CDG, HKG-NRT, DXB-LHR, etc. |

## API Usage

- **Total API Calls**: 130 (65 routes × 2 calls per route)
- **SerpApi Free Tier**: 250 calls/month
- **Estimated Time**: ~4.5 minutes (with 2-second delay between calls)
- **Monthly Maintenance**: 20-30 calls for spot-checks

## Expected Results

Based on the route diversity, you should expect to find:

- **30-60 unique OTAs** in the whitelist
- **Common OTAs**: Expedia, Booking.com, Priceline, Kayak, CheapOair, Orbitz, Travelocity, Kiwi.com, eDreams, Momondo
- **Regional OTAs**: Gotogate, BudgetAir, FlightHub, JustFly
- **Meta-search**: Kayak, Skyscanner, Google Flights
- **Airline sites**: If `exclude_airlines: false`, you'll also see official airline websites

## Name Normalization

The tool handles common OTA name variations:

- "Booking.com" → "booking"
- "Expedia.com" → "expedia"
- "Priceline.com" → "priceline"
- Removes domains (.com, .net, .org, .travel)
- Removes special characters
- Converts to lowercase

## Integration with SMSPilot/Aviasales

Use the generated whitelist to filter Aviasales API results:

```python
import json

# Load whitelist
with open('ota_whitelist.json', 'r') as f:
    whitelist_data = json.load(f)

# Create set of trusted OTAs
trusted_otas = {
    ota['normalized_name']
    for ota in whitelist_data['whitelist']
}

# Filter Aviasales results
def filter_aviasales_results(results, trusted_otas):
    return [
        result for result in results
        if normalize_name(result['agency']) in trusted_otas
    ]
```

## Limitations

- **Google Flights Coverage**: Only includes OTAs that appear in Google Flights
- **Temporal Variations**: OTA availability may change over time
- **Route Dependency**: Results may vary based on specific routes
- **API Costs**: Beyond free tier, SerpApi charges per search

## Maintenance

To keep the whitelist current:

1. **Monthly Updates**: Run on a subset of routes (~10-15) to check for new OTAs
2. **Quarterly Full Refresh**: Re-run all 65 routes
3. **Add New Routes**: Update `routes.json` with emerging markets or airlines

## Troubleshooting

### "Config file not found"
- Ensure `config.json` exists (copy from `config.example.json`)
- Check file permissions

### "No flights found"
- Verify dates are in the future
- Check airport codes are valid IATA codes
- Some routes may have limited availability

### "Rate limit exceeded"
- Increase `rate_limit_delay` in config
- Check SerpApi account status

### "Invalid API key"
- Verify API key in `config.json`
- Check SerpApi account is active

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check SerpApi documentation: https://serpapi.com/google-flights-api

## Acknowledgments

- SerpApi for Google Flights API access
- Route selection based on aviation industry data

---

**Note**: This tool is for research and legitimate business purposes. Ensure compliance with SerpApi's terms of service and applicable laws.
