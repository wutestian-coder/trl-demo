# trl-demo

自動化記事本（Notepad）測試腳本集合。

## 檔案說明

### `test_notepad.py`

以 Python 自動化方式測試 Windows 記事本（Notepad）的基本操作，涵蓋：

- 開啟記事本並清除舊有工作階段
- 輸入測試文字（多行）
- 儲存檔案至暫存資料夾
- 重新開啟已儲存的檔案
- 從畫面讀回內容並驗證關鍵字 `PASS`
- 量測操作前後記憶體用量差異
- 關閉記事本並輸出測試結果

## 環境需求

| 項目 | 說明 |
|------|------|
| 作業系統 | Windows 10 / 11（需有 `notepad.exe`） |
| Python | 3.8 以上 |
| 依賴套件 | `psutil`、`pywinauto` |

安裝依賴：

```bash
pip install psutil pywinauto
```

## 使用方式

```bash
python test_notepad.py
```

執行後會依序列印各步驟進度，最終輸出測試結果摘要，例如：

```
============================================================
  測試結果
============================================================
  驗證結果         :  PASS
  記憶體（操作前） :  12.34 MB
  記憶體（操作後） :  13.56 MB
  記憶體增加量     :  +1.22 MB
============================================================
```

程式結束碼：`0` 代表測試通過，`1` 代表測試失敗。

## 測試流程

1. 終止所有現有 `notepad.exe` 程序並清除工作階段快取
2. 啟動新的記事本視窗
3. 讀取記憶體用量（操作前）
4. 輸入以下測試內容：
   - `TRI AXI Inspection`
   - `Serial Number : TRIAXI001`
   - `Result : PASS`
5. 將內容寫入 `%TEMP%\test.txt`
6. 關閉記事本（放棄存檔對話框選擇「不儲存」）
7. 以記事本重新開啟 `test.txt`
8. 從畫面讀取內容，驗證是否包含 `PASS`
9. 讀取記憶體用量（操作後）並計算差值

## 注意事項

- 腳本需在**有圖形介面的 Windows 桌面環境**下執行，不支援 headless 模式。
- `pywinauto` 使用 UIA（UI Automation）後端，請確認記事本視窗可正常取得焦點。
- 若使用 Windows Store 版記事本，腳本會自動清除
  `%LocalAppData%\Packages\Microsoft.WindowsNotepad_8wekyb3d8bbwe\LocalState\TabState`
  下的工作階段檔案，以避免舊分頁干擾測試。
