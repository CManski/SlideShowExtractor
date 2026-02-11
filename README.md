# Photo Extractor

A desktop application that extracts scene-change images from slideshow videos as JPEG files. Double-click and it just works — no installation, no setup, no dependencies.

Available for **Windows** (.exe) and **macOS** (.dmg).

## Using the Application

1. **Launch PhotoExtractor** (double-click the .exe on Windows or the .app on macOS)
2. **Select Video File** — supports .mp4, .avi, .mov, .vob, .mpg, .mpeg, .mkv, .wmv, .ts, .m2ts, .mts, .flv, .webm, .m4v, .3gp, .f4v
3. **Select Destination Folder** — where extracted JPEGs will be saved
4. **Adjust Sensitivity** — slide from 1 (most sensitive, more images) to 9 (least sensitive, fewer images). Default is 5.
5. **Click Extract Images** — wait for progress bar to complete

Output files: `frame_0001.jpg`, `frame_0002.jpg`, etc.

### Tips for DVD Slideshows (VOB files)

- Start with sensitivity **3–5** and adjust from there
- Lower values capture smaller scene changes (good for slideshows with transitions)
- Higher values only capture major scene changes

## Building

### Option A: GitHub Actions (recommended — works from any OS)

1. Push this repo to GitHub
2. Go to **Actions** tab → **Build Photo Extractor** → **Run workflow**
3. When it finishes, download from the **Artifacts** section:
   - `PhotoExtractor-Windows` — contains `PhotoExtractor.exe`
   - `PhotoExtractor-macOS` — contains `PhotoExtractor.dmg`

FFmpeg is downloaded and bundled automatically. No manual steps.

### Option B: Build on Windows

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Double-click `build.bat`
3. Output: `dist\PhotoExtractor.exe`

### Option C: Build on macOS

1. Install Python 3.8+ and Homebrew
2. Run `./build_mac.sh`
3. Output: `dist/PhotoExtractor.dmg`

The script installs FFmpeg via Homebrew and bundles all dependencies automatically.
