import os
import json
import time
import keyboard
import shutil

def setup_areas_folder():
    """Create/empty the areas folder"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    areas_dir = os.path.join(script_dir, 'areas')
    
    # Remove if exists and create new
    if os.path.exists(areas_dir):
        shutil.rmtree(areas_dir)
    os.makedirs(areas_dir)
    
    return areas_dir

def load_areas():
    """Load areas from JSON file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'areas.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_area_pages():
    # Setup areas folder
    areas_dir = setup_areas_folder()
    
    # Load areas from JSON
    areas = load_areas()
    
    print("\nStarting browser automation in 5 seconds...")
    print("Make sure Chrome is the active window!")
    print("Press 'q' to quit at any time")
    time.sleep(5)
    
    try:
        for i, area in enumerate(areas, 1):
            if keyboard.is_pressed('q'):
                print("\nQuitting...")
                break
            
            print(f"\nProcessing {area['name']} ({i}/{len(areas)})...")
            
            # Select URL bar
            keyboard.press_and_release('ctrl+l')
            time.sleep(0.5)
            
            # Type URL and press enter
            keyboard.write(area['url'])
            keyboard.press_and_release('enter')
            
            # Wait for page to load (1.5 seconds)
            print("Waiting for page to load...")
            time.sleep(1.5)
            
            # Save page (Ctrl+S)
            keyboard.press_and_release('ctrl+s')
            time.sleep(1)
            
            # Type filename and press enter
            area_filename = f"{area['name'].lower()}.html"
            keyboard.write(os.path.join(areas_dir, area_filename))
            time.sleep(0.5)
            keyboard.press_and_release('enter')
            
            # Wait for save dialog to complete
            time.sleep(2)
            
            print(f"Saved {area_filename}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nDone!")

if __name__ == "__main__":
    save_area_pages() 