"""ElectronStore online installer for Windows.

Builds into ElectronStoreSetup.exe (see electronstore-setup.spec). When the
shop runs that one file it:

1. downloads the latest ElectronStore.exe from a configured URL,
2. installs it under %LOCALAPPDATA%\\Programs\\ElectronStore,
3. adds Start Menu and desktop shortcuts,
4. registers an uninstall entry in Windows Settings, and
5. offers to launch the app.

The app stores its data in %LOCALAPPDATA%\\ElectronStore (see paths.py), so
updating or uninstalling never touches sales records.

The download URL defaults to the GitHub latest-release asset. Override at
runtime with the ELECTRONSTORE_DOWNLOAD_URL environment variable or --url.
"""

import argparse
import os
import subprocess
import urllib.request
from pathlib import Path

PRODUCT_NAME = "ElectronStore POS"
DEFAULT_URL = (
    "https://github.com/IrunguPeter/electronics-store"
    "/releases/latest/download/ElectronStore.exe"
)


def is_windows():
    return os.name == "nt"


def install_dir():
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "Programs" / "ElectronStore"


def start_menu_dir():
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def download(url, dest, report=None):
    """Stream url to dest and sanity-check it is a Windows PE executable."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(
        url, headers={"User-Agent": f"{PRODUCT_NAME} installer"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total and total.isdigit() else None
        done = 0
        with open(tmp, "wb") as fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fh.write(chunk)
                done += len(chunk)
                if report is not None:
                    report(done, total)
    with open(tmp, "rb") as fh:
        if fh.read(2) != b"MZ":
            tmp.unlink(missing_ok=True)
            raise RuntimeError("Downloaded file is not a valid Windows program")
    tmp.replace(dest)
    return dest


def _ps_str(value):
    return "'" + str(value).replace("'", "''") + "'"


def _run_powershell(script):
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-Command", "-"],
        input=script, text=True, capture_output=True)


def create_shortcut(lnk, target, args="", icon=""):
    script = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut("
        + _ps_str(lnk) + "); "
        "$s.TargetPath = " + _ps_str(target) + "; "
    )
    if args:
        script += "$s.Arguments = " + _ps_str(args) + "; "
    if icon:
        script += "$s.IconLocation = " + _ps_str(f"{icon},0") + "; "
    script += "$s.Save()"
    _run_powershell(script)


def add_start_menu_shortcut(exe):
    folder = start_menu_dir() / "ElectronStore"
    folder.mkdir(parents=True, exist_ok=True)
    create_shortcut(folder / "ElectronStore.lnk", exe, icon=exe)


def add_desktop_shortcut(exe):
    desktop = Path(os.environ.get("USERPROFILE") or str(Path.home())) / "Desktop"
    if desktop.exists():
        create_shortcut(desktop / "ElectronStore.lnk", exe, icon=exe)


def uninstall_cmd_path(exe):
    return exe.parent / "uninstall.cmd"


def _quoted(path):
    return str(path).replace('"', '""')


def write_uninstall_script(exe):
    exe.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "@echo off\r\n"
        "setlocal\r\n"
        f'del /q "{_quoted(exe)}" 2>nul\r\n'
        f'del /q "{_quoted(start_menu_dir() / "ElectronStore" / "ElectronStore.lnk")}" 2>nul\r\n'
        f'rd "{_quoted(start_menu_dir() / "ElectronStore")}" 2>nul\r\n'
        'del /q "%USERPROFILE%\\Desktop\\ElectronStore.lnk" 2>nul\r\n'
        'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\'
        'Uninstall\\ElectronStore" /f 2>nul\r\n'
        f'rd /q "{_quoted(exe.parent)}" 2>nul\r\n'
    )
    uninstall_cmd_path(exe).write_text(script, encoding="ascii")


def register_uninstall(exe):
    import winreg
    key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\ElectronStore"
    cmd = f'cmd /c ""{_quoted(uninstall_cmd_path(exe))}""'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as k:
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, PRODUCT_NAME)
        winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, "1.0")
        winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "ElectronStore")
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(exe.parent))
        winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, str(exe))
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, cmd)


def install(url, dest, shortcuts=True, report=None):
    """Run the whole install. Returns the final exe path."""
    exe = download(url, dest, report=report)
    if shortcuts and is_windows():
        if report is not None:
            report(0, 0, "Adding shortcuts...")
        add_start_menu_shortcut(exe)
        add_desktop_shortcut(exe)
        write_uninstall_script(exe)
        register_uninstall(exe)
    elif shortcuts and report is not None:
        report(0, 0, "Shortcuts skipped (not Windows)")
    return exe


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="ElectronStore online installer")
    p.add_argument("--url", default=os.environ.get("ELECTRONSTORE_DOWNLOAD_URL")
                   or DEFAULT_URL, help="URL of the app .exe to download")
    p.add_argument("--install-dir", default=None,
                   help="Override the installation folder")
    p.add_argument("--no-shortcuts", action="store_true",
                   help="Skip Start Menu/desktop shortcuts and uninstall entry")
    p.add_argument("--run", action="store_true",
                   help="Launch the app after install (no GUI)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    dest = Path(args.install_dir or install_dir()) / "ElectronStore.exe"

    if not is_windows():
        print("Windows-only installer; downloading for testing only.")
        print(f"Downloading {args.url} ...")
        exe = install(args.url, dest, shortcuts=False)
        print(f"OK -> {exe} ({exe.stat().st_size:,} bytes)")
        if args.run:
            subprocess.Popen([str(exe)])
        return 0

    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except Exception:
        print("Could not start the installer window.")
        return 1

    root = tk.Tk()
    root.title("ElectronStore Installer")
    root.resizable(False, False)
    try:
        from paths import ICON_PATH
        if ICON_PATH.exists():
            root.iconbitmap(str(ICON_PATH))
    except Exception:
        pass

    frame = tk.Frame(root, padx=24, pady=20)
    frame.pack()
    tk.Label(frame, text="ElectronStore Installer",
             font=("Segoe UI", 16, "bold")).pack()
    status = tk.Label(frame, text="Connecting...", wraplength=420,
                      justify="left", font=("Segoe UI", 10))
    status.pack(pady=12)
    bar = ttk.Progressbar(frame, length=420, mode="determinate")
    bar.pack()

    state = {"exe": None, "ok": False}

    def report(done, total, msg=None):
        if msg:
            status.configure(text=msg)
        elif total:
            bar.configure(mode="determinate", maximum=total)
            bar["value"] = done
            status.configure(
                text=f"Downloading... {done / 1048576:,.1f} MB of "
                     f"{total / 1048576:,.1f} MB")
        else:
            bar.configure(mode="indeterminate")
            bar.start(10)
        root.update_idletasks()

    def done_install():
        bar.configure(mode="determinate", maximum=100, value=100)
        bar.stop()
        status.configure(
            text=f"ElectronStore installed to:\n{dest}"
                 "\nYou can remove it any time from Settings > Apps.")
        run_btn.configure(state="normal")
        close_btn.configure(text="Close and run", command=lambda: launch(True))

    def launch(silent):
        if state["exe"] and state["ok"]:
            subprocess.Popen([str(state["exe"])])
        if silent:
            root.destroy()

    def install_now():
        try:
            state["exe"] = install(
                args.url, dest,
                shortcuts=not args.no_shortcuts,
                report=report)
            state["ok"] = True
        except Exception as exc:
            messagebox.showerror("Install failed", str(exc))
            root.destroy()
            return
        done_install()

    btns = tk.Frame(frame)
    btns.pack(pady=12)
    run_btn = tk.Button(btns, text="Run ElectronStore", state="disabled",
                        command=lambda: launch(False), padx=12)
    run_btn.pack(side="left")
    close_btn = tk.Button(btns, text="Close", command=root.destroy, padx=12)
    close_btn.pack(side="left", padx=8)

    root.after(100, install_now)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())