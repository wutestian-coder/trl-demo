#!/usr/bin/env python3
import os
import sys
import time
import traceback
import tempfile
import subprocess

import psutil
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SAVE_PATH  = os.path.join(tempfile.gettempdir(), "test.txt")
TEST_LINES = [
    "TRI AXI Inspection",
    "Serial Number : TRIAXI001",
    "Result : PASS",
]
SEP = "=" * 60


def get_notepad_memory_mb():
    for proc in psutil.process_iter(["name", "memory_info"]):
        try:
            if proc.info["name"].lower() == "notepad.exe":
                return proc.info["memory_info"].rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None


def find_edit_control(window):
    for cls in ("Edit", "RichEditD2DPT", "RICHEDIT50W"):
        try:
            ctrl = window.child_window(class_name=cls)
            if ctrl.exists(timeout=1):
                return ctrl
        except Exception:
            pass
    try:
        ctrl = window.child_window(control_type="Document")
        if ctrl.exists(timeout=1):
            return ctrl
    except Exception:
        pass
    return window


def find_notepad_window(extra_pattern=""):
    pattern = r".*Notepad.*|.*記事本.*|.*Untitled.*|.*無標題.*"
    if extra_pattern:
        pattern += f"|{extra_pattern}"
    for _ in range(6):
        try:
            candidates = Desktop(backend="uia").windows(title_re=pattern)
            visible = [w for w in candidates if w.is_visible()]
            if visible:
                return visible[0]
        except Exception:
            pass
        time.sleep(1)
    return None


def read_notepad_content(window):
    import tkinter as tk
    try:
        window.set_focus()
        time.sleep(0.3)
        send_keys("^a")
        time.sleep(0.2)
        send_keys("^c")
        time.sleep(0.4)
        root = tk.Tk()
        root.withdraw()
        content = root.clipboard_get()
        root.destroy()
        if content and content.strip():
            return content
    except Exception:
        pass
    try:
        ctrl = find_edit_control(window)
        val = ctrl.get_value()
        title = window.window_text()
        if val and val.strip() and val.strip() != title.strip():
            return val
    except Exception:
        pass
    return ""


def main():
    print(f"\n{SEP}")
    print("  記事本自動化測試")
    print(SEP)

    mem_before = mem_after = None
    test_passed = False
    content = ""
    win = win2 = None

    try:
        print("\n[步驟 1] 開啟記事本 …")
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"].lower() == "notepad.exe":
                    proc.kill()
            except Exception:
                pass
        time.sleep(0.5)

        session_dir = os.path.expandvars(
            r"%LocalAppData%\Packages\Microsoft.WindowsNotepad_8wekyb3d8bbwe\LocalState\TabState"
        )
        if os.path.isdir(session_dir):
            for fname in os.listdir(session_dir):
                try:
                    os.remove(os.path.join(session_dir, fname))
                except Exception:
                    pass

        subprocess.Popen(["notepad.exe"])
        time.sleep(2.0)

        win = find_notepad_window()
        if win is None:
            raise RuntimeError("找不到記事本視窗")
        win.set_focus()
        print("         完成。")

        print("[步驟 2] 讀取 notepad.exe 記憶體用量（操作前）…")
        mem_before = get_notepad_memory_mb()
        print(f"         {f'{mem_before:.2f} MB' if mem_before is not None else '無法取得'}")

        print("[步驟 3] 輸入測試內容 …")
        win.set_focus()
        find_edit_control(win).click_input()
        time.sleep(0.3)
        send_keys("^a", pause=0.05)
        send_keys("{DELETE}", pause=0.05)
        time.sleep(0.2)
        for i, line in enumerate(TEST_LINES):
            send_keys(line, with_spaces=True, pause=0.02)
            if i < len(TEST_LINES) - 1:
                send_keys("{ENTER}")
        time.sleep(0.5)
        for line in TEST_LINES:
            print(f"         > {line}")

        print(f"[步驟 4] 存檔 → {SAVE_PATH}")
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(TEST_LINES))
        print("         存檔完成。")

        print("[步驟 6] 關閉記事本 …")
        try:
            win.close()
        except Exception:
            send_keys("%{F4}")
        time.sleep(0.8)
        try:
            dlg = Desktop(backend="uia").window(title_re=r".*記事本.*|.*Notepad.*")
            if dlg.exists(timeout=2):
                for btn in ("不要儲存", "Don't Save", "Discard"):
                    try:
                        dlg.child_window(title=btn, control_type="Button").click()
                        break
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(0.5)

        print(f"         重新開啟 {os.path.basename(SAVE_PATH)} …")
        subprocess.Popen(["notepad.exe", SAVE_PATH])
        time.sleep(2.0)
        win2 = find_notepad_window(".*test.*")
        if win2 is None:
            raise RuntimeError("重新開啟後找不到記事本視窗")
        win2.set_focus()

        print("[步驟 7] 從畫面讀取內容 …")
        content = read_notepad_content(win2)
        if content:
            for line in content.splitlines():
                print(f"         │ {line}")
        else:
            print("         （無法讀取畫面文字）")

        print("[步驟 8] 驗證 'PASS' 是否存在 …")
        test_passed = "PASS" in content
        print(f"         {'PASS 存在 ✓' if test_passed else 'PASS 不存在 ✗'}")

        print("[步驟 9] 讀取 notepad.exe 記憶體用量（操作後）…")
        mem_after = get_notepad_memory_mb()
        print(f"         {f'{mem_after:.2f} MB' if mem_after is not None else '無法取得'}")

    except Exception as exc:
        print(f"\n[錯誤] {exc}")
        traceback.print_exc()

    finally:
        for w in (win2, win):
            if w is not None:
                try:
                    w.close()
                except Exception:
                    pass
        time.sleep(0.5)

    mem_diff = (
        mem_after - mem_before
        if (mem_before is not None and mem_after is not None)
        else None
    )
    verdict = "PASS" if test_passed else "FAIL"

    print(f"\n{SEP}")
    print("  測試結果")
    print(SEP)
    print(f"  驗證結果         :  {verdict}")
    print(f"  記憶體（操作前） :  {f'{mem_before:.2f} MB' if mem_before is not None else 'N/A'}")
    print(f"  記憶體（操作後） :  {f'{mem_after:.2f} MB'  if mem_after  is not None else 'N/A'}")
    print(f"  記憶體增加量     :  {f'{mem_diff:+.2f} MB'  if mem_diff   is not None else 'N/A'}")
    print(SEP)
    print()

    return 0 if test_passed else 1


if __name__ == "__main__":
    sys.exit(main())
