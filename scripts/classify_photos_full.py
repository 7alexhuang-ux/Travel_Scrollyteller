
import os
import json
from PIL import Image
from PIL.ExifTags import TAGS

def get_exif_date(image_path):
    try:
        if not image_path.lower().endswith(('.jpg', '.jpeg')):
            return None
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None
        for tag, value in exif_data.items():
            if TAGS.get(tag) == 'DateTimeOriginal':
                return value
        return None
    except:
        return None

def main():
    inbox_dir = r"C:\Project\Alex_Diary\inbox\緬甸"
    files = os.listdir(inbox_dir)
    
    results = {
        'screenshots': [],
        'videos': [],
        'photos': [],
        'other': []
    }
    
    for f in files:
        path = os.path.join(inbox_dir, f)
        ext = os.path.splitext(f)[1].lower()
        size = os.path.getsize(path)
        
        item = {
            'filename': f,
            'size': size,
            'ext': ext
        }
        
        if ext in ('.png'):
            results['screenshots'].append(item)
        elif ext in ('.mp4', '.mov'):
            results['videos'].append(item)
        elif ext in ('.jpg', '.jpeg'):
            date = get_exif_date(path)
            item['date_taken'] = date
            results['photos'].append(item)
        else:
            results['other'].append(item)
            
    # Sort photos by date
    results['photos'].sort(key=lambda x: str(x.get('date_taken', '')))
    
    # Save detailed data
    with open('photo_classification.json', 'w', encoding='utf-8') as jf:
        json.dump(results, jf, indent=2, ensure_ascii=False)
        
    # Print summary
    print(f"Summary:")
    print(f"- Screenshots (PNG): {len(results['screenshots'])}")
    print(f"- Videos (MP4/MOV): {len(results['videos'])}")
    print(f"- Photos (JPG): {len(results['photos'])}")
    print(f"- Other: {len(results['other'])}")
    
    if results['photos']:
        dates = [p['date_taken'] for p in results['photos'] if p.get('date_taken')]
        if dates:
            print(f"- Photo Date Range: {min(dates)} to {max(dates)}")

if __name__ == "__main__":
    main()
