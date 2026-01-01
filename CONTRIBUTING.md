# Contributing to OTA Whitelist Builder

Thank you for your interest in contributing to the OTA Whitelist Builder! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Setup](#development-setup)
4. [Adding New Routes](#adding-new-routes)
5. [Improving Name Normalization](#improving-name-normalization)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct that promotes:
- Respectful and inclusive communication
- Constructive feedback
- Focus on what is best for the community
- Empathy towards other contributors

## How to Contribute

There are many ways to contribute:

### 1. Report Bugs
- Check if the bug has already been reported in Issues
- If not, create a new issue with:
  - Clear title and description
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (Python version, OS, etc.)
  - Logs or error messages

### 2. Suggest Enhancements
- Check if the enhancement has been suggested
- Create an issue describing:
  - The problem it solves
  - Proposed solution
  - Alternatives considered
  - Example use cases

### 3. Submit Code Changes
- Fix bugs
- Add features
- Improve documentation
- Enhance tests

## Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/OTA-Whitelist-Builder.git
cd OTA-Whitelist-Builder
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up configuration:
```bash
cp config.example.json config.json
# Add your SerpApi key to config.json
```

6. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

## Adding New Routes

To add new routes to `routes.json`:

1. Follow the existing format:
```json
{
  "id": 66,
  "category": "Category Name",
  "departure_id": "IATA_CODE",
  "arrival_id": "IATA_CODE",
  "outbound_date": "2026-MM-DD",
  "return_date": "2026-MM-DD",
  "description": "City to City"
}
```

2. Guidelines:
   - Use valid 3-letter IATA airport codes
   - Set dates in the future (at least 2 weeks out)
   - Choose dates that avoid major holidays (for typical pricing)
   - Ensure the route represents real flight service
   - Add to appropriate category or create new category

3. Categories to consider:
   - Emerging markets (Africa, South America)
   - Low-cost carriers specific routes
   - Seasonal/charter routes
   - Business routes (city pairs with high business travel)

## Improving Name Normalization

The `normalize_ota_name()` function can always be improved. To enhance it:

1. Identify problematic variations:
   - Review `raw_booking_data.json` for duplicate OTAs
   - Run `analyze_whitelist.py` to find potential duplicates

2. Add normalization rules in `scraper.py`:
```python
# In normalize_ota_name method
replacements = {
    'old_variation': 'normalized',
    # Add your new mappings here
}
```

3. Test your changes:
   - Run quick_start.py
   - Check for reduced duplicates
   - Verify correct grouping

4. Document patterns you've addressed

## Testing

Before submitting changes:

1. **Quick Test**:
```bash
python quick_start.py
```
This runs a 3-route test to verify basic functionality.

2. **Full Test** (if you have API credits):
```bash
python scraper.py
```
Then verify outputs with:
```bash
python analyze_whitelist.py
```

3. **Code Quality**:
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Keep functions focused and small
- Add comments for complex logic

4. **Integration Test**:
```bash
python aviasales_integration_example.py
```

## Pull Request Process

1. **Before submitting**:
   - Update CHANGELOG.md with your changes
   - Update README.md if needed
   - Ensure your code follows the project style
   - Test your changes thoroughly

2. **Commit messages**:
   - Use clear, descriptive messages
   - Format: `type: brief description`
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   - Examples:
     - `feat: add support for one-way flights`
     - `fix: handle missing booking_token gracefully`
     - `docs: improve installation instructions`

3. **Create pull request**:
   - Provide clear title and description
   - Reference any related issues
   - Explain what changed and why
   - Include test results if applicable

4. **After submission**:
   - Respond to feedback promptly
   - Make requested changes in new commits
   - Keep the PR focused (one feature/fix per PR)

## Specific Contribution Ideas

### High Priority
- [ ] Add more international routes
- [ ] Improve OTA name normalization
- [ ] Add support for additional APIs beyond SerpApi
- [ ] Create automated tests

### Medium Priority
- [ ] Add async support for faster scraping
- [ ] Build a web dashboard
- [ ] Add database storage option
- [ ] Create Docker container

### Low Priority / Nice to Have
- [ ] Add price trend analysis
- [ ] Create mobile app integration
- [ ] Add email notifications
- [ ] Build REST API

## Questions?

If you have questions:
1. Check existing issues and documentation
2. Create a new issue with the "question" label
3. Be specific about what you're trying to do

## Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- CHANGELOG.md

Thank you for contributing! 🙏
