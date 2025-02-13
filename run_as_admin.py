import os
import sys
import ctypes
import subprocess

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Yönetici olarak yeniden başlat
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(['"' + sys.argv[0].replace('"', '\\"') + '"'] + sys.argv[1:]), None, 1)
else:
    # cursor_manager.py'yi çalıştır
    subprocess.run([sys.executable, "cursor_manager.py"] + sys.argv[1:]) 