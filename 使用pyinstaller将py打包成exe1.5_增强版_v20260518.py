# -*- coding: utf-8 -*-
"""PyInstaller 打包工具增强版。

功能重点：
- 自动检测 PyInstaller，并在界面显示实际位置。
- 路径输入框支持超长路径显示、复制和手动编辑。
- Windows 下对文件系统操作尽量使用长路径前缀，减少 MAX_PATH 限制。
- 记忆常用工作目录、脚本目录、输出目录和图标目录。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Iterable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "PyInstaller打包工具"
APP_VERSION = "v1.5"
APP_TITLE = f"{APP_NAME} {APP_VERSION} 增强版"
DEFAULT_PYINSTALLER_TEXT = "未检测到 PyInstaller，请点击重新检测或手动选择"
MAX_RECENT_ITEMS = 20


def app_config_path() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        config_dir = Path(base) / APP_NAME
    else:
        config_dir = Path.home() / f".{APP_NAME}"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "settings.json"


CONFIG_FILE = app_config_path()


def strip_long_path_prefix(path: str) -> str:
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def normalize_display_path(path: str) -> str:
    if not path:
        return ""
    return strip_long_path_prefix(os.path.abspath(os.path.expanduser(path)))


def to_long_path(path: str) -> str:
    """Return a Windows extended-length path for filesystem-heavy operations."""
    if not path:
        return path
    normalized = normalize_display_path(path)
    if os.name != "nt" or normalized.startswith("\\\\?\\"):
        return normalized
    if normalized.startswith("\\\\"):
        return "\\\\?\\UNC\\" + normalized.lstrip("\\")
    return "\\\\?\\" + normalized


def is_file(path: str) -> bool:
    return bool(path) and os.path.isfile(to_long_path(path))


def is_dir(path: str) -> bool:
    return bool(path) and os.path.isdir(to_long_path(path))


def unique_existing(paths: Iterable[str], directory: bool | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in paths:
        normalized = normalize_display_path(str(item).strip())
        if not normalized:
            continue
        if directory is True and not is_dir(normalized):
            continue
        if directory is False and not is_file(normalized):
            continue
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            result.append(normalized)
    return result[:MAX_RECENT_ITEMS]


def safe_exe_name(name: str, fallback: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name.strip())
    cleaned = cleaned.strip(" .")
    return cleaned or fallback


def load_settings() -> dict:
    defaults = {
        "last_script": "",
        "last_output": "",
        "last_icon": "",
        "last_work_dir": "",
        "pyinstaller_path": "",
        "recent_work_dirs": [],
        "recent_script_dirs": [],
        "recent_output_dirs": [],
        "recent_icon_dirs": [],
    }
    if not CONFIG_FILE.exists():
        return defaults
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return defaults
    if isinstance(data, dict):
        defaults.update(data)
    return defaults


def save_settings(settings: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)


def detect_pyinstaller() -> dict[str, str]:
    candidates: list[dict[str, str]] = []
    frozen = bool(getattr(sys, "frozen", False))

    for python_exe in discover_python_executables():
        pyinstaller_exe = pyinstaller_exe_from_python(python_exe)
        if pyinstaller_exe and is_valid_pyinstaller_exe(pyinstaller_exe):
            candidates.append(
                {
                    "mode": "exe",
                    "command": pyinstaller_exe,
                    "display": pyinstaller_exe,
                    "description": "Python Scripts 目录中的 pyinstaller.exe",
                }
            )

    executable = shutil.which("pyinstaller")
    if executable:
        executable = normalize_display_path(executable)
        if is_valid_pyinstaller_exe(executable):
            candidates.append(
                {
                    "mode": "exe",
                    "command": executable,
                    "display": executable,
                    "description": "系统 PATH 中的 pyinstaller.exe",
                }
            )

    scripts_dir = Path(sys.executable).parent / "Scripts"
    candidate = normalize_display_path(str(scripts_dir / "pyinstaller.exe"))
    if is_valid_pyinstaller_exe(candidate):
        candidates.append(
            {
                "mode": "exe",
                "command": candidate,
                "display": candidate,
                "description": "当前 Python Scripts 目录",
            }
        )

    module_spec = None if frozen else importlib.util.find_spec("PyInstaller")
    if module_spec and module_spec.origin:
        candidates.append(
            {
                "mode": "module",
                "command": sys.executable,
                "display": normalize_display_path(module_spec.origin),
                "description": "当前 Python 环境的 PyInstaller 模块",
            }
        )

    for python_exe in discover_python_executables():
        version = probe_python_module_pyinstaller(python_exe)
        if version:
            candidates.append(
                {
                    "mode": "python_module",
                    "command": python_exe,
                    "display": python_exe,
                    "description": f"Python 环境中的 PyInstaller {version}",
                }
            )

    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["mode"], candidate["display"].lower())
        if key in seen:
            continue
        seen.add(key)
        return candidate

    return {"mode": "", "command": "", "display": "", "description": ""}


def pyinstaller_exe_from_python(python_exe: str) -> str:
    if not python_exe:
        return ""
    candidate = Path(normalize_display_path(python_exe)).parent / "Scripts" / "pyinstaller.exe"
    if is_file(str(candidate)):
        return normalize_display_path(str(candidate))
    return ""


def is_valid_pyinstaller_exe(path: str) -> bool:
    if not is_file(path):
        return False
    if "pyinstaller" not in Path(path).name.lower():
        return False
    try:
        completed = subprocess.run(
            [to_long_path(path), "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except Exception:
        return False
    return completed.returncode == 0 and bool((completed.stdout or completed.stderr).strip())


def discover_python_executables() -> list[str]:
    candidates: list[str] = []

    if not getattr(sys, "frozen", False):
        candidates.append(sys.executable)

    python_from_path = shutil.which("python")
    if python_from_path:
        candidates.append(python_from_path)

    py_launcher = shutil.which("py")
    if py_launcher:
        try:
            completed = subprocess.run(
                [py_launcher, "-0p"],
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in (completed.stdout or "").splitlines():
                match = re.search(r"([A-Z]:\\.*?python(?:\.exe)?)$", line.strip(), re.IGNORECASE)
                if match:
                    candidates.append(match.group(1))
        except Exception:
            pass

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")]
    search_roots = [
        Path(local_app_data) / "Programs" / "Python" if local_app_data else None,
        *(Path(path) / "Python" for path in program_files if path),
    ]
    for root in search_roots:
        if not root or not root.exists():
            continue
        try:
            for exe in root.glob("Python*/python.exe"):
                candidates.append(str(exe))
        except OSError:
            continue

    return unique_existing(candidates, directory=False)


def probe_python_module_pyinstaller(python_exe: str) -> str:
    try:
        completed = subprocess.run(
            [to_long_path(python_exe), "-m", "PyInstaller", "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def run_pyinstaller_version(command_info: dict[str, str]) -> str:
    command = build_pyinstaller_base_command(command_info) + ["--version"]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def build_pyinstaller_base_command(command_info: dict[str, str]) -> list[str]:
    mode = command_info.get("mode", "")
    command = command_info.get("command", "")
    if mode == "module" and command:
        return [sys.executable, "-m", "PyInstaller"]
    if mode == "python_module" and command:
        return [to_long_path(command), "-m", "PyInstaller"]
    if mode == "exe" and command:
        return [to_long_path(command)]
    return []


class PathRow:
    def __init__(
        self,
        parent: tk.Widget,
        row: int,
        label: str,
        browse_text: str,
        browse_command,
        paste_command=None,
        placeholder: str = "",
    ) -> None:
        self.value = tk.StringVar(value=placeholder)
        self.entry = ttk.Entry(parent, textvariable=self.value)
        self.entry.state(["readonly"])
        self.entry.bind("<FocusIn>", lambda _event: self.entry.selection_range(0, tk.END))

        ttk.Button(parent, text=browse_text, command=browse_command).grid(
            row=row, column=0, padx=(12, 8), pady=5, sticky="ew"
        )
        ttk.Label(parent, text=label).grid(row=row, column=1, padx=(0, 6), pady=5, sticky="w")
        self.entry.grid(row=row, column=2, padx=(0, 12), pady=5, sticky="ew")
        if paste_command:
            ttk.Button(parent, text="粘贴", command=paste_command).grid(
                row=row, column=3, padx=(0, 12), pady=5, sticky="ew"
            )

    def set(self, value: str) -> None:
        self.entry.state(["!readonly"])
        self.value.set(value)
        self.entry.xview_moveto(1)
        self.entry.state(["readonly"])

    def get(self) -> str:
        return self.value.get().strip()


class PyInstallerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("880x560")
        self.root.minsize(760, 500)

        self.settings = load_settings()
        self.python_script_path = normalize_display_path(self.settings.get("last_script", ""))
        self.output_path = normalize_display_path(self.settings.get("last_output", ""))
        self.icon_path = normalize_display_path(self.settings.get("last_icon", ""))
        self.work_dir = normalize_display_path(self.settings.get("last_work_dir", ""))
        self.exe_name = ""
        self.packaging = False
        self.pyinstaller_info = detect_pyinstaller()

        saved_pyinstaller = normalize_display_path(self.settings.get("pyinstaller_path", ""))
        if saved_pyinstaller and is_valid_pyinstaller_exe(saved_pyinstaller):
            self.pyinstaller_info = {
                "mode": "exe",
                "command": saved_pyinstaller,
                "display": saved_pyinstaller,
                "description": "上次手动选择的 pyinstaller.exe",
            }
        elif saved_pyinstaller:
            self.settings["pyinstaller_path"] = ""

        self.create_widgets()
        self.refresh_path_fields()
        self.refresh_pyinstaller_label()
        self.refresh_recent_values()

    def create_widgets(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(12, 10, 12, 4))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=APP_TITLE, font=("Microsoft YaHei UI", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(header, text="重新检测 PyInstaller", command=self.auto_detect_pyinstaller).grid(
            row=0, column=1, padx=(8, 0), sticky="e"
        )

        body = ttk.Frame(self.root, padding=(0, 4, 0, 0))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(2, weight=1)

        ttk.Label(body, text="常用工作目录").grid(row=0, column=0, padx=(12, 8), pady=5, sticky="w")
        self.work_dir_var = tk.StringVar()
        self.work_dir_combo = ttk.Combobox(body, textvariable=self.work_dir_var, values=[], state="readonly")
        self.work_dir_combo.grid(row=0, column=1, columnspan=3, padx=(0, 12), pady=5, sticky="ew")
        self.work_dir_combo.bind("<<ComboboxSelected>>", self.use_recent_work_dir)

        self.script_row = PathRow(
            body,
            1,
            "脚本路径",
            "选择脚本",
            self.select_python_script,
            lambda: self.paste_path("script"),
            "未选择脚本",
        )
        self.output_row = PathRow(
            body,
            2,
            "输出目录",
            "选择输出",
            self.select_output_path,
            lambda: self.paste_path("output"),
            "未选择输出目录",
        )

        ttk.Label(body, text="输出 exe 名称").grid(row=3, column=0, padx=(12, 8), pady=5, sticky="w")
        self.exe_name_var = tk.StringVar()
        ttk.Entry(body, textvariable=self.exe_name_var).grid(
            row=3, column=1, columnspan=3, padx=(0, 12), pady=5, sticky="ew"
        )

        self.no_console_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(body, text="窗口程序模式：运行 exe 时不显示控制台", variable=self.no_console_var).grid(
            row=4, column=0, columnspan=4, padx=12, pady=5, sticky="w"
        )

        self.pyinstaller_row = PathRow(
            body,
            5,
            "PyInstaller 位置",
            "手动选择",
            self.select_pyinstaller_path,
            lambda: self.paste_path("pyinstaller"),
            DEFAULT_PYINSTALLER_TEXT,
        )

        self.icon_row = PathRow(
            body,
            6,
            "图标路径",
            "选择图标",
            self.select_icon_path,
            lambda: self.paste_path("icon"),
            "未选择图标",
        )

        action_frame = ttk.Frame(body)
        action_frame.grid(row=7, column=0, columnspan=4, padx=12, pady=(8, 4), sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        self.package_button = ttk.Button(action_frame, text="开始打包", command=self.start_packaging)
        self.package_button.grid(row=0, column=0, sticky="ew")

        self.progress_bar = ttk.Progressbar(body, orient="horizontal", mode="indeterminate")
        self.progress_bar.grid(row=8, column=0, columnspan=4, padx=12, pady=(4, 6), sticky="ew")
        self.progress_bar.grid_remove()

        log_frame = ttk.LabelFrame(body, text="状态与日志", padding=(8, 6))
        log_frame.grid(row=9, column=0, columnspan=4, padx=12, pady=(6, 12), sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        body.rowconfigure(9, weight=1)

        self.log_text = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.append_log(f"配置文件：{CONFIG_FILE}")

    def read_clipboard_path(self) -> str:
        try:
            raw = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showerror("错误", "剪贴板里没有可用文本。")
            return ""
        return normalize_display_path(raw.strip().strip('"').strip("'"))

    def paste_path(self, kind: str) -> None:
        path = self.read_clipboard_path()
        if not path:
            return

        if kind == "script":
            if not is_file(path) or Path(path).suffix.lower() != ".py":
                messagebox.showerror("错误", "剪贴板路径不是有效的 .py 脚本。")
                return
            self.python_script_path = path
            self.exe_name_var.set(Path(path).stem)
            self.remember_recent_dir("recent_script_dirs", path)
        elif kind == "output":
            if not is_dir(path):
                messagebox.showerror("错误", "剪贴板路径不是有效的输出目录。")
                return
            self.output_path = path
            self.remember_recent_dir("recent_output_dirs", path)
        elif kind == "icon":
            if not is_file(path) or Path(path).suffix.lower() != ".ico":
                messagebox.showerror("错误", "剪贴板路径不是有效的 .ico 图标。")
                return
            self.icon_path = path
            self.remember_recent_dir("recent_icon_dirs", path)
        elif kind == "pyinstaller":
            if not is_valid_pyinstaller_exe(path):
                messagebox.showerror("错误", "剪贴板路径不是有效的 pyinstaller.exe。")
                return
            self.pyinstaller_info = {
                "mode": "exe",
                "command": path,
                "display": path,
                "description": "从剪贴板粘贴的 pyinstaller.exe",
            }
            self.settings["pyinstaller_path"] = path
            self.remember_recent_dir("recent_work_dirs", path)

        self.refresh_path_fields()
        if kind == "pyinstaller":
            self.refresh_pyinstaller_label()
        self.save_current_settings()

    def append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message.rstrip() + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def refresh_path_fields(self) -> None:
        self.script_row.set(self.python_script_path or "未选择脚本")
        self.output_row.set(self.output_path or "未选择输出目录")
        self.icon_row.set(self.icon_path or "未选择图标")
        if self.python_script_path and not self.exe_name_var.get():
            self.exe_name_var.set(Path(self.python_script_path).stem)

    def refresh_pyinstaller_label(self) -> None:
        if self.pyinstaller_info.get("display"):
            version = run_pyinstaller_version(self.pyinstaller_info)
            suffix = f"（{version}）" if version else ""
            text = f"{self.pyinstaller_info['display']} {suffix}"
            self.pyinstaller_row.set(text)
            self.append_log(f"PyInstaller：{self.pyinstaller_info['description']} - {text}")
        else:
            self.pyinstaller_row.set(DEFAULT_PYINSTALLER_TEXT)
            self.append_log("未自动检测到 PyInstaller。")

    def refresh_recent_values(self) -> None:
        recents = unique_existing(self.settings.get("recent_work_dirs", []), directory=True)
        if self.work_dir and is_dir(self.work_dir):
            recents = unique_existing([self.work_dir, *recents], directory=True)
        self.settings["recent_work_dirs"] = recents
        self.work_dir_combo["values"] = recents
        self.work_dir_var.set(self.work_dir if self.work_dir else (recents[0] if recents else ""))

    def use_recent_work_dir(self, _event=None) -> None:
        selected = normalize_display_path(self.work_dir_var.get())
        if selected and is_dir(selected):
            self.work_dir = selected
            self.remember_work_dir(selected)
            self.append_log(f"已切换常用工作目录：{selected}")

    def initial_dir(self, key: str) -> str:
        configured = self.settings.get(key, "")
        configured_dirs = configured if isinstance(configured, list) else [configured]
        candidates = [
            self.work_dir,
            self.output_path,
            self.python_script_path and str(Path(self.python_script_path).parent),
            *configured_dirs,
            str(Path.home()),
        ]
        for candidate in candidates:
            candidate = normalize_display_path(candidate)
            if candidate and is_dir(candidate):
                return candidate
        return str(Path.home())

    def remember_work_dir(self, path: str) -> None:
        if not path:
            return
        directory = normalize_display_path(path if is_dir(path) else str(Path(path).parent))
        if not is_dir(directory):
            return
        self.work_dir = directory
        self.settings["last_work_dir"] = directory
        self.settings["recent_work_dirs"] = unique_existing(
            [directory, *self.settings.get("recent_work_dirs", [])], directory=True
        )
        self.refresh_recent_values()

    def remember_recent_dir(self, key: str, path: str) -> None:
        directory = normalize_display_path(path if is_dir(path) else str(Path(path).parent))
        if is_dir(directory):
            self.settings[key] = unique_existing([directory, *self.settings.get(key, [])], directory=True)
            self.remember_work_dir(directory)

    def save_current_settings(self) -> None:
        self.settings["last_script"] = self.python_script_path
        self.settings["last_output"] = self.output_path
        self.settings["last_icon"] = self.icon_path
        if self.pyinstaller_info.get("mode") == "exe" and self.pyinstaller_info.get("display"):
            self.settings["pyinstaller_path"] = self.pyinstaller_info["display"]
        save_settings(self.settings)

    def auto_detect_pyinstaller(self) -> None:
        self.pyinstaller_info = detect_pyinstaller()
        self.settings["pyinstaller_path"] = ""
        self.refresh_pyinstaller_label()
        self.save_current_settings()

    def select_python_script(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择 Python 脚本",
            initialdir=self.initial_dir("recent_script_dirs"),
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self.python_script_path = normalize_display_path(file_path)
        self.exe_name_var.set(Path(self.python_script_path).stem)
        self.remember_recent_dir("recent_script_dirs", self.python_script_path)
        self.refresh_path_fields()
        self.save_current_settings()

    def select_output_path(self) -> None:
        folder_path = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.initial_dir("recent_output_dirs"),
            mustexist=True,
        )
        if not folder_path:
            return
        self.output_path = normalize_display_path(folder_path)
        self.remember_recent_dir("recent_output_dirs", self.output_path)
        self.refresh_path_fields()
        self.save_current_settings()

    def select_pyinstaller_path(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择 pyinstaller.exe",
            initialdir=self.initial_dir("recent_work_dirs"),
            filetypes=[("PyInstaller executable", "pyinstaller.exe"), ("Executable", "*.exe"), ("All files", "*.*")],
        )
        if not file_path:
            return
        selected = normalize_display_path(file_path)
        if not is_valid_pyinstaller_exe(selected):
            messagebox.showerror("错误", "请选择有效的 pyinstaller.exe。")
            return
        self.pyinstaller_info = {
            "mode": "exe",
            "command": selected,
            "display": selected,
            "description": "手动选择",
        }
        self.settings["pyinstaller_path"] = selected
        self.remember_recent_dir("recent_work_dirs", selected)
        self.refresh_pyinstaller_label()
        self.save_current_settings()

    def select_icon_path(self) -> None:
        file_path = filedialog.askopenfilename(
            title="选择图标文件",
            initialdir=self.initial_dir("recent_icon_dirs"),
            filetypes=[("ICO files", "*.ico"), ("All files", "*.*")],
        )
        if not file_path:
            self.icon_path = ""
            self.refresh_path_fields()
            self.save_current_settings()
            return
        self.icon_path = normalize_display_path(file_path)
        self.remember_recent_dir("recent_icon_dirs", self.icon_path)
        self.refresh_path_fields()
        self.save_current_settings()

    def validate_before_packaging(self) -> bool:
        if self.packaging:
            messagebox.showinfo("提示", "正在打包中，请稍候。")
            return False
        if not self.python_script_path or not is_file(self.python_script_path):
            messagebox.showerror("错误", "请先选择有效的 Python 脚本。")
            return False
        if not self.output_path or not is_dir(self.output_path):
            messagebox.showerror("错误", "请先选择有效的输出目录。")
            return False
        if self.icon_path and not is_file(self.icon_path):
            messagebox.showerror("错误", "图标路径无效，请重新选择。")
            return False
        if not build_pyinstaller_base_command(self.pyinstaller_info):
            messagebox.showerror("错误", "未找到 PyInstaller，请先重新检测或手动选择。")
            return False
        return True

    def build_command(self) -> list[str]:
        fallback_name = Path(self.python_script_path).stem
        self.exe_name = safe_exe_name(self.exe_name_var.get(), fallback_name)
        self.exe_name_var.set(self.exe_name)

        command = build_pyinstaller_base_command(self.pyinstaller_info)
        command.extend(
            [
                "--onefile",
                "--clean",
                "--noconfirm",
                "--distpath",
                to_long_path(self.output_path),
                "--workpath",
                to_long_path(str(Path(self.output_path) / "_pyinstaller_build")),
                "--specpath",
                to_long_path(str(Path(self.output_path) / "_pyinstaller_spec")),
                "--name",
                self.exe_name,
            ]
        )
        if self.no_console_var.get():
            command.append("--noconsole")
        if self.icon_path:
            command.extend(["--icon", to_long_path(self.icon_path)])
        command.append(to_long_path(self.python_script_path))
        return command

    def start_packaging(self) -> None:
        if not self.validate_before_packaging():
            return
        self.save_current_settings()
        command = self.build_command()
        self.packaging = True
        self.package_button.configure(state="disabled", text="打包中...")
        self.progress_bar.grid()
        self.progress_bar.start()
        self.append_log("开始打包：")
        self.append_log(" ".join(f'"{item}"' if " " in item else item for item in command))
        threading.Thread(target=self.run_pyinstaller, args=(command,), daemon=True).start()

    def run_pyinstaller(self, command: list[str]) -> None:
        try:
            process = subprocess.Popen(
                command,
                cwd=to_long_path(self.work_dir or str(Path(self.python_script_path).parent)),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            assert process.stdout is not None
            for line in process.stdout:
                self.root.after(0, self.append_log, line.rstrip())
            return_code = process.wait()
            self.root.after(0, self.finish_packaging, return_code)
        except Exception as exc:
            self.root.after(0, self.append_log, f"异常：{exc}")
            self.root.after(0, self.finish_packaging, 1)

    def finish_packaging(self, return_code: int) -> None:
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.package_button.configure(state="normal", text="开始打包")
        self.packaging = False

        output_exe = normalize_display_path(str(Path(self.output_path) / f"{self.exe_name}.exe"))
        if return_code == 0 and is_file(output_exe):
            message = f"打包成功：{output_exe}"
            self.append_log(message)
            messagebox.showinfo("成功", message)
            return
        self.append_log(f"打包失败，返回码：{return_code}")
        messagebox.showerror("失败", "打包失败，请查看状态与日志中的错误信息。")


def self_check() -> int:
    settings = load_settings()
    detected = detect_pyinstaller()
    print(f"{APP_TITLE} 自检")
    print(f"Python: {sys.executable}")
    print(f"配置文件: {CONFIG_FILE}")
    print(f"最近工作目录数量: {len(settings.get('recent_work_dirs', []))}")
    if detected.get("display"):
        version = run_pyinstaller_version(detected)
        print(f"PyInstaller: {detected['display']} {version}".strip())
        return 0
    print("PyInstaller: 未检测到")
    return 2


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--self-check", action="store_true", help="运行命令行自检后退出")
    args = parser.parse_args()
    if args.self_check:
        return self_check()

    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass
    app = PyInstallerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
