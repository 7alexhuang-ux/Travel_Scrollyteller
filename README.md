# Travel_Scrollyteller

一個結合照片地圖與滾動式敘事（Scrollytelling）的互動式旅行記錄工具。

## 🌟 核心功能
- **互動式照片地圖**：根據 GPS 座標自動串聯照片，並支援即時標註與分類。
- **滾動式敘事報告**：將旅行筆記與照片轉化為精美、流暢的網頁式簡報。
- **本地伺服器同步**：網頁介面與 Markdown 筆記（`notes/`）之間的實時資料同步。

## 🚀 快速上手

### 1. 準備工作
- 安裝 Python 3.x
- 將您的旅行照片放入指定資料夾

### 2. 配置設定
雖然專案正朝向 `config.json` 自動化配置發展，目前您可以直接在以下腳本中修改路徑：
- `scripts/diary_server.py`
- `scripts/export_package.py`

### 3. 使用方法

#### 🗺️ 互動式照片地圖 (Interactive Photo Map)
此介面用於瀏覽照片分佈、標註地點資訊與撰寫心得。
1. **啟動伺服器**：
   ```bash
   python scripts/diary_server.py
   ```
2. **開啟網頁**：在瀏覽器輸入 `http://localhost:10001/output/photo_map_interactive.html`。
3. **操作指南**：
   - **地圖瀏覽**：左側地圖會顯示照片群集（Clusters）。點擊群集可展開查看該區域的照片。
   - **撰寫筆記**：點擊照片後，右側面板會顯示詳細資訊。您可以直接在欄位中輸入「心得」、「精修筆記」或「Tips」。
   - **地點標註**：您可以為特定的照片或群集命名地點。
   - **自動儲存**：在介面上的所有修改都會即時同步回本地的 `notes/journey_notes.md` 與 `data/` 資料夾，無需手動存檔。
   - **精選照片**：點擊星號（Star）標記該照片為「精選」，這將影響最後網頁簡報的呈現內容。

#### 📄 滾動式網頁簡報 (Scrollytelling Export)
當您完成筆記與照片篩選後，可以生成一個獨立的網頁呈現包。
1. **執行匯出腳本**：
   ```bash
   python scripts/export_package.py
   ```
2. **生成的結果**：
   - 腳本會讀取 `data/` 中的配置與 `notes/` 中的內容。
   - 在 `output/` 目錄下會生成一個名為 `Golden_Journey_Presentation_YYYYMMDD` 的資料夾。
   - 該資料夾包含所有必要的靜態資源（HTML, CSS, JS）以及經過壓縮的照片。
3. **查看簡報**：開啟資料夾內的 `index.html`，即可體驗滾動式的旅行敘事呈現。這個資料夾可以獨立移動或部署到任何網頁伺服器。


## 📂 目錄結構
- `data/`：存放地點、分類與照片選取等 JSON 數據。
- `notes/`：存放 Markdown 格式的旅行筆記。
- `scripts/`：後端伺服器與自動化處理腳本。
- `output/`：生成的網頁檔案與匯出的封裝包（已由 .gitignore 忽略上傳）。

## 📄 授權條款
MIT License

