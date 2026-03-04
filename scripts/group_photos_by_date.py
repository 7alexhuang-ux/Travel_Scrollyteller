
import json
from collections import Counter

def main():
    with open('photo_classification.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    photos = data['photos']
    date_groups = Counter()
    
    for p in photos:
        dt = p.get('date_taken')
        if dt:
            date = dt.split(' ')[0].replace(':', '-')
            date_groups[date] += 1
        else:
            date_groups['No Date'] += 1
            
    print("Photos by Date:")
    for date in sorted(date_groups.keys()):
        print(f"{date}: {date_groups[date]} photos")

if __name__ == "__main__":
    main()
