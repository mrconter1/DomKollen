import os
import json
import time
import keyboard

def load_verdicts():
    """Load verdicts from JSON file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'verdicts.json')
    
    if not os.path.exists(json_path):
        print("Error: verdicts.json not found. Please run extract_verdicts.py first.")
        return None
        
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def setup_pdfs_folder():
    """Create/ensure pdfs folder exists"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdfs_dir = os.path.join(script_dir, 'pdfs')
    
    if not os.path.exists(pdfs_dir):
        os.makedirs(pdfs_dir)
    
    return pdfs_dir

def get_existing_pdfs(pdfs_dir):
    """Get list of already downloaded PDFs"""
    if not os.path.exists(pdfs_dir):
        return set()
    return {f.lower() for f in os.listdir(pdfs_dir) if f.endswith('.pdf')}

def download_verdicts(start_area="malmö", start_case="B 11677-20"):
    verdicts = load_verdicts()
    if not verdicts:
        return
    
    pdfs_dir = setup_pdfs_folder()
    existing_pdfs = get_existing_pdfs(pdfs_dir)
    
    # Filter out verdicts that are already downloaded
    pending_verdicts = []
    for verdict in verdicts:
        filename = f"{verdict['area']}_{verdict['case_id'].replace(' ', '_')}.pdf".lower()
        if filename not in existing_pdfs:
            pending_verdicts.append(verdict)
    
    if not pending_verdicts:
        print("\nAll PDFs have already been downloaded!")
        return
    
    # Find starting point if specified
    start_index = 0
    if start_area and start_case:
        for i, verdict in enumerate(pending_verdicts):
            if verdict['area'].lower() == start_area.lower() and verdict['case_id'] == start_case:
                start_index = i
                break
    
    pending_verdicts = pending_verdicts[start_index:]
    total_verdicts = len(verdicts)
    pending_count = len(pending_verdicts)
    downloaded_count = total_verdicts - pending_count
    
    print(f"\nFound {downloaded_count} already downloaded PDFs")
    print(f"Need to download {pending_count} PDFs")
    if start_index > 0:
        print(f"Starting from: {start_area} - {start_case}")
    
    print("\nStarting browser automation in 5 seconds...")
    print("Make sure Chrome is the active window!")
    print("Press 'q' to quit at any time")
    time.sleep(5)
    
    try:
        for i, verdict in enumerate(pending_verdicts, 1):
            if keyboard.is_pressed('q'):
                print("\nQuitting...")
                break
            
            case_id = verdict['case_id']
            area = verdict['area']
            pdf_url = verdict['verdict_pdf']
            
            print(f"\nDownloading verdict {i}/{pending_count}")
            print(f"Area: {area}")
            print(f"Case: {case_id}")
            
            # Select URL bar and navigate to PDF
            keyboard.press_and_release('ctrl+l')
            time.sleep(0.25)
            keyboard.write(pdf_url)
            keyboard.press_and_release('enter')
            
            # Wait for PDF to load
            print("Waiting for PDF to load...")
            time.sleep(2)
            
            # Save PDF
            keyboard.press_and_release('ctrl+s')
            time.sleep(1)
            
            # Create filename: area_caseid.pdf
            filename = f"{area}_{case_id.replace(' ', '_')}.pdf"
            pdf_path = os.path.join(pdfs_dir, filename)
            
            # Type save path and save
            keyboard.write(pdf_path)
            time.sleep(0.5)
            keyboard.press_and_release('enter')
            
            # Wait for save to complete
            time.sleep(0.5)
            
            print(f"Saved: {filename}")
            
    except Exception as e:
        print(f"Error: {e}")
        print(f"Last processed: {area} - {case_id}")
    
    print("\nDone!")

if __name__ == "__main__":
    # Start from Malmö B 11677-20
    download_verdicts() 