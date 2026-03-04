
import json

def main():
    DIRECTORY = os.getcwd()
    INPUT_PATH = os.path.join(DIRECTORY, "projects", "Golden_Journey", "data", "gps_samples.json")
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    # Simple clustering by lat/lon rounding to roughly 500m
    clusters = {}
    for s in samples:
        if 'lat' in s and 'lon' in s:
            # Approx 0.005 is roughly 500m
            key = (round(s['lat'], 3), round(s['lon'], 3))
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(s)
    
    print(f"Total Unique Locations Detected (approx 500m radius): {len(clusters)}")
    
    # Sort locations by number of photos (density)
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
    
    summary = []
    for (lat, lon), items in sorted_clusters:
        items_sorted = sorted(items, key=lambda x: x.get('date', ''))
        summary.append({
            'lat': lat,
            'lon': lon,
            'count': len(items),
            'start_time': items_sorted[0].get('date', 'Unknown'),
            'end_time': items_sorted[-1].get('date', 'Unknown'),
            'sample_file': items_sorted[0]['filename'],
            'all_files': [i['filename'] for i in items_sorted]
        })
        
    OUTPUT_PATH = os.path.join(DIRECTORY, "projects", "Golden_Journey", "data", "location_clusters.json")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as jf:
        json.dump(summary, jf, indent=2)

if __name__ == "__main__":
    main()
