
import os
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_decimal_from_dms(dms, ref):
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])
    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds
    return degrees + minutes / 60.0 + seconds / 3600.0

def get_exif_and_gps(image_path):
    try:
        if not image_path.lower().endswith(('.jpg', '.jpeg')):
            return None
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None
        
        info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'DateTimeOriginal':
                info['date'] = value
            elif tag_name == 'GPSInfo':
                gps_json = {}
                for t in value:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_json[sub_tag] = value[t]
                
                if 'GPSLatitude' in gps_json and 'GPSLatitudeRef' in gps_json:
                    info['lat'] = get_decimal_from_dms(gps_json['GPSLatitude'], gps_json['GPSLatitudeRef'])
                if 'GPSLongitude' in gps_json and 'GPSLongitudeRef' in gps_json:
                    info['lon'] = get_decimal_from_dms(gps_json['GPSLongitude'], gps_json['GPSLongitudeRef'])
        return info
    except:
        return None

def main():
    inbox_dir = r"C:\Project\Alex_Diary\inbox\緬甸"
    # 全量掃描所有 JPG 檔案
    files = sorted([f for f in os.listdir(inbox_dir) if f.lower().endswith(('.jpg', '.jpeg'))])
    
    samples = []
    print(f"🔥 開始全量掃描 {len(files)} 張照片...")
    
    count = 0
    for f in files:
        path = os.path.join(inbox_dir, f)
        info = get_exif_and_gps(path)
        if info:
            info['filename'] = f
            samples.append(info)
        count += 1
        if count % 500 == 0:
            print(f"已處理 {count} / {len(files)}...")
            
    DIRECTORY = os.getcwd()
    OUTPUT_PATH = os.path.join(DIRECTORY, "projects", "Golden_Journey", "data", "gps_samples.json")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as jf:
        json.dump(samples, jf, indent=2)
    
    print(f"✅ 全量掃描完成。共提取到 {len([s for s in samples if 'lat' in s])} 個帶有 GPS 的點位。")

if __name__ == "__main__":
    main()
