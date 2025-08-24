# ahk_rpc.py
import ctypes
import ctypes.wintypes as w
import json, os, time, uuid, tempfile

WM_COPYDATA = 0x004A

class COPYDATASTRUCT(ctypes.Structure):
    _fields_ = [
        ("dwData", w.LPARAM),
        ("cbData", w.DWORD),
        ("lpData", w.LPVOID),
    ]

SendMessageW = ctypes.windll.user32.SendMessageW
FindWindowW  = ctypes.windll.user32.FindWindowW

def _find_ahk_window(title: str | None = None) -> int:
    if title:
        hwnd = FindWindowW(None, title)
        if hwnd:
            return hwnd
    hwnd = FindWindowW("AutoHotkey", None)
    if not hwnd:
        raise RuntimeError("AHK window not found")
    return hwnd

def call(func: str, *args, title: str | None = None, timeout: float = 3.0):
    hwnd = _find_ahk_window(title)

    reply = os.path.join(tempfile.gettempdir(), f"ahk_rpc_{uuid.uuid4().hex}.json")
    payload = {"type": "call", "func": func, "args": list(args), "reply_file": reply}
    s = json.dumps(payload, ensure_ascii=False)

    buf = ctypes.create_unicode_buffer(s)
    cds = COPYDATASTRUCT()
    cds.dwData = 0
    cds.cbData = len(s) * 2
    cds.lpData = ctypes.cast(buf, w.LPVOID)

    SendMessageW(hwnd, WM_COPYDATA, 0, ctypes.byref(cds))

    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(reply):
            with open(reply, "r", encoding="utf-8") as f:
                resp = json.load(f)
            try: os.remove(reply)
            except OSError: pass
            if resp.get("ok"):
                return resp.get("result")
            raise RuntimeError(resp.get("error") or "AHK error")
        time.sleep(0.01)
    raise TimeoutError("No reply from AHK within timeout")
