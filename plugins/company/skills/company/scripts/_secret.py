"""
bootcamp-company の連携道具が使う「パスワードのしまい方」。

- Mac:     キーチェーン（パソコンの鍵の保管庫）
- Windows: Windows のデータ保護機能（DPAPI）で暗号化して設定ファイルに入れる。
           そのパソコンの、その人のアカウントでしか元に戻せない。ファイルを開いても読めない
- その他:  設定ファイルにそのまま（本人しか読めない権限にする）

秘書（Claude）が設定ファイルを開いても、Mac・Windows ではパスワードが見えないようにするのが目的。
"""
import base64
import platform
import subprocess

SYSTEM = platform.system()


# ---------------------------------------------------------------------------
# Windows DPAPI（標準ライブラリの ctypes だけで呼ぶ）
# ---------------------------------------------------------------------------

def _dpapi(data, protect):
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    fn = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    CRYPTPROTECT_UI_FORBIDDEN = 0x01
    if not fn(ctypes.byref(blob_in), None, None, None, None, CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out)):
        raise OSError("Windows のデータ保護（DPAPI）に失敗しました")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


# ---------------------------------------------------------------------------
# 保存と取り出し
# ---------------------------------------------------------------------------

def save(service, account, secret, cfg):
    """secret をしまい、cfg に「どこにしまったか」を書き込む（cfg は呼び出し側が保存する）。"""
    for key in ("password", "password_dpapi"):
        cfg.pop(key, None)
    if SYSTEM == "Darwin":
        subprocess.run(["security", "delete-generic-password", "-s", service, "-a", account], capture_output=True)
        subprocess.run(["security", "add-generic-password", "-s", service, "-a", account, "-w", secret],
                       check=True, capture_output=True)
        cfg["password_store"] = "keychain"
        return
    if SYSTEM == "Windows":
        try:
            cfg["password_dpapi"] = base64.b64encode(_dpapi(secret.encode("utf-8"), True)).decode()
            cfg["password_store"] = "dpapi"
            return
        except Exception:
            pass  # DPAPI が使えない特殊な環境だけ、下のファイル保存に落とす
    cfg["password_store"] = "file"
    cfg["password"] = secret


def load(service, account, cfg):
    """しまったパスワードを取り出す。見つからなければ None。"""
    store = cfg.get("password_store")
    if store == "keychain":
        r = subprocess.run(["security", "find-generic-password", "-s", service, "-a", account, "-w"],
                           capture_output=True, text=True)
        return r.stdout.rstrip("\n") if r.returncode == 0 else None
    if store == "dpapi":
        try:
            return _dpapi(base64.b64decode(cfg["password_dpapi"]), False).decode("utf-8")
        except Exception:
            return None
    return cfg.get("password")
