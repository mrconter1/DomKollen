import json
import requests
import io
import PyPDF2
import re
from typing import Optional, Dict, List, Tuple, Set
from collections import Counter

# Keywords to look for in the verdicts
KEYWORDS = [
    "bedrägeri",
    "bokföring",
    "barn",
    "förtal",
    "försök",
    "grov",
    "hets",
    "hot",
    "kroppsskada",
    "medhjälp",
    "misshandel",
    "mord",
    "narkotika",
    "rån",
    "sexuellt",
    "smuggling",
    "stöld",
    "tjänstefel",
    "tvång",
    "vapen",
    "vållande",
    "våld",
    "våldtäkt",
    "övergrepp",
    "kränkande",
    # Additional crime types
    "rattfylleri",
    "utpressning",
    "skadegörelse",
    "penningtvätt",
    "människohandel",
    "ofredande",
    "trakasserier",
    "dopning",
    "urkundsförfalskning",
    "koppleri"
]

def extract_case_ids(text: str) -> List[str]:
    # Regular expression to match case IDs (B followed by space and numbers-numbers)
    case_pattern = r'B\s+\d+-\d+'
    # Find all matches and remove duplicates while preserving order
    matches = re.finditer(case_pattern, text)
    seen = set()
    unique_cases = []
    for match in matches:
        case_id = match.group(0)
        if case_id not in seen:
            seen.add(case_id)
            unique_cases.append(case_id)
    return unique_cases

def extract_court_name(text: str) -> Optional[str]:
    # Regular expression to match court name before "TINGSRÄTT"
    court_pattern = r'^([A-ZÅÄÖ]+(?:\s[A-ZÅÄÖ]+)*)\sTINGSRÄTT'
    match = re.search(court_pattern, text, re.MULTILINE)
    if match:
        # Get the court name and format it
        court_name = match.group(1)
        # Convert to title case (first letter capital, rest lowercase)
        court_name = court_name.title()
        return court_name
    return None

def extract_date(text: str) -> Optional[str]:
    # Regular expression to match dates in format YYYY-MM-DD
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    match = re.search(date_pattern, text)
    return match.group(0) if match else None

def analyze_text_content(text: str) -> Dict[str, int]:
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Count occurrences of each keyword
    keyword_counts = {}
    for keyword in KEYWORDS:
        count = text_lower.count(keyword)
        if count > 0:  # Only include keywords that appear at least once
            keyword_counts[keyword] = count
    
    return keyword_counts

def get_sorted_tags(keyword_counts: Dict[str, int]) -> List[str]:
    # Sort keywords by count in descending order
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    return [keyword for keyword, count in sorted_keywords]

def get_significant_tags(tags: List[str], keyword_counts: Dict[str, int]) -> List[str]:
    if not tags or not keyword_counts:
        return []

    # Calculate total mentions
    total_mentions = sum(keyword_counts.values())
    
    # Get the maximum count for any tag
    max_count = max(keyword_counts.values())

    # Filter tags based on both relative and absolute thresholds
    return [tag for tag in tags if (
        keyword_counts[tag] / total_mentions >= 0.05 and  # Relative threshold: 5% of total mentions
        (keyword_counts[tag] >= 3 or keyword_counts[tag] / max_count >= 0.2)  # Absolute threshold
    )]

def download_and_process_pdf(url: str) -> Tuple[List[str], Dict[str, int], Optional[str], Optional[str], List[str], int]:
    try:
        # Download PDF
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to download PDF from {url}")
            return [], {}, None, None, [], 0
        
        # Create PDF reader object
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Get number of pages
        num_pages = len(pdf_reader.pages)
        
        # Extract text from first page only for court name and case IDs
        first_page_text = pdf_reader.pages[0].extract_text()
        
        # Extract case IDs and court name from first page
        case_ids = extract_case_ids(first_page_text)
        court_name = extract_court_name(first_page_text)
        
        # Extract text from all pages for full analysis
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Extract date from full text
        date = extract_date(full_text)
        
        # Analyze text content
        keyword_counts = analyze_text_content(full_text)
        
        # Get sorted tags based on frequency
        tags = get_sorted_tags(keyword_counts)
        
        return tags, keyword_counts, date, court_name, case_ids, num_pages
    except Exception as e:
        print(f"Error processing PDF {url}: {str(e)}")
        return [], {}, None, None, [], 0

def process_verdicts(input_file='verdict_links.json', output_file='court_cases.json'):
    # Load verdict links
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            verdict_links = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found. Please run extract_verdict_links.py first.")
        return
    except json.JSONDecodeError:
        print(f"Error: {input_file} is not a valid JSON file.")
        return

    # Process each verdict
    processed_cases = []
    total_cases = len(verdict_links)
    
    # Keep track of cases per tag
    cases_per_tag: Dict[str, int] = Counter()
    
    for i, url in enumerate(verdict_links, 1):
        print(f"Processing verdict {i}/{total_cases}")
        
        # Process PDF and get tags and counts
        tags, keyword_counts, date, court_name, case_ids, num_pages = download_and_process_pdf(url)
        
        # Get significant tags for this case
        significant_tags = get_significant_tags(tags, keyword_counts)
        
        # Update cases per tag count (increment by 1 for each significant tag in this case)
        cases_per_tag.update({tag: 1 for tag in significant_tags})
        
        # Add metadata to the case
        processed_case = {
            'court_ids': case_ids,
            'area': court_name if court_name else "Unknown",
            'verdict_pdf': url,
            'tags': tags,
            'keyword_counts': keyword_counts,
            'date': date,
            'num_pages': num_pages
        }
        
        processed_cases.append(processed_case)
        print(f"Court: {court_name}")
        print(f"Case IDs found: {case_ids}")
        print(f"Date found: {date}")
        print(f"Number of pages: {num_pages}")
        print(f"Keywords found: {keyword_counts}")
        print(f"All tags: {tags}")
        print(f"Significant tags: {significant_tags}")
        print("-" * 80)

    # Create the final output with both cases and tag statistics
    output_data = {
        'cases': processed_cases,
        'tag_stats': {
            'cases_per_tag': dict(cases_per_tag),
            'ordered_tags': [tag for tag, _ in sorted(cases_per_tag.items(), key=lambda x: (-x[1], x[0]))]
        }
    }

    # Save everything to a single JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nSuccessfully processed {len(processed_cases)} verdicts and saved to {output_file}")
    print("\nNumber of cases per significant tag:")
    for tag, count in sorted(cases_per_tag.items(), key=lambda x: (-x[1], x[0])):
        print(f"{tag}: {count} cases")

if __name__ == "__main__":
    process_verdicts() 