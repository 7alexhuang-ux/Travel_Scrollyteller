#!/usr/bin/env python3
"""
清理 MD 筆記中的重複空條目
保留每個照片的第一個有內容的筆記
"""
import re
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_MD = os.path.join(BASE, "notes", "緬甸_行程筆記.md")
BACKUP_MD = os.path.join(BASE, "notes", "緬甸_行程筆記_backup.md")

def has_real_content(body):
    """檢查筆記是否有實際內容"""
    # 提取心得
    note_match = re.search(r'-\s+\*\*心得\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)', body, re.DOTALL)
    if note_match:
        note = note_match.group(1).strip()
        if note and note != "None" and len(note) > 5:
            return True

    # 提取精修筆記
    refined_match = re.search(r'-\s+\*\*精修筆記\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)', body, re.DOTALL)
    if refined_match:
        refined = refined_match.group(1).strip()
        if refined and "現場細節整理中" not in refined:
            return True

    return False

def cleanup():
    print("=" * 60)
    print("[CLEANUP] Removing duplicate empty notes")
    print("=" * 60)

    with open(NOTES_MD, "r", encoding="utf-8") as f:
        content = f.read()

    # Backup
    with open(BACKUP_MD, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Backup saved to: {BACKUP_MD}")

    # Find all note blocks
    pattern = r"(##\s+(IMG_[A-Za-z0-9_]+\.(?:JPG|PNG|JPEG|MOV|MP4))\n(.*?))(?=\n##|\Z)"
    matches = list(re.finditer(pattern, content, re.DOTALL))

    print(f"\nTotal note blocks found: {len(matches)}")

    # Group by filename
    notes_by_file = {}
    for m in matches:
        full_block = m.group(1)
        filename = m.group(2).strip()
        body = m.group(3).strip()

        if filename not in notes_by_file:
            notes_by_file[filename] = []
        notes_by_file[filename].append({
            "block": full_block,
            "body": body,
            "has_content": has_real_content(body),
            "start": m.start(),
            "end": m.end()
        })

    # Find duplicates
    duplicates = {k: v for k, v in notes_by_file.items() if len(v) > 1}
    print(f"Files with duplicates: {len(duplicates)}")

    # Blocks to remove (keep the first one with content, or the first one if none have content)
    blocks_to_remove = []
    for filename, entries in duplicates.items():
        # Sort by position
        entries.sort(key=lambda x: x["start"])

        # Find first entry with content
        first_with_content = None
        for e in entries:
            if e["has_content"]:
                first_with_content = e
                break

        # Mark others for removal
        keep = first_with_content or entries[0]
        for e in entries:
            if e is not keep:
                blocks_to_remove.append(e)

        if len(entries) > 1:
            print(f"  {filename}: keeping 1, removing {len(entries)-1}")

    print(f"\nBlocks to remove: {len(blocks_to_remove)}")

    if blocks_to_remove:
        # Sort by position (descending) to remove from end first
        blocks_to_remove.sort(key=lambda x: x["start"], reverse=True)

        # Remove blocks
        for b in blocks_to_remove:
            content = content[:b["start"]] + content[b["end"]:]

        # Clean up extra newlines
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Write cleaned content
        with open(NOTES_MD, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\nCleaned! Removed {len(blocks_to_remove)} duplicate blocks.")
    else:
        print("\nNo duplicates to remove.")

if __name__ == "__main__":
    cleanup()
