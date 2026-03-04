# Travel_Scrollyteller

An interactive storytelling tool that combines photo maps and scroll-based presentation (Scrollytelling).

## 🌟 Features
- **Interactive Photo Map**: Cluster photos by GPS location and annotate them in real-time.
- **Scrollytelling Report**: Generate a beautiful, interactive web presentation from your travel notes and photos.
- **Local Server Sync**: Real-time synchronization between the web interface and your Markdown notes.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.x
- Your travel photos in a folder

### 2. Configuration
Open `config.json` (to be implemented) or edit the paths in:
- `scripts/diary_server.py`
- `scripts/export_package.py`

### 3. Usage
- **Start the Sync Server**:
  ```bash
  python scripts/diary_server.py
  ```
- **Open the Map Interface**:
  Open `http://localhost:10001/output/photo_map_interactive.html` in your browser.

- **Export Presentation**:
  ```bash
  python scripts/export_package.py
  ```

## 📂 Directory Structure
- `data/`: JSON data for locations and selections.
- `notes/`: Markdown travel notes.
- `scripts/`: Backend server and automation scripts.
- `output/`: Web application files and exported packages.

## 📄 License
MIT
