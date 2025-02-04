from bs4 import BeautifulSoup
import os
import json

def extract_areas():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, 'areas.html')
    
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all area links
    areas = []
    print("\nFound areas:")
    print("-" * 50)
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href.startswith('/tr/'):
            area = {
                'name': link.text,
                'path': href,
                'url': f'https://fup.link{href}'
            }
            areas.append(area)
            print(f"{link.text:<20} - {area['url']}")
    print("-" * 50)
    
    # Sort areas by name
    areas.sort(key=lambda x: x['name'])
    
    # Save to JSON file
    json_path = os.path.join(script_dir, 'areas.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(areas, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(areas)} areas to areas.json")
    return areas

if __name__ == "__main__":
    extract_areas() 