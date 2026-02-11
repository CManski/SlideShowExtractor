"""
Photo Extractor - Extract scene-change images from slideshow videos using FFmpeg.
"""

import os
import sys
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Windows-only flag to hide console windows from subprocess calls
_SUBPROCESS_FLAGS = 0
if sys.platform == "win32":
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW

# Platform-appropriate binary extension
_BINARY_EXT = ".exe" if sys.platform == "win32" else ""


def _resource_dir():
    """Base directory for bundled resources (PyInstaller or source)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _exe_dir():
    """Directory where the running .exe (or script) lives."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _find_binary(name):
    """Find a bundled binary: PyInstaller bundle → next to exe → system PATH."""
    for base in (_resource_dir(), _exe_dir()):
        path = os.path.join(base, "ffmpeg", name)
        if os.path.isfile(path):
            return path
    # Fall back to system PATH (for development without bundled ffmpeg)
    return shutil.which(name)


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    ffprobe = _find_binary(f"ffprobe{_BINARY_EXT}")
    if not ffprobe:
        return None
    try:
        result = subprocess.run(
            [ffprobe,
             "-v", "error",
             "-analyzeduration", "100000000",
             "-probesize", "100000000",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             video_path],
            capture_output=True, text=True,
            creationflags=_SUBPROCESS_FLAGS,
            encoding="utf-8", errors="replace",
        )
        return float(result.stdout.strip())
    except (ValueError, FileNotFoundError, OSError):
        return None


VIDEO_FILETYPES = [
    ("Video files", "*.mp4 *.avi *.mov *.vob *.mpg *.mpeg *.mkv *.wmv "
                    "*.ts *.m2ts *.mts *.flv *.webm *.m4v *.3gp *.f4v"),
    ("All files", "*.*"),
]

VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.vob', '.mpg', '.mpeg', '.mkv', '.wmv',
    '.ts', '.m2ts', '.mts', '.flv', '.webm', '.m4v', '.3gp', '.f4v',
}


class PhotoExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Extractor")
        self.root.resizable(False, False)
        self.root.geometry("540x400")

        self.video_path = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.sensitivity = tk.IntVar(value=5)
        self.status_text = tk.StringVar(value="Ready")
        self.is_running = False
        self.cancelled = False
        self.process = None

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # -- Source (file or folder) --
        f1 = ttk.LabelFrame(self.root, text="Source", padding=8)
        f1.pack(fill="x", **pad)
        ttk.Entry(f1, textvariable=self.video_path, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(f1, text="Select Folder", command=self._select_source_folder).pack(
            side="right")
        ttk.Button(f1, text="Select File", command=self._select_video).pack(
            side="right", padx=(0, 4))

        # -- Destination folder --
        f2 = ttk.LabelFrame(self.root, text="Destination Folder", padding=8)
        f2.pack(fill="x", **pad)
        ttk.Entry(f2, textvariable=self.dest_folder, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(f2, text="Select Destination Folder", command=self._select_dest).pack(side="right")

        # -- Sensitivity slider --
        f3 = ttk.LabelFrame(self.root, text="Sensitivity", padding=8)
        f3.pack(fill="x", **pad)
        ttk.Label(f3, text="1\n(More images)").pack(side="left")
        self.slider = ttk.Scale(f3, from_=1, to=9, orient="horizontal",
                                variable=self.sensitivity, command=self._on_slider)
        self.slider.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Label(f3, text="9\n(Fewer images)").pack(side="left")
        self.sens_label = ttk.Label(f3, text="  5", width=3)
        self.sens_label.pack(side="left", padx=(4, 0))

        # -- Buttons row --
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(**pad)
        self.extract_btn = ttk.Button(btn_frame, text="Extract Images", command=self._start_extraction)
        self.extract_btn.pack(side="left", padx=(0, 8))
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._cancel, state="disabled")
        self.cancel_btn.pack(side="left")

        # -- Progress bar --
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", **pad)

        # -- Status --
        ttk.Label(self.root, textvariable=self.status_text, anchor="w").pack(fill="x", **pad)

    # -------------------------------------------------------------- actions
    def _on_slider(self, _val):
        self.sens_label.config(text=f"  {self.sensitivity.get()}")

    def _select_video(self):
        path = filedialog.askopenfilename(title="Select Video File", filetypes=VIDEO_FILETYPES)
        if path:
            self.video_path.set(path)
            self.status_text.set("Ready")

    def _select_source_folder(self):
        path = filedialog.askdirectory(title="Select Source Folder")
        if path:
            self.video_path.set(path)
            count = sum(1 for f in os.listdir(path)
                        if os.path.isfile(os.path.join(path, f))
                        and os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS)
            self.status_text.set(f"Found {count} video file{'s' if count != 1 else ''} in folder.")

    def _select_dest(self):
        path = filedialog.askdirectory(title="Select Destination Folder")
        if path:
            self.dest_folder.set(path)

    def _set_running(self, running):
        self.is_running = running
        self.extract_btn.config(state="disabled" if running else "normal")
        self.cancel_btn.config(state="normal" if running else "disabled")

    def _cancel(self):
        if self.process:
            self.cancelled = True
            self.process.kill()

    # ----------------------------------------------------------- extraction
    def _start_extraction(self):
        source = self.video_path.get()
        dest = self.dest_folder.get()

        if not source:
            messagebox.showwarning("Missing Input", "Please select a video file or source folder.")
            return
        if not os.path.exists(source):
            messagebox.showerror("Not Found", f"Source not found:\n{source}")
            return

        if os.path.isfile(source):
            videos = [source]
        elif os.path.isdir(source):
            videos = sorted(
                os.path.join(source, f) for f in os.listdir(source)
                if os.path.isfile(os.path.join(source, f))
                and os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS
            )
            if not videos:
                messagebox.showwarning("No Videos Found",
                                       "No supported video files found in the selected folder.")
                return
        else:
            messagebox.showerror("Invalid Source", f"Source is not a file or folder:\n{source}")
            return

        if not dest:
            messagebox.showwarning("Missing Input", "Please select a destination folder.")
            return
        if not os.path.isdir(dest):
            messagebox.showerror("Folder Not Found", f"Destination folder not found:\n{dest}")
            return

        ffmpeg = _find_binary(f"ffmpeg{_BINARY_EXT}")
        if not ffmpeg:
            messagebox.showerror(
                "FFmpeg Not Found",
                "Could not find the bundled FFmpeg.\n\n"
                "The application may be corrupted — try re-downloading it.")
            return

        self.cancelled = False
        self._set_running(True)
        self.progress["value"] = 0
        self.status_text.set("Starting extraction...")
        threading.Thread(target=self._run_extraction, args=(ffmpeg, videos, dest), daemon=True).start()

    def _run_extraction(self, ffmpeg, videos, dest):
        threshold = round(self.sensitivity.get() / 10.0, 1)
        total_files = len(videos)
        batch_mode = total_files > 1
        total_images = 0

        for file_idx, video in enumerate(videos):
            if self.cancelled:
                break

            # Create per-video subfolder when processing multiple files
            if batch_mode:
                video_name = os.path.splitext(os.path.basename(video))[0]
                file_dest = os.path.join(dest, video_name)
                os.makedirs(file_dest, exist_ok=True)
            else:
                file_dest = dest

            output_pattern = os.path.join(file_dest, "frame_%04d.jpg")
            duration = get_video_duration(video)

            cmd = [
                ffmpeg, "-y",
                "-analyzeduration", "100000000",   # 100MB probe for VOB/MPEG
                "-probesize", "100000000",
                "-i", video,
                "-vf", f"select='gt(scene,{threshold})'",
                "-vsync", "vfr",
                "-q:v", "2",
                output_pattern,
            ]

            try:
                self.process = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,     # discard stdout to prevent deadlock
                    creationflags=_SUBPROCESS_FLAGS,
                )

                time_re = re.compile(rb"time=(\d+):(\d+):(\d+)\.(\d+)")
                last_error_lines = []
                buf = b""

                # Read stderr in binary, split on both \r and \n for real-time progress
                while True:
                    chunk = self.process.stderr.read(4096)
                    if not chunk:
                        break
                    buf += chunk
                    # Split on \r or \n to get individual status lines
                    while b"\r" in buf or b"\n" in buf:
                        # Find the earliest delimiter
                        r_pos = buf.find(b"\r")
                        n_pos = buf.find(b"\n")
                        if r_pos == -1:
                            pos = n_pos
                        elif n_pos == -1:
                            pos = r_pos
                        else:
                            pos = min(r_pos, n_pos)

                        line = buf[:pos]
                        buf = buf[pos + 1:]

                        # Track last meaningful lines for error reporting
                        decoded = line.decode("utf-8", errors="replace").strip()
                        if decoded:
                            last_error_lines.append(decoded)
                            if len(last_error_lines) > 20:
                                last_error_lines.pop(0)

                        # Parse progress
                        m = time_re.search(line)
                        if m and duration and duration > 0:
                            h, mi, s, cs = (int(x) for x in m.groups())
                            cur = h * 3600 + mi * 60 + s + cs / 100.0
                            file_pct = min(99, cur / duration * 100)
                            overall_pct = (file_idx * 100 + file_pct) / total_files
                            if batch_mode:
                                status = (f"[{file_idx + 1}/{total_files}] "
                                          f"{os.path.basename(video)} — {file_pct:.0f}%")
                            else:
                                status = (f"Extracting... {overall_pct:.0f}%  "
                                          f"({cur:.0f}s / {duration:.0f}s)")
                            self.root.after(0, self._update_progress,
                                            overall_pct, status)

                self.process.wait()

                # If user cancelled, just clean up quietly
                if self.cancelled:
                    self.root.after(0, self._cancelled)
                    return

                if self.process.returncode == 0:
                    count = sum(1 for f in os.listdir(file_dest)
                                if f.startswith("frame_") and f.lower().endswith(".jpg"))
                    total_images += count
                else:
                    # Show the actual FFmpeg error to the user
                    error_detail = "\n".join(last_error_lines[-10:])
                    filename = os.path.basename(video)
                    msg = (f"FFmpeg failed on {filename} "
                           f"(exit code {self.process.returncode}).\n\n"
                           f"{error_detail}")
                    self.root.after(0, self._error, msg)
                    return

            except FileNotFoundError:
                self.root.after(0, self._error, "FFmpeg executable not found.")
                return
            except Exception as e:
                self.root.after(0, self._error, str(e))
                return
            finally:
                self.process = None

        if not self.cancelled:
            if batch_mode:
                self.root.after(0, self._done_batch, total_images, total_files)
            else:
                self.root.after(0, self._done, total_images)

    def _update_progress(self, pct, status):
        self.progress["value"] = pct
        self.status_text.set(status)

    def _done(self, count):
        self.progress["value"] = 100
        self.status_text.set(f"Done! Extracted {count} image{'s' if count != 1 else ''}.")
        self._set_running(False)
        messagebox.showinfo("Complete", f"Extracted {count} image{'s' if count != 1 else ''}.")

    def _done_batch(self, count, num_files):
        self.progress["value"] = 100
        self.status_text.set(
            f"Done! Extracted {count} image{'s' if count != 1 else ''} "
            f"from {num_files} video{'s' if num_files != 1 else ''}.")
        self._set_running(False)
        messagebox.showinfo(
            "Complete",
            f"Extracted {count} image{'s' if count != 1 else ''} "
            f"from {num_files} video{'s' if num_files != 1 else ''}.")

    def _cancelled(self):
        self.progress["value"] = 0
        self.status_text.set("Cancelled.")
        self._set_running(False)

    def _error(self, msg):
        self.progress["value"] = 0
        self.status_text.set("Error during extraction.")
        self._set_running(False)
        messagebox.showerror("Extraction Error", msg)


def main():
    root = tk.Tk()
    PhotoExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
