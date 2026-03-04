
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None
        
        decoded = {}
        for tag, value in exif_data.items():
            decoded[TAGS.get(tag, tag)] = value
        
        # GPS data
        if 'GPSInfo' in decoded:
            gps_data = {}
            for t in decoded['GPSInfo']:
                sub_tag = GPSTAGS.get(t, t)
                gps_data[sub_tag] = decoded['GPSInfo'][t]
            decoded['GPSInfo'] = gps_data
            
        return decoded
    except Exception as e:
        return {'error': str(e)}

def main():
    inbox_dir = r"C:\Project\Alex_Diary\inbox\緬甸"
    # Sample first 5 images
    files = [f for f in os.listdir(inbox_dir) if f.lower().endswith('.jpg')][:5]
    for f in files:
        full_path = os.path.join(inbox_dir, f)
        print(f"File: {f}")
        exif = get_exif_data(full_path)
        if exif:
            print(f"  Date Taken: {exif.get('DateTimeOriginal')}")
            print(f"  GPS Info: {exif.get('GPSInfo')}")
        else:
            print("  No EXIF data")
        print("-" * 20)

if __name__ == "__main__":
    main()
