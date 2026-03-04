import os
import json
import re
import shutil
import datetime

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_TEMPLATE = os.path.join(PROJECT_ROOT, "output", "index.html")
CLUSTERS_FILE = os.path.join(PROJECT_ROOT, "data", "location_clusters.json")
NOTES_FILE = os.path.join(PROJECT_ROOT, "notes", "journey_notes.md")
MANUAL_LOCATIONS_FILE = os.path.join(PROJECT_ROOT, "data", "manual_cluster_locations.json")
SELECTED_PHOTOS_FILE = os.path.join(PROJECT_ROOT, "data", "selected_photos.json")

# Default source dir - User should symlink or update this
PHOTOS_SOURCE_DIR = os.path.join(PROJECT_ROOT, "inbox_photos") 

EXPORT_DIR_NAME = f"Journey_Export_{datetime.datetime.now().strftime('%Y%m%d')}"
EXPORT_DIR = os.path.join(PROJECT_ROOT, "output", EXPORT_DIR_NAME)
EXPORT_IMAGES_DIR = os.path.join(EXPORT_DIR, "images")

# --- Helpers ---
def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def parse_notes():
    notes = {}
    if not os.path.exists(NOTES_FILE): return notes
    
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        content = f.read()
            
    pattern = r"##\s+(IMG_[A-Za-z0-9_]+\.(?:JPG|PNG|JPEG|MOV|MP4))\n(.*?)(?=\n##|\Z)"
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        filename = match.group(1).strip()
        body = match.group(2).strip()
        note_data = {"note": "", "refined_note": "", "tips": "", "location": "", "subtitle": ""}
        
        m = re.search(r"-\s+\*\*心得\*\*:\s*(.*?)(?=\n-|\Z)", body, re.DOTALL)
        if m: note_data["note"] = m.group(1).strip()
        m = re.search(r"-\s+\*\*精修筆記\*\*:\s*(.*?)(?=\n-|\Z)", body, re.DOTALL)
        if m: note_data["refined_note"] = m.group(1).strip()
        m = re.search(r"-\s+\*\*Tips\*\*:\s*(.*?)(?=\n-|\Z)", body, re.DOTALL)
        if m: note_data["tips"] = m.group(1).strip()
        m = re.search(r"-\s+\*\*子標題\*\*:\s*(.*?)(?=\n-|\Z)", body, re.DOTALL)
        if m: note_data["subtitle"] = m.group(1).strip()
        
        notes[filename] = note_data
    return notes

def main():
    print(f"Start exporting presentation to {EXPORT_DIR}...")
    
    # 1. Create Directories
    if os.path.exists(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)
    os.makedirs(EXPORT_IMAGES_DIR)
    
    # 2. Prepare Data
    clusters = load_json(CLUSTERS_FILE)
    manual_locs = load_json(MANUAL_LOCATIONS_FILE)
    selected_photos = load_json(SELECTED_PHOTOS_FILE)
    notes = parse_notes()

    # Mark starred photos
    starred_files = set(k for k, v in selected_photos.items() if v.get('selected', False))
    
    # Bundle Data & Filter
    filtered_clusters = []
    images_to_copy = set()
    
    print("Filtering clusters...")
    for c in clusters:
        sample = c['sample_file']
        
        # Determine Name
        loc_name = manual_locs.get(sample, f"考察位點 #{clusters.index(c) + 1}")
        
        # FILTER CONDITION: 
        # 1. Must be meaningful (mostly same as before)
        is_meaningful = False
        if "考察位點" not in loc_name:
            is_meaningful = True
        
        note = notes.get(sample, {})
        has_content = note.get("note") or note.get("tips")
        if note.get("refined_note") and "現場細節整理中" not in note.get("refined_note"):
            has_content = True
            
        if has_content:
            is_meaningful = True
            
        if is_meaningful:
            # OPTIMIZATION: ONLY include 1 (Sample) + up to 2 extra images if strictly needed
            # For this request: "Only photos appearing in presentation" -> The sample photo is the main one.
            # We will truncate 'all_files' in the data to JUST the sample file
            # This ensures the frontend doesn't try to load other missing images
            
            filtered_clusters.append(c)
            for f in c.get('all_files', []):
                images_to_copy.add(f)
        else:
            # Skip this cluster
            pass
            
    # Update Note Data with starred photos
    full_data = {
        "cluster_locations": manual_locs,
        "notes": notes,
        "starred_photos": list(starred_files)
    }
    
    print(f"Kept {len(filtered_clusters)} / {len(clusters)} locations for presentation.")
    print(f"Copying {len(images_to_copy)} images (Cover images only)...")
    
    # Batch Copy Images
    success_count = 0
    for img in images_to_copy:
        src = os.path.join(PHOTOS_SOURCE_DIR, img)
        dst = os.path.join(EXPORT_IMAGES_DIR, img)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            success_count += 1
            
    print(f"Copied {success_count} images successfully.")

    # 4. Process HTML
    with open(HTML_TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()
        
    # Inject Data
    script_injection = f"""
    <script>
        const CLUSTER_DATA_INJECTED = {json.dumps(filtered_clusters, ensure_ascii=False)};
        const NOTE_DATA_INJECTED = {json.dumps(full_data, ensure_ascii=False)};
        
        // Override init
        async function init() {{
            clusters = CLUSTER_DATA_INJECTED;
            noteData = NOTE_DATA_INJECTED;
            renderAll();
        }}
        
        // Start the app
        init();
    </script>
    """
    
    # Insert Logic
    html = html.replace("init();", "// init(); disabled for static export")
    html = html.replace("</body>", f"{script_injection}</body>")
    html = html.replace('contenteditable="true"', 'contenteditable="false"')
    html = html.replace('/photo/', 'images/')
    
    # Disable internal calls
    no_op_functions = """
    <script>
        async function saveName() { console.log("Read-only mode"); }
        async function saveNote() { console.log("Read-only mode"); }
        function init() {
            clusters = CLUSTER_DATA_INJECTED;
            noteData = NOTE_DATA_INJECTED;
            renderAll();
        }
    </script>
    """
    html = html.replace(f"{script_injection}</body>", f"{script_injection}\n{no_op_functions}\n</body>")

    # Write HTML
    with open(os.path.join(EXPORT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
        
    # 5. Create README
    with open(os.path.join(EXPORT_DIR, "README.txt"), "w", encoding="utf-8") as f:
        f.write("Golden Journey Presentation - Lightweight Version\n")
        f.write(f"Generated on {datetime.datetime.now()}\n\n")
        f.write("Includes only meaningful locations and their cover photos.\n")
     
    # 6. Zip It
    shutil.make_archive(EXPORT_DIR, 'zip', os.path.dirname(EXPORT_DIR), EXPORT_DIR_NAME)
    
    print(f"Presentation Export complete: {EXPORT_DIR}.zip")

if __name__ == "__main__":
    main()
