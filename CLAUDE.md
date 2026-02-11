# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Photo Extractor is a cross-platform desktop GUI app (Python/tkinter) that uses FFmpeg scene detection to extract still images from slideshow videos. Ships as a standalone `.exe` (Windows) or `.dmg` containing a `.app` bundle (macOS) via PyInstaller with FFmpeg bundled inside. Target: Windows 10/11 and macOS 12+, zero-install for end users.

## Build

**Automated (GitHub Actions — works from macOS/Linux/Windows):**
Push to `main` or manually trigger the workflow. It downloads FFmpeg, builds with PyInstaller, and uploads both `PhotoExtractor.exe` and `PhotoExtractor.dmg` as artifacts.

**Manual Windows:**
```
build.bat
```
Auto-downloads FFmpeg if missing, installs PyInstaller, outputs `dist\PhotoExtractor.exe`.

**Manual macOS:**
```
./build_mac.sh
```
Installs FFmpeg via Homebrew if missing, bundles dylibs for standalone distribution, builds .app with PyInstaller, creates `dist/PhotoExtractor.dmg`.

**Run from source (dev):**
```
python photo_extractor.py
```
Requires `ffmpeg` and `ffprobe` either in a `ffmpeg/` sibling folder (with platform-appropriate names) or on your system PATH.

## Architecture

Single-file app (`photo_extractor.py`), one class:

- **`PhotoExtractorApp`** — tkinter GUI with file/folder pickers, sensitivity slider (1–9), extract/cancel buttons, progress bar, status text.
- **Extraction runs on a daemon thread** — spawns FFmpeg subprocess, parses `time=` from stderr for progress, posts updates to UI thread via `root.after()`.
- **FFmpeg path resolution** (`_find_binary`) — checks `sys._MEIPASS` (PyInstaller bundle) first, then `ffmpeg/` folder next to the exe/script, then falls back to system PATH.
- **`_SUBPROCESS_FLAGS`** — set to `CREATE_NO_WINDOW` on Windows only; 0 on macOS/Linux.
- **`_BINARY_EXT`** — `.exe` on Windows, empty string on macOS/Linux. Used for platform-aware binary lookup.

### macOS .dmg Build

`build_mac.sh` handles the full pipeline:
1. Copies FFmpeg from Homebrew (or system PATH)
2. Uses `otool`/`install_name_tool` to bundle all non-system dylibs alongside FFmpeg with `@loader_path` references
3. Builds `.app` with PyInstaller (`--onedir --windowed`)
4. Packages into `.dmg` with an Applications symlink using `hdiutil`

## Key Details

- Sensitivity slider 1–9 maps to FFmpeg scene threshold 0.1–0.9 (`threshold = value / 10`).
- FFmpeg command: `ffmpeg -y -analyzeduration 100000000 -probesize 100000000 -i [input] -vf "select='gt(scene,{threshold})'" -vsync vfr -q:v 2 [dest]/frame_%04d.jpg`
- `-q:v 2` produces high-quality JPEGs.
- `-analyzeduration`/`-probesize` at 100MB ensures proper handling of VOB/MPEG/transport stream files.
- Progress uses ffprobe for total duration, then parses FFmpeg's `time=HH:MM:SS.cs` output.
- All subprocess calls use `_SUBPROCESS_FLAGS` to avoid console window flashes on Windows.
- Supported formats: mp4, avi, mov, vob, mpg, mpeg, mkv, wmv, ts, m2ts, mts, flv, webm, m4v, 3gp, f4v.
