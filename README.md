# DomKollen

DomKollen is a modern web application for exploring and analyzing Swedish court verdicts. It provides an intuitive interface for legal professionals, researchers, and the public to search, filter, and analyze court cases based on various criteria.

## Overview

The application processes court verdict PDFs and extracts key information such as case IDs, dates, court names, and relevant legal keywords. The processed data is presented through a responsive web interface that allows users to:

- Filter cases by multiple criteria including date ranges and legal areas
- Search and filter by legal keywords and themes
- Sort verdicts by date, length, and other attributes
- Analyze keyword frequencies and patterns across verdicts
- View detailed case information with direct links to original verdict PDFs

## Technical Stack

- Frontend: React with TypeScript, utilizing Next.js for server-side rendering
- UI Components: Material-UI for a modern, responsive interface
- Data Processing: Python scripts for PDF processing and text analysis
- Data Storage: Structured JSON for efficient data querying and updates

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Visit `http://localhost:3000` in your browser

## Data Processing

The system uses two main Python scripts:
- `extract_verdict_links.py`: Collects verdict PDF URLs from court websites
- `process_verdicts.py`: Downloads PDFs, extracts text, and performs keyword analysis

The processed data is stored in `court_cases.json`, which serves as the primary data source for the web interface.

## License

This project is open source and available under the MIT license. 
