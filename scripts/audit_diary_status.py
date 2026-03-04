
import json
import os
import re

# Paths
BASE_DIR = r"c:\Project\Alex_Diary"
CLUSTERS_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "data", "location_clusters.json")
MANUAL_LOCS_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "data", "manual_cluster_locations.json")
SELECTED_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "data", "selected_photos.json")
NOTES_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "notes", "緬甸_行程筆記.md")
OUTPUT_MD_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "notes", "行程整理大表.md")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def parse_notes(path):
    notes = {}
    if not os.path.exists(path):
        return notes
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex matches ## FILENAME blocks
    pattern = r"##\s+(IMG_[A-Za-z0-9_]+\.(?:JPG|PNG|JPEG|MOV|MP4))\n(.*?)(?=\n##|\Z)"
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        filename = match.group(1).strip()
        body = match.group(2).strip()
        
        # Extract Note Content
        note_match = re.search(r"-\s+\*\*心得\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
        refined_match = re.search(r"-\s+\*\*精修筆記\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
        
        note_text = ""
        if note_match: note_text += note_match.group(1).strip()
        if refined_match: note_text += refined_match.group(1).strip()

        notes[filename] = {
            "has_note": len(note_text) > 10, # Arbitrary threshold
            "length": len(note_text)
        }
    return notes

def main():
    print("Loading data...")
    clusters = load_json(CLUSTERS_PATH) # List of dicts
    manual_locs = load_json(MANUAL_LOCS_PATH) # Dict: filename -> location name
    selected_photos = load_json(SELECTED_PATH) # Dict: filename -> {selected: true}
    notes = parse_notes(NOTES_PATH) # Dict: filename -> {has_note, length}

    print(f"Loaded {len(clusters)} clusters.")

    # Process Data
    report_rows = []
    
    stats = {"ready": 0, "partial": 0, "chaos": 0}

    for c in clusters:
        sample = c.get("sample_file")
        files = c.get("all_files", [])
        
        # 1. Check Name
        loc_name = manual_locs.get(sample, "")
        if not loc_name:
            # Fallback: check if note has location field (not parsed above but usually synced)
            pass
        
        # 2. Check Selection
        selected_count = sum(1 for f in files if f in selected_photos and selected_photos[f].get("selected"))
        
        # 3. Check Note (Attached to Sample File)
        note_info = notes.get(sample, {"has_note": False, "length": 0})
        
        # Determine Status
        status = "🔴 Chaos"
        status_score = 0
        
        has_name = len(loc_name) > 1 and "位點" not in loc_name and "未命名" not in loc_name
        has_note = note_info["has_note"]
        has_selection = selected_count > 0
        
        if has_name: status_score += 1
        if has_note: status_score += 1
        if has_selection: status_score += 1
        
        if status_score == 3:
            status = "🟢 Ready"
            stats["ready"] += 1
        elif status_score > 0:
            status = "🟡 Partial"
            stats["partial"] += 1
        else:
            stats["chaos"] += 1

        report_rows.append({
            "status": status,
            "sample": sample,
            "name": loc_name if has_name else "(未命名)",
            "count": c.get("count", 0),
            "selected": selected_count,
            "note_len": note_info["length"]
        })

    # Sort: Chaos first, then Partial, then Ready (to help user work)
    # Actually user wants "Redone", so maybe sort by status priority
    # Let's sort by Status Group (Red -> Yellow -> Green)
    
    report_rows.sort(key=lambda x: (
        0 if "Chaos" in x["status"] else 1 if "Partial" in x["status"] else 2,
        -x["count"] # Then by size (bigger clusters first)
    ))

    # Generate Markdown
    md_lines = []
    md_lines.append("# 緬甸行程整理大表 (Status Audit)")
    md_lines.append(f"> 統計: 🟢 完成: **{stats['ready']}** | 🟡 進行中: **{stats['partial']}** | 🔴 待處理: **{stats['chaos']}**")
    md_lines.append("")
    md_lines.append("這份表格是系統自動生成的，用來幫助你釐清目前混亂的狀態。請依照這個順序處理：")
    md_lines.append("1. **🔴 Chaos (優先處理)**: 這些是大群的照片，但完全沒有名字，也沒有筆記。請先去地圖上幫它們「命名」。")
    md_lines.append("2. **🟡 Partial**: 這些已經有名字了，但可能還沒選精選照片，或是還沒寫心得。")
    md_lines.append("3. **🟢 Ready**: 這些已經準備好可以產出簡報了。")
    md_lines.append("")
    md_lines.append("| 狀態 | 地點名稱 (Cluster Name) | 照片數 | 精選數 | 筆記字數 | 代表圖檔 (Sample) |")
    md_lines.append("| :--- | :--- | :---: | :---: | :---: | :--- |")

    for row in report_rows:
        md_lines.append(f"| {row['status']} | {row['name']} | {row['count']} | {row['selected']} | {row['note_len']} | `{row['sample']}` |")

    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Report generated at {OUTPUT_MD_PATH}")

if __name__ == "__main__":
    main()
