#!/usr/bin/env python3
"""
Diagnose note and photo alignment issues
"""
import json
import re
import os
import sys

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_MD = os.path.join(BASE, "notes", "緬甸_行程筆記.md")
CLUSTERS_JSON = os.path.join(BASE, "data", "location_clusters.json")
LOCATIONS_JSON = os.path.join(BASE, "data", "manual_cluster_locations.json")

def parse_md_notes():
    """Parse MD notes, return {filename: [notes_list]}"""
    with open(NOTES_MD, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"##\s+(IMG_[A-Za-z0-9_]+\.(?:JPG|PNG|JPEG|MOV|MP4))\n(.*?)(?=\n##|\Z)"
    matches = re.finditer(pattern, content, re.DOTALL)

    result = {}
    for match in matches:
        filename = match.group(1).strip()
        body = match.group(2).strip()

        # Count notes
        note_matches = re.findall(r"-\s+\*\*心得\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
        if filename not in result:
            result[filename] = []
        result[filename].extend([n.strip()[:50] + "..." for n in note_matches if n.strip()])

    return result

def load_clusters():
    with open(CLUSTERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def load_locations():
    with open(LOCATIONS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def diagnose():
    print("=" * 60)
    print("[DIAGNOSE] Notes & Photo Alignment Report")
    print("=" * 60)

    md_notes = parse_md_notes()
    clusters = load_clusters()
    locations = load_locations()

    # 1. MD stats
    print(f"\n[MD NOTES STATS]")
    print(f"   - Photos with notes: {len(md_notes)}")
    total_notes = sum(len(v) for v in md_notes.values())
    print(f"   - Total note entries: {total_notes}")

    # 2. Multi-note files (potential misalignment)
    multi_note_files = {k: v for k, v in md_notes.items() if len(v) > 1}
    print(f"\n[WARNING] Photos with multiple notes (may be misplaced): {len(multi_note_files)}")
    for fname, notes in list(multi_note_files.items())[:5]:
        loc = locations.get(fname, "unnamed")
        print(f"   - {fname} ({loc}): {len(notes)} notes")
        for i, n in enumerate(notes[:2], 1):
            print(f"      {i}. {n}")

    # 3. Cluster sample_file without notes
    print(f"\n[CLUSTER ANALYSIS]")
    print(f"   - Total clusters: {len(clusters)}")

    missing_notes = []
    for c in clusters:
        sample = c.get("sample_file")
        if sample and sample not in md_notes:
            loc = locations.get(sample, "unnamed")
            missing_notes.append((sample, loc, c.get("count", 0)))

    print(f"   - Clusters with sample_file missing notes: {len(missing_notes)}")
    for fname, loc, count in missing_notes[:10]:
        print(f"      - {fname} ({loc}) - {count} photos")

    # 4. Orphan notes (not sample_file)
    sample_files = set(c.get("sample_file") for c in clusters)
    all_cluster_files = set()
    for c in clusters:
        all_cluster_files.update(c.get("all_files", []))

    orphan_notes = []
    for fname in md_notes:
        if fname not in sample_files:
            loc = locations.get(fname, "unnamed")
            in_cluster = fname in all_cluster_files
            orphan_notes.append((fname, loc, in_cluster))

    print(f"\n[ORPHAN NOTES] Photos with notes but not sample_file: {len(orphan_notes)}")
    for fname, loc, in_cluster in orphan_notes[:10]:
        status = "in cluster" if in_cluster else "NOT in any cluster"
        print(f"   - {fname} ({loc}) - {status}")

    # 5. Suggestions
    print("\n" + "=" * 60)
    print("[SUGGESTIONS]")
    print("=" * 60)

    if multi_note_files:
        print("\n1. Split multi-note photos:")
        for fname, notes in list(multi_note_files.items())[:3]:
            print(f"   - {fname} has {len(notes)} notes that should be separated")

    if missing_notes:
        print("\n2. Add notes for cluster sample_files:")
        for fname, loc, count in missing_notes[:5]:
            print(f"   - {fname} ({loc}) - represents {count} photos but has no note")

if __name__ == "__main__":
    diagnose()
