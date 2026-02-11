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
- **Source selection** — supports both single video files and folders (batch mode). Folder mode scans for supported video extensions and processes each file into its own subfolder.
- **Extraction runs on a daemon thread** — spawns FFmpeg subprocess per video, parses `time=` from stderr for progress, posts updates to UI thread via `root.after()`.
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

- Sensitivity slider 1–9 uses an exponential scale: `threshold = 0.01 * (1.7 ** (value - 1))`, mapping to approximately 0.01–0.70. Low values catch dissolve/fade transitions; high values catch only hard cuts.
- Scene detection uses a settle delay: on detecting a transition, the filter waits 1 second before capturing to grab the clean slide rather than a mid-transition frame. Implemented via FFmpeg's `select` filter with `st()`/`ld()` register expressions.
- FFmpeg filter chain: `select='if(gt(scene,T)+not(n),st(0,t+1)*0,if(ld(0)*gte(t+1-ld(0),1),st(0,0)*0+1,0))',scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuvj420p`
- `scale=trunc(iw/2)*2:trunc(ih/2)*2` ensures even dimensions for the MJPEG encoder.
- `format=yuvj420p` converts to JPEG-compatible pixel format (fixes DVD/VOB sources).
- `-q:v 2` produces high-quality JPEGs.
- `-analyzeduration`/`-probesize` at 100MB ensures proper handling of VOB/MPEG/transport stream files.
- Progress uses ffprobe for total duration, then parses FFmpeg's `time=HH:MM:SS.cs` output. Batch mode shows overall progress across all files.
- All subprocess calls use `_SUBPROCESS_FLAGS` to avoid console window flashes on Windows.
- Supported formats: mp4, avi, mov, vob, mpg, mpeg, mkv, wmv, ts, m2ts, mts, flv, webm, m4v, 3gp, f4v.
