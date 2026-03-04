"""
自動命名腳本：根據 GPS 座標反向查詢地名，產出審查表供人工確認
使用 OpenStreetMap Nominatim API（免費，1 req/sec 限速）
"""

import json
import os
import time
import urllib.request
import urllib.parse

BASE_DIR = r"c:\Project\Alex_Diary"
CLUSTERS_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "data", "location_clusters.json")
MANUAL_LOCS_PATH = os.path.join(BASE_DIR, "projects", "Golden_Journey", "data", "manual_cluster_locations.json")
OUTPUT_REVIEW = os.path.join(BASE_DIR, "projects", "Golden_Journey", "notes", "地點命名審查表.md")
OUTPUT_JSON = os.path.join(BASE_DIR, "projects", "Golden_Journey", "data", "auto_name_suggestions.json")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def reverse_geocode(lat, lon):
    """用 Nominatim 反向地理編碼"""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=18&addressdetails=1&accept-language=zh-TW,en"
    headers = {"User-Agent": "AlexDiary/1.0 (personal architecture research)"}
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception as e:
        print(f"  ⚠️ Geocode failed for ({lat}, {lon}): {e}")
        return None

def extract_best_name(geo_data):
    """從 Nominatim 結果中提取最佳地名"""
    if not geo_data:
        return None, None
    
    addr = geo_data.get("address", {})
    display = geo_data.get("display_name", "")
    
    # 優先順序：具體建築 > 旅遊景點 > 道路 > 區域
    candidates = []
    
    # 1. 建築 / 景點名稱
    for key in ["tourism", "building", "amenity", "shop", "historic", "place_of_worship"]:
        if key in addr and addr[key]:
            candidates.append(("🏛️", addr[key]))
    
    # 2. 道路名
    if "road" in addr and addr["road"]:
        candidates.append(("🛣️", addr["road"]))
    
    # 3. 區域/鄰里
    for key in ["neighbourhood", "suburb", "quarter"]:
        if key in addr and addr[key]:
            candidates.append(("📍", addr[key]))
    
    # 4. 顯示名（取前兩段）
    if display:
        parts = display.split(", ")
        short_display = ", ".join(parts[:2])
        candidates.append(("🗺️", short_display))
    
    if candidates:
        return candidates[0][0], candidates[0][1]
    return None, None

def main():
    print("🔍 載入資料...")
    clusters = load_json(CLUSTERS_PATH)
    manual_locs = load_json(MANUAL_LOCS_PATH)
    
    if isinstance(clusters, dict):
        clusters = list(clusters.values())
    
    # 找出未命名的 cluster（排除已有名稱的）
    unnamed = []
    named_count = 0
    
    for c in clusters:
        sample = c.get("sample_file", "")
        existing_name = manual_locs.get(sample, "")
        has_name = existing_name and "位點" not in existing_name and "未命名" not in existing_name
        
        if has_name:
            named_count += 1
        else:
            # 只處理有 GPS 且照片數 >= 2 的 cluster
            if c.get("lat") and c.get("lon") and c.get("count", 0) >= 2:
                unnamed.append(c)
    
    print(f"📊 已命名: {named_count} | 待命名（≥2張照片）: {len(unnamed)} | 總計: {len(clusters)}")
    
    if not unnamed:
        print("✅ 所有 cluster 都已命名！")
        return
    
    # 反向地理編碼（帶限速）
    suggestions = {}
    
    # 先做座標去重（相近座標只查一次）
    coord_cache = {}
    
    print(f"\n🌐 開始反向地理編碼（{len(unnamed)} 個位置，預估 {len(unnamed)} 秒）...\n")
    
    for i, c in enumerate(unnamed):
        lat, lon = round(c["lat"], 4), round(c["lon"], 4)
        cache_key = f"{lat},{lon}"
        sample = c["sample_file"]
        count = c.get("count", 0)
        
        if cache_key in coord_cache:
            icon, name = coord_cache[cache_key]
            print(f"  [{i+1}/{len(unnamed)}] (cached) {sample} ({count}張) → {icon} {name}")
        else:
            geo = reverse_geocode(lat, lon)
            icon, name = extract_best_name(geo)
            coord_cache[cache_key] = (icon, name)
            
            if name:
                print(f"  [{i+1}/{len(unnamed)}] {sample} ({count}張) → {icon} {name}")
            else:
                print(f"  [{i+1}/{len(unnamed)}] {sample} ({count}張) → ❓ 查無結果")
            
            time.sleep(1.1)  # 尊重 Nominatim 限速
        
        if name:
            suggestions[sample] = {
                "suggested_name": name,
                "source_icon": icon,
                "lat": c["lat"],
                "lon": c["lon"],
                "count": count,
                "start_time": c.get("start_time", ""),
            }
    
    # 儲存 JSON 建議
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(suggestions, f, ensure_ascii=False, indent=2)
    
    # 產出 Markdown 審查表
    md = []
    md.append("# 🗺️ 地點自動命名審查表")
    md.append(f"> 自動產生於 {time.strftime('%Y-%m-%d %H:%M')}")
    md.append(f"> 共 {len(suggestions)} 個建議，請逐一確認後執行 `apply_names.py`")
    md.append("")
    md.append("## 使用方式")
    md.append("1. 看下表，覺得名字OK的就不用動")
    md.append("2. 覺得不對的，直接在「✏️ 修正名稱」欄位寫上你要的名字")
    md.append("3. 完全不想要的，在該行前面加 `~~` 刪除線")
    md.append("4. 確認完畢後告訴我，我會幫你批次寫入")
    md.append("")
    md.append("| # | 照片數 | 代表圖檔 | 座標 | 🤖 建議名稱 | ✏️ 修正名稱 |")
    md.append("| :---: | :---: | :--- | :--- | :--- | :--- |")
    
    for i, (sample, info) in enumerate(sorted(suggestions.items(), key=lambda x: -x[1]["count"]), 1):
        coord = f"[{info['lat']:.3f}, {info['lon']:.3f}](https://www.google.com/maps?q={info['lat']},{info['lon']})"
        md.append(f"| {i} | {info['count']} | `{sample}` | {coord} | {info['source_icon']} {info['suggested_name']} | |")
    
    with open(OUTPUT_REVIEW, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    
    print(f"\n✅ 完成！")
    print(f"   📄 審查表: {OUTPUT_REVIEW}")
    print(f"   📦 建議 JSON: {OUTPUT_JSON}")
    print(f"\n👉 請打開審查表確認名稱，確認後告訴我，我會幫你批次寫入。")

if __name__ == "__main__":
    main()
