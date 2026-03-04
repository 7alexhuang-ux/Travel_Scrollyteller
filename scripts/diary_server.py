
import http.server
import socketserver
import json
import os
import re
from datetime import datetime

PORT = 10001
DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS_DIR = os.path.join(DIRECTORY, "inbox_photos")
SAVED_NOTES_PATH = os.path.join(DIRECTORY, "notes", "journey_notes.md")

# Data Paths
CLUSTER_LOCATIONS_PATH = os.path.join(DIRECTORY, "data", "manual_cluster_locations.json")
SELECTED_PHOTOS_PATH = os.path.join(DIRECTORY, "data", "selected_photos.json")
CLUSTER_META_PATH = os.path.join(DIRECTORY, "data", "cluster_meta.json")

class DiaryHandler(http.server.SimpleHTTPRequestHandler):
    def get_existing_notes(self):
        """解析 Markdown 筆記檔，返回格式化的 notes, cluster_locations, starred_photos 和 sub_locations"""
        result = {
            "notes": {},
            "cluster_locations": {},
            "starred_photos": [],
            "sub_locations": {}  # {filename: sublocation}
        }

        # 1. 讀取地點對照表
        if os.path.exists(CLUSTER_LOCATIONS_PATH):
            with open(CLUSTER_LOCATIONS_PATH, "r", encoding="utf-8") as f:
                result["cluster_locations"] = json.load(f)

        # 1.5 讀取星號選片
        if os.path.exists(SELECTED_PHOTOS_PATH):
            with open(SELECTED_PHOTOS_PATH, "r", encoding="utf-8") as f:
                selections = json.load(f)
                result["starred_photos"] = [k for k, v in selections.items() if v.get("selected")]

        # 1.6 讀取子地點資料
        if os.path.exists(CLUSTER_META_PATH):
            with open(CLUSTER_META_PATH, "r", encoding="utf-8") as f:
                cluster_meta = json.load(f)
                for cluster_id, meta in cluster_meta.items():
                    sub_tags = meta.get("sub_tags", {})
                    for filename, subtag in sub_tags.items():
                        if subtag:
                            result["sub_locations"][filename] = subtag
        
        # 2. 解析筆記 Markdown
        if not os.path.exists(SAVED_NOTES_PATH):
            return result
        
        with open(SAVED_NOTES_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Regex to find ## IMG_xxxx.JPG blocks
        pattern = r"##\s+(IMG_[A-Za-z0-9_]+\.(?:JPG|PNG|JPEG|MOV|MP4))\n(.*?)(?=\n##|\Z)"
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            filename = match.group(1).strip()
            body = match.group(2).strip()

            note_obj = {}

            # 🔧 FIX: 提取所有心得欄位（可能有多條）並合併
            note_matches = re.findall(r"-\s+\*\*心得\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
            if note_matches:
                # 合併所有心得，用分隔線區分
                combined_notes = []
                for i, n in enumerate(note_matches):
                    cleaned = n.strip()
                    if cleaned:
                        combined_notes.append(cleaned)
                note_obj["note"] = "\n\n---\n\n".join(combined_notes) if len(combined_notes) > 1 else (combined_notes[0] if combined_notes else "")

            # 🔧 FIX: 精修筆記也可能有多條
            refined_matches = re.findall(r"-\s+\*\*精修筆記\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
            if refined_matches:
                combined_refined = [r.strip() for r in refined_matches if r.strip()]
                note_obj["refined_note"] = "\n\n---\n\n".join(combined_refined) if len(combined_refined) > 1 else (combined_refined[0] if combined_refined else "")

            # 🔧 FIX: Tips 也可能有多條
            tips_matches = re.findall(r"-\s+\*\*Tips\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
            if tips_matches:
                combined_tips = [t.strip() for t in tips_matches if t.strip()]
                note_obj["tips"] = "\n\n---\n\n".join(combined_tips) if len(combined_tips) > 1 else (combined_tips[0] if combined_tips else "")

            location_match = re.search(r"-\s+\*\*地點\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
            if location_match:
                loc_name = location_match.group(1).strip()
                note_obj["location"] = loc_name
                # 同時更新 cluster_locations（Markdown 中的地點優先）
                if loc_name:
                    result["cluster_locations"][filename] = loc_name

            subtitle_match = re.search(r"-\s+\*\*副標題\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
            if subtitle_match:
                note_obj["subtitle"] = subtitle_match.group(1).strip()

            category_match = re.search(r"-\s+\*\*類型\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
            if category_match:
                note_obj["category"] = category_match.group(1).strip()

            if note_obj:
                # 🔧 FIX: 如果 filename 已存在，合併筆記而非覆蓋
                # 優先保留有實際內容的筆記
                if filename in result["notes"]:
                    existing = result["notes"][filename]
                    # 只有當新筆記有實際內容時才更新
                    for key in ["note", "refined_note", "tips", "subtitle", "category", "location"]:
                        new_val = note_obj.get(key, "")
                        old_val = existing.get(key, "")
                        # 如果新值有內容且不是 "None"，更新
                        if new_val and new_val != "None" and new_val != "現場細節整理中...":
                            if not old_val or old_val == "None" or old_val == "現場細節整理中...":
                                existing[key] = new_val
                            elif new_val not in old_val:  # 避免重複
                                existing[key] = old_val + "\n\n---\n\n" + new_val
                else:
                    # 過濾掉 "None" 筆記
                    if note_obj.get("note") != "None":
                        result["notes"][filename] = note_obj

        return result

    def update_note_entry(self, filename, updates):
        """
        更新或新增筆記條目（upsert 模式）
        - 若 filename 已存在：只更新提供的欄位，保留其他欄位
        - 若 filename 不存在：新增完整條目
        """
        # 讀取現有內容
        if os.path.exists(SAVED_NOTES_PATH):
            with open(SAVED_NOTES_PATH, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = ""

        # 尋找該 filename 的區塊
        pattern = rf"(## {re.escape(filename)}\n)(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            # 更新現有條目
            body = match.group(2)

            # 解析現有欄位
            fields = {}
            for field_name, field_key in [
                ("日期", "time"), ("心得", "note"), ("精修筆記", "refined_note"),
                ("Tips", "tips"), ("副標題", "subtitle"), ("類型", "category"), ("記錄時間", "recorded_at")
            ]:
                field_match = re.search(rf"-\s+\*\*{field_name}\*\*:\s*(.*?)(?=\n-\s+\*\*|\Z)", body, re.DOTALL)
                if field_match:
                    fields[field_key] = field_match.group(1).strip()

            # 合併更新
            for key, value in updates.items():
                if value is not None:
                    fields[key] = value

            # 更新記錄時間
            fields["recorded_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 重建條目
            new_body = self._build_note_body(fields)
            new_block = f"## {filename}\n{new_body}\n"

            # 替換原內容
            content = content[:match.start()] + new_block + content[match.end():]
        else:
            # 新增條目
            updates["recorded_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_body = self._build_note_body(updates)
            new_block = f"## {filename}\n{new_body}\n"
            content = content + new_block

        # 寫回檔案
        with open(SAVED_NOTES_PATH, "w", encoding="utf-8") as f:
            f.write(content)

    def _build_note_body(self, fields):
        """根據欄位字典建構 Markdown 格式的筆記內容"""
        lines = []
        field_order = [
            ("time", "日期"), ("note", "心得"), ("refined_note", "精修筆記"),
            ("tips", "Tips"), ("subtitle", "副標題"), ("category", "類型"), ("recorded_at", "記錄時間")
        ]
        for key, label in field_order:
            if key in fields and fields[key]:
                lines.append(f"- **{label}**: {fields[key]}")
        return "\n".join(lines)

    def get_selected_photos(self):
        """讀取選片資料"""
        if os.path.exists(SELECTED_PHOTOS_PATH):
            with open(SELECTED_PHOTOS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_selected_photos(self, data):
        """儲存選片資料"""
        with open(SELECTED_PHOTOS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_cluster_meta(self):
        """讀取 cluster 層級的地點資訊 (含子標籤)"""
        if os.path.exists(CLUSTER_META_PATH):
            with open(CLUSTER_META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_cluster_meta(self, data):
        """儲存 cluster 層級的地點資訊"""
        with open(CLUSTER_META_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def sync_photo_locations(self, location_name, cluster_files):
        """同步更新 manual_cluster_locations.json 中的個別照片地點"""
        if os.path.exists(CLUSTER_LOCATIONS_PATH):
            with open(CLUSTER_LOCATIONS_PATH, "r", encoding="utf-8") as f:
                photo_locations = json.load(f)
        else:
            photo_locations = {}

        for filename in cluster_files:
            photo_locations[filename] = location_name

        with open(CLUSTER_LOCATIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(photo_locations, f, ensure_ascii=False, indent=2)

    def do_POST(self):
        if self.path == '/save_note':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            filename = data.get('filename')
            if not filename:
                self.send_response(400)
                self.end_headers()
                return

            # 收集要更新的欄位（只傳送有值的欄位）
            updates = {}
            if 'time' in data and data['time']:
                updates['time'] = data['time']
            if 'note' in data and data['note']:
                updates['note'] = data['note']
            if 'refined_note' in data and data['refined_note']:
                updates['refined_note'] = data['refined_note']
            if 'tips' in data and data['tips']:
                updates['tips'] = data['tips']
            if 'subtitle' in data:
                updates['subtitle'] = data['subtitle'] if data['subtitle'] else None
            if 'category' in data:
                updates['category'] = data['category'] if data['category'] else None

            # 使用 upsert 邏輯更新筆記
            self.update_note_entry(filename, updates)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        elif self.path == '/toggle_selection':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            filename = data.get('filename')
            selected = data.get('selected', True)
            category = data.get('category', '')

            selections = self.get_selected_photos()

            if selected:
                selections[filename] = {
                    "selected": True,
                    "category": category,
                    "updated_at": datetime.now().isoformat()
                }
            else:
                if filename in selections:
                    del selections[filename]

            self.save_selected_photos(selections)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "selections": selections}).encode())

        elif self.path == '/update_category':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            filename = data.get('filename')
            category = data.get('category', '')

            selections = self.get_selected_photos()

            if filename in selections:
                selections[filename]["category"] = category
                selections[filename]["updated_at"] = datetime.now().isoformat()
                self.save_selected_photos(selections)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        elif self.path == '/save_cluster_location':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            cluster_id = data.get('cluster_id')
            location = data.get('location', '')
            point_type = data.get('point_type', 'major') # 'major' or 'minor'
            cluster_files = data.get('files', [])

            cluster_meta = self.get_cluster_meta()

            if cluster_id not in cluster_meta:
                cluster_meta[cluster_id] = {"location": "", "sub_tags": {}}

            cluster_meta[cluster_id]["location"] = location
            cluster_meta[cluster_id]["point_type"] = point_type
            cluster_meta[cluster_id]["updated_at"] = datetime.now().isoformat()
            self.save_cluster_meta(cluster_meta)

            if location and cluster_files:
                self.sync_photo_locations(location, cluster_files)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "cluster_meta": cluster_meta}).encode())

        elif self.path == '/save_photo_subtag':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            cluster_id = data.get('cluster_id')
            filename = data.get('filename')
            subtag = data.get('subtag', '')

            cluster_meta = self.get_cluster_meta()

            if cluster_id not in cluster_meta:
                cluster_meta[cluster_id] = {"location": "", "sub_tags": {}}

            if subtag:
                cluster_meta[cluster_id]["sub_tags"][filename] = subtag
            elif filename in cluster_meta[cluster_id].get("sub_tags", {}):
                del cluster_meta[cluster_id]["sub_tags"][filename]

            self.save_cluster_meta(cluster_meta)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        elif self.path == '/save_photo_order':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            cluster_id = data.get('cluster_id')
            photo_order = data.get('order', [])

            if not cluster_id:
                self.send_response(400)
                self.end_headers()
                return

            cluster_meta = self.get_cluster_meta()
            if cluster_id not in cluster_meta:
                cluster_meta[cluster_id] = {"location": "", "sub_tags": {}, "photo_order": []}

            cluster_meta[cluster_id]["photo_order"] = photo_order
            cluster_meta[cluster_id]["updated_at"] = datetime.now().isoformat()
            self.save_cluster_meta(cluster_meta)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())

        else:
            super().do_POST()

    def do_GET(self):
        if self.path == '/get_notes':
            notes = self.get_existing_notes()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(notes).encode())
            return

        if self.path == '/get_selections':
            selections = self.get_selected_photos()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(selections).encode())
            return

        if self.path == '/get_cluster_locations':
            cluster_meta = self.get_cluster_meta()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(cluster_meta).encode())
            return

        if self.path.startswith('/photo/'):
            filename = self.path.split('/')[-1]
            img_path = os.path.join(PHOTOS_DIR, filename)
            if os.path.exists(img_path):
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                with open(img_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
        
        super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-type')
        self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DiaryHandler) as httpd:
        print(f"Server started at http://localhost:{PORT}/projects/Golden_Journey/output/photo_map_interactive.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
