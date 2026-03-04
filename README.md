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
- **啟動同步伺服器**：
  ```bash
  python scripts/diary_server.py
  ```
- **開啟地圖介面**：
  在瀏覽器中開啟 `http://localhost:10001/output/photo_map_interactive.html`。

- **匯出呈現包**：
  ```bash
  python scripts/export_package.py
  ```

## 📂 目錄結構
- `data/`：存放地點、分類與照片選取等 JSON 數據。
- `notes/`：存放 Markdown 格式的旅行筆記。
- `scripts/`：後端伺服器與自動化處理腳本。
- `output/`：生成的網頁檔案與匯出的封裝包（已由 .gitignore 忽略上傳）。

## 📄 授權條款
MIT License

