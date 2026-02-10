"""
Photo Extractor - Extract scene-change images from slideshow videos using FFmpeg.
"""

import os
import sys
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Windows-only flag to hide console windows from subprocess calls
_SUBPROCESS_FLAGS = 0
if sys.platform == "win32":
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW


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
    """Find a bundled binary, checking the PyInstaller bundle first, then next to the exe."""
    for base in (_resource_dir(), _exe_dir()):
        path = os.path.join(base, "ffmpeg", name)
        if os.path.isfile(path):
            return path
    return None


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    ffprobe = _find_binary("ffprobe.exe")
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
    ("Video files", "*.mp4 *.avi *.mov *.vob *.mpg *.mpeg *.mkv *.wmv"),
    ("All files", "*.*"),
]


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

        # -- Video file --
        f1 = ttk.LabelFrame(self.root, text="Source Video", padding=8)
        f1.pack(fill="x", **pad)
        ttk.Entry(f1, textvariable=self.video_path, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(f1, text="Select Video File", command=self._select_video).pack(side="right")

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
        video = self.video_path.get()
        dest = self.dest_folder.get()

        if not video:
            messagebox.showwarning("Missing Input", "Please select a video file.")
            return
        if not os.path.isfile(video):
            messagebox.showerror("File Not Found", f"Video file not found:\n{video}")
            return
        if not dest:
            messagebox.showwarning("Missing Input", "Please select a destination folder.")
            return
        if not os.path.isdir(dest):
            messagebox.showerror("Folder Not Found", f"Destination folder not found:\n{dest}")
            return

        ffmpeg = _find_binary("ffmpeg.exe")
        if not ffmpeg:
            messagebox.showerror(
                "FFmpeg Not Found",
                "Could not find the bundled ffmpeg.exe.\n\n"
                "The application may be corrupted — try re-downloading it.")
            return

        self.cancelled = False
        self._set_running(True)
        self.progress["value"] = 0
        self.status_text.set("Starting extraction...")
        threading.Thread(target=self._run_extraction, args=(ffmpeg, video, dest), daemon=True).start()

    def _run_extraction(self, ffmpeg, video, dest):
        threshold = round(self.sensitivity.get() / 10.0, 1)
        output_pattern = os.path.join(dest, "frame_%04d.jpg")
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
                stdout=subprocess.DEVNULL,     # FIX: discard stdout to prevent deadlock
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
                        pct = min(99, cur / duration * 100)
                        self.root.after(0, self._update_progress, pct, cur, duration)

            self.process.wait()

            # If user cancelled, just clean up quietly
            if self.cancelled:
                self.root.after(0, self._cancelled)
                return

            if self.process.returncode == 0:
                count = sum(1 for f in os.listdir(dest)
                            if f.startswith("frame_") and f.lower().endswith(".jpg"))
                self.root.after(0, self._done, count)
            else:
                # Show the actual FFmpeg error to the user
                error_detail = "\n".join(last_error_lines[-10:])
                msg = f"FFmpeg failed (exit code {self.process.returncode}).\n\n{error_detail}"
                self.root.after(0, self._error, msg)

        except FileNotFoundError:
            self.root.after(0, self._error, "FFmpeg executable not found.")
        except Exception as e:
            self.root.after(0, self._error, str(e))
        finally:
            self.process = None

    def _update_progress(self, pct, cur, dur):
        self.progress["value"] = pct
        self.status_text.set(f"Extracting... {pct:.0f}%  ({cur:.0f}s / {dur:.0f}s)")

    def _done(self, count):
        self.progress["value"] = 100
        self.status_text.set(f"Done! Extracted {count} image{'s' if count != 1 else ''}.")
        self._set_running(False)
        messagebox.showinfo("Complete", f"Extracted {count} image{'s' if count != 1 else ''}.")

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
