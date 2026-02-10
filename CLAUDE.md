# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Photo Extractor is a Windows desktop GUI app (Python/tkinter) that uses FFmpeg scene detection to extract still images from slideshow videos. Ships as a single standalone .exe via PyInstaller with FFmpeg bundled inside. Target: Windows 10/11, zero-install for end users.

## Build

**Automated (GitHub Actions — works from macOS/Linux/Windows):**
Push to `main` or manually trigger the workflow. It downloads FFmpeg, builds with PyInstaller, and uploads `PhotoExtractor.exe` as an artifact.

**Manual (Windows only):**
```
build.bat
```
Auto-downloads FFmpeg if missing, installs PyInstaller, outputs `dist\PhotoExtractor.exe`.

**Run from source (dev):**
```
python photo_extractor.py
```
Requires `ffmpeg/ffmpeg.exe` and `ffmpeg/ffprobe.exe` in a sibling folder.

## Architecture

Single-file app (`photo_extractor.py`), one class:

- **`PhotoExtractorApp`** — tkinter GUI with file/folder pickers, sensitivity slider (1–9), extract/cancel buttons, progress bar, status text.
- **Extraction runs on a daemon thread** — spawns FFmpeg subprocess, parses `time=` from stderr for progress, posts updates to UI thread via `root.after()`.
- **FFmpeg path resolution** (`_find_binary`) — checks `sys._MEIPASS` (PyInstaller bundle) first, then `ffmpeg/` folder next to the exe/script.
- **`_SUBPROCESS_FLAGS`** — set to `CREATE_NO_WINDOW` on Windows only, so the code can also run on macOS/Linux for development.

## Key Details

- Sensitivity slider 1–9 maps to FFmpeg scene threshold 0.1–0.9 (`threshold = value / 10`).
- FFmpeg command: `ffmpeg -y -i [input] -vf "select='gt(scene,{threshold})'" -vsync vfr -q:v 2 [dest]/frame_%04d.jpg`
- `-q:v 2` produces high-quality JPEGs.
- Progress uses ffprobe for total duration, then parses FFmpeg's `time=HH:MM:SS.cs` output.
- All subprocess calls use `_SUBPROCESS_FLAGS` to avoid console window flashes on Windows.
