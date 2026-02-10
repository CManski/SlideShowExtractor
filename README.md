# Photo Extractor

A Windows desktop application that extracts scene-change images from slideshow videos as JPEG files. Your boss double-clicks the .exe and it just works — no installation, no setup, no dependencies.

## Using the Application

1. **Double-click PhotoExtractor.exe**
2. **Select Video File** — supports .mp4, .avi, .mov, .vob, .mpg, .mpeg, .mkv, .wmv
3. **Select Destination Folder** — where extracted JPEGs will be saved
4. **Adjust Sensitivity** — slide from 1 (most sensitive, more images) to 9 (least sensitive, fewer images). Default is 5.
5. **Click Extract Images** — wait for progress bar to complete

Output files: `frame_0001.jpg`, `frame_0002.jpg`, etc.

### Tips for DVD Slideshows (VOB files)

- Start with sensitivity **3–5** and adjust from there
- Lower values capture smaller scene changes (good for slideshows with transitions)
- Higher values only capture major scene changes

## Building the .exe

### Option A: GitHub Actions (recommended — works from any OS)

1. Push this repo to GitHub
2. Go to **Actions** tab → **Build PhotoExtractor.exe** → **Run workflow**
3. When it finishes, download `PhotoExtractor.exe` from the **Artifacts** section

FFmpeg is downloaded and bundled automatically. No manual steps.

### Option B: Build on a Windows PC

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Double-click `build.bat`
3. The script downloads FFmpeg automatically and builds `dist\PhotoExtractor.exe`

That's it. Share the .exe file with anyone — everything is bundled inside.
