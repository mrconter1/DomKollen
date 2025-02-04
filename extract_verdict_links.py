import requests
from bs4 import BeautifulSoup
import json
import time

def convert_to_url_safe(text):
    # Convert Swedish characters to URL-safe versions
    conversions = {
        'å': 'a',
        'ä': 'a',
        'ö': 'o',
        'Å': 'a',
        'Ä': 'a',
        'Ö': 'o',
        ' ': '-'
    }
    
    for char, replacement in conversions.items():
        text = text.replace(char, replacement)
    
    return text.lower()

def get_verdict_pdf(url):
    # Send GET request
    response = requests.get(url)
    
    # Check if request was successful
    if response.status_code != 200:
        print(f"Failed to fetch page {url}. Status code: {response.status_code}")
        return None
    
    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all PDF links
    for link in soup.find_all('a'):
        href = link.get('href', '')
        # Look for DOM PDFs
        if 'DOM' in href and href.endswith('.pdf'):
            return href
    
    return None

def scrape_court_ids(url, area_name, max_verdicts, current_count):
    # Send GET request
    response = requests.get(url)
    
    # Check if request was successful
    if response.status_code != 200:
        print(f"Failed to fetch page {url}. Status code: {response.status_code}")
        return [], current_count
    
    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all court IDs (they are in <a> tags)
    court_cases = []
    for link in soup.find_all('a'):
        if current_count >= max_verdicts:
            break
            
        text = link.text.strip()
        # Look for patterns like "B 1065-19"
        if text.startswith('B ') and '-' in text:
            # Get the case URL
            case_url = f"https://fup.link/tr/{convert_to_url_safe(area_name)}/{text.lower().replace(' ', '-')}"
            
            # Get verdict PDF URL
            print(f"Checking verdict for {text}...")
            verdict_pdf = get_verdict_pdf(case_url)
            
            # Only include cases with verdict PDFs
            if verdict_pdf:
                court_case = {
                    'court_id': text,
                    'area': area_name,
                    'verdict_pdf': verdict_pdf
                }
                court_cases.append(court_case)
                current_count += 1
                print(f"Found verdict PDF for {text} (Total: {current_count})")
                
                if current_count >= max_verdicts:
                    break
            
            # Add a small delay between case checks
            time.sleep(0.5)
    
    return court_cases, current_count

def scrape_areas(max_total_verdicts=10):
    # URL of the main page
    url = "https://fup.link/tr"
    
    # Send GET request
    response = requests.get(url)
    
    # Check if request was successful
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return
    
    # Parse HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all <a> tags within <li> tags
    all_court_cases = []
    current_count = 0
    
    for link in soup.select('li a'):
        if current_count >= max_total_verdicts:
            break
            
        area_name = link.text
        # Get area URL
        area_url = f"https://fup.link{link['href']}"
        
        # Get court cases for this area
        print(f"Scraping court IDs for {area_name}...")
        remaining_verdicts = max_total_verdicts - current_count
        court_cases, current_count = scrape_court_ids(area_url, area_name, max_total_verdicts, current_count)
        all_court_cases.extend(court_cases)
        
        print(f"Total verdicts found so far: {current_count}/{max_total_verdicts}")
        
        # Add a small delay to be nice to the server
        time.sleep(1)
    
    # Sort court cases by area and then by court_id
    all_court_cases.sort(key=lambda x: (x['area'], x['court_id']))
    
    # Save to JSON file
    with open('verdict_links.json', 'w', encoding='utf-8') as f:
        json.dump(all_court_cases, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully scraped {len(all_court_cases)} court cases with verdicts and saved to verdict_links.json")

if __name__ == "__main__":
    scrape_areas() 