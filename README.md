# KTV GUI 專案

這是一個使用 Python 和 PySide6 開發的 KTV 點歌系統圖形介面應用程式。

## 功能

*   搜尋網易雲音樂和 YouTube 上的歌曲
*   播放歌曲和 MV
*   顯示歌詞
*   管理播放列表（點歌、插歌、刪除）
*   管理我的最愛歌單

## 安裝

1.  **克隆儲存庫** (如果您尚未這樣做):
    ```bash
    git clone <repository-url>
    cd KTV_GUI
    ```

2.  **建立虛擬環境** (建議):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **安裝依賴項**:
    ```bash
    pip install -r requirements.txt
    ```

## 執行

```bash
python main.py
```

## 注意事項

*   本專案包含從網易雲音樂和 YouTube 下載的快取檔案，這些檔案已透過 `.gitignore` 排除在版本控制之外。
*   執行檔 (`getncm.exe`, `getyt.exe`, `player.exe`) 和 DLL 檔案 (`Aero/aeroDll.dll`) 也被排除在外。如果您需要重新建置這些檔案，可能需要查看相關的建置腳本或原始碼 (如果有的話)。
