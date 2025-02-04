import json
import io
import PyPDF2
import re
from typing import Optional, Dict, List, Tuple, Set
from collections import Counter
import os
from multiprocessing import Pool, cpu_count

# Keywords to look for in the verdicts
KEYWORDS = [
    "bedrägeri",
    "bokföring",
    "barn",
    "förtal",
    "försök",
    "grov",
    "grovt",
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

def process_local_pdf(pdf_path: str) -> Tuple[List[str], Dict[str, int], Optional[str], Optional[str], List[str], int]:
    try:
        print(f"Opening PDF: {os.path.basename(pdf_path)}")
        
        # Open PDF file
        with open(pdf_path, 'rb') as pdf_file:
            print("Reading PDF structure...")
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Get number of pages
            num_pages = len(pdf_reader.pages)
            print(f"PDF has {num_pages} pages")
            
            # Extract text from all pages in one go
            print("Extracting text from all pages...")
            full_text = ""
            for i, page in enumerate(pdf_reader.pages):
                try:
                    print(f"Processing page {i+1}/{num_pages}...", end='\r')
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as e:
                    print(f"\nError on page {i+1}: {str(e)}")
                    continue
            
            if not full_text:
                print("Warning: No text could be extracted from PDF")
                return [], {}, None, None, [], num_pages
                
            print("\nExtracting metadata...")
            # Extract metadata from full text
            case_ids = extract_case_ids(full_text)
            court_name = extract_court_name(full_text)
            date = extract_date(full_text)
            
            print("Analyzing content...")
            # Analyze text content
            keyword_counts = analyze_text_content(full_text)
            
            # Get sorted tags based on frequency
            tags = get_sorted_tags(keyword_counts)
            
            return tags, keyword_counts, date, court_name, case_ids, num_pages
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {str(e)}")
        return [], {}, None, None, [], 0

def process_pdf_worker(args):
    pdf_path, pdf_file = args
    try:
        tags, keyword_counts, date, court_name, case_ids, num_pages = process_local_pdf(pdf_path)
        return {
            'filename': pdf_file,
            'tags': tags,
            'keyword_counts': keyword_counts,
            'date': date,
            'court_name': court_name,
            'case_ids': case_ids,
            'num_pages': num_pages,
            'success': True
        }
    except Exception as e:
        print(f"Worker error processing {pdf_file}: {str(e)}")
        return {
            'filename': pdf_file,
            'success': False
        }

def process_local_verdicts(limit=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdfs_dir = os.path.join(script_dir, 'pdfs')
    verdicts_json = os.path.join(script_dir, 'verdicts.json')
    
    if not os.path.exists(pdfs_dir):
        print(f"Error: {pdfs_dir} not found")
        return
    
    if not os.path.exists(verdicts_json):
        print(f"Error: {verdicts_json} not found")
        return
    
    print("Loading verdicts.json...")
    # Load verdicts.json to get the fup.link URLs
    with open(verdicts_json, 'r', encoding='utf-8') as f:
        verdicts_data = json.load(f)
    
    print("Creating URL lookup table...")
    # Create URL lookup by filename
    url_lookup = {}
    for verdict in verdicts_data:
        filename = f"{verdict['area']}_{verdict['case_id'].replace(' ', '_')}.pdf".lower()
        url_lookup[filename] = verdict['verdict_pdf']
    
    # Process PDFs
    processed_cases = []
    cases_per_tag = Counter()
    
    print("Scanning PDF directory...")
    # Get list of PDF files and sort them
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith('.pdf')]
    pdf_files.sort()
    
    # Limit to first N files (if limit is specified)
    if limit:
        pdf_files = pdf_files[:limit]
    total_files = len(pdf_files)
    
    print(f"\nProcessing {total_files} PDF files...")
    
    # Prepare arguments for parallel processing
    pdf_args = [(os.path.join(pdfs_dir, pdf_file), pdf_file) for pdf_file in pdf_files]
    
    # Use half of available CPU cores to avoid overloading
    num_processes = max(1, cpu_count() // 2)
    print(f"Using {num_processes} processes for parallel processing")
    
    # Process PDFs in parallel
    with Pool(num_processes) as pool:
        results = pool.map(process_pdf_worker, pdf_args)
    
    # Process results
    for result in results:
        if not result['success']:
            print(f"Skipping failed PDF: {result['filename']}")
            continue
            
        pdf_file = result['filename']
        tags = result['tags']
        keyword_counts = result['keyword_counts']
        date = result['date']
        court_name = result['court_name']
        case_ids = result['case_ids']
        num_pages = result['num_pages']
        
        # Skip cases where we couldn't extract the court name
        if not court_name:
            print(f"Skipping {pdf_file} - Could not determine court name")
            continue
        
        # Get significant tags for this case
        significant_tags = get_significant_tags(tags, keyword_counts)
        
        # Update cases per tag count
        cases_per_tag.update({tag: 1 for tag in significant_tags})
        
        # Get the fup.link URL for this PDF
        verdict_pdf = url_lookup.get(pdf_file.lower(), "")
        if not verdict_pdf:
            print(f"Warning: No URL found for {pdf_file}")
        
        # Add metadata to the case
        processed_case = {
            'court_ids': case_ids,
            'area': court_name,  # No need for the "Unknown" fallback since we skip those
            'verdict_pdf': verdict_pdf,
            'tags': tags,
            'keyword_counts': keyword_counts,
            'date': date,
            'num_pages': num_pages,
            'filename': pdf_file
        }
        
        processed_cases.append(processed_case)
        print(f"\nProcessed: {pdf_file}")
        print(f"Court: {court_name}")
        print(f"Case IDs: {case_ids}")
        print(f"Date: {date}")
        print(f"Pages: {num_pages}")
        print(f"Keywords: {len(keyword_counts)}")
        print(f"Significant tags: {significant_tags}")
        
        # Save progress after each batch
        output_data = {
            'cases': processed_cases,
            'tag_stats': {
                'cases_per_tag': dict(cases_per_tag),
                'ordered_tags': [tag for tag, _ in sorted(cases_per_tag.items(), key=lambda x: (-x[1], x[0]))]
            }
        }
        
        output_file = os.path.join(script_dir, 'court_cases.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nSuccessfully processed {len(processed_cases)} verdicts")
    print("\nNumber of cases per significant tag:")
    for tag, count in sorted(cases_per_tag.items(), key=lambda x: (-x[1], x[0])):
        print(f"{tag}: {count} cases")

if __name__ == "__main__":
    process_local_verdicts()  # Removed the limit to process all files 