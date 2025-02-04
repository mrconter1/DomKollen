# Manual Scraping Scripts

This directory contains scripts for manually scraping court case data using a combination of browser automation and HTML parsing.

## Scripts

### extract_areas.py
Extracts all court area links from a saved HTML page of the main court listing.

Usage:
```bash
python extract_areas.py <path_to_html_file>
```

The script will:
1. Parse the provided HTML file
2. Extract all court area links
3. Save the data to `areas.json` with the following structure:
```json
[
  {
    "name": "Court Name",
    "path": "/tr/court-path",
    "url": "https://fup.link/tr/court-path"
  }
]
```

## Workflow
1. Save the main court listing page HTML
2. Run extract_areas.py to get all court areas
3. Use the generated areas.json for further processing 