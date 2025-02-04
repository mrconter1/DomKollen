from bs4 import BeautifulSoup
import os
import json
import time
import keyboard

def load_area_cases(area_file):
    """Extract all case URLs from an area HTML file"""
    with open(area_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    cases = []
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href.startswith('/tr/'):
            cases.append({
                'case_id': link.text,
                'url': f'https://fup.link{href}'
            })
    return cases

def load_existing_verdicts(script_dir):
    """Load existing verdicts from JSON file if it exists"""
    output_file = os.path.join(script_dir, 'verdicts.json')
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def is_verdict_duplicate(verdict, existing_verdicts):
    """Check if a verdict is already in the list"""
    for existing in existing_verdicts:
        if (existing['area'] == verdict['area'] and 
            existing['case_id'] == verdict['case_id'] and
            existing['verdict_pdf'] == verdict['verdict_pdf']):
            return True
    return False

def process_areas(start_from="sundsvalls"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    areas_dir = os.path.join(script_dir, 'areas')
    
    if not os.path.exists(areas_dir):
        print("Error: areas directory not found. Please run save_area_pages.py first.")
        return
    
    # Load existing verdicts
    verdicts = load_existing_verdicts(script_dir)
    print(f"\nLoaded {len(verdicts)} existing verdicts")
    
    # Get area files and find starting point
    area_files = [f for f in os.listdir(areas_dir) if f.endswith('.html')]
    area_files.sort()  # Sort alphabetically
    
    start_index = 0
    for i, file in enumerate(area_files):
        if start_from in file.lower():
            start_index = i
            break
    
    area_files = area_files[start_index:]  # Start from specified area
    print(f"\nStarting from {area_files[0]}")
    
    print("\nStarting browser automation in 5 seconds...")
    print("Make sure Chrome is the active window!")
    print("Press 'q' to quit at any time")
    time.sleep(5)
    
    try:
        for i, area_file in enumerate(area_files, 1):
            if keyboard.is_pressed('q'):
                print("\nQuitting...")
                break
            
            print(f"\nProcessing {area_file} ({i}/{len(area_files)})...")
            area_path = os.path.join(areas_dir, area_file)
            cases = load_area_cases(area_path)
            
            for j, case in enumerate(cases, 1):
                if keyboard.is_pressed('q'):
                    print("\nQuitting...")
                    break
                
                print(f"  Checking case {case['case_id']} ({j}/{len(cases)})...")
                
                # Select URL bar and navigate to case
                keyboard.press_and_release('ctrl+l')
                time.sleep(0.5)
                keyboard.write(case['url'])
                keyboard.press_and_release('enter')
                
                # Wait for page to load
                print("    Waiting for page to load...")
                time.sleep(1)
                
                # Save page for processing
                keyboard.press_and_release('ctrl+s')
                time.sleep(1)
                
                # Save to temp file
                temp_file = os.path.join(script_dir, 'temp_case.html')
                keyboard.write(temp_file)
                time.sleep(0.5)
                keyboard.press_and_release('enter')
                time.sleep(2)
                
                # Read temp file and look for DOM pdf
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        if href.endswith('.pdf') and 'DOM' in href:
                            verdict = {
                                'area': area_file.replace('.html', ''),
                                'case_id': case['case_id'],
                                'case_url': case['url'],
                                'verdict_pdf': href
                            }
                            if not is_verdict_duplicate(verdict, verdicts):
                                verdicts.append(verdict)
                                print(f"    Found new verdict PDF: {href}")
                            else:
                                print(f"    Skipping duplicate verdict: {href}")
                            break
                except Exception as e:
                    print(f"    Error processing case HTML: {e}")
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Save all verdicts to JSON
        if verdicts:
            output_file = os.path.join(script_dir, 'verdicts.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(verdicts, f, ensure_ascii=False, indent=2)
            print(f"\nSaved {len(verdicts)} verdicts to verdicts.json")
        else:
            print("\nNo verdicts found")

if __name__ == "__main__":
    process_areas() 