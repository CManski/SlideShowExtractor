@echo off
REM Build Photo Extractor into a standalone .exe
REM Prerequisites: Python 3.8+ with pip

echo === Photo Extractor Build ===
echo.

REM Auto-download FFmpeg if not present
if not exist "ffmpeg\ffmpeg.exe" (
    echo FFmpeg not found. Downloading automatically...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg_dl.zip'"
    echo Extracting FFmpeg...
    powershell -Command "Expand-Archive -Path 'ffmpeg_dl.zip' -DestinationPath 'ffmpeg_temp' -Force"
    if not exist "ffmpeg" mkdir ffmpeg
    powershell -Command "$bin = Get-ChildItem -Path 'ffmpeg_temp' -Recurse -Directory -Filter 'bin' | Select-Object -First 1; Copy-Item \"$($bin.FullName)\ffmpeg.exe\" -Destination 'ffmpeg\ffmpeg.exe'; Copy-Item \"$($bin.FullName)\ffprobe.exe\" -Destination 'ffmpeg\ffprobe.exe'"
    del ffmpeg_dl.zip
    rmdir /s /q ffmpeg_temp
    echo FFmpeg downloaded successfully.
    echo.
)

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building PhotoExtractor.exe...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "PhotoExtractor" ^
    --add-data "ffmpeg\ffmpeg.exe;ffmpeg" ^
    --add-data "ffmpeg\ffprobe.exe;ffmpeg" ^
    photo_extractor.py

echo.
if exist "dist\PhotoExtractor.exe" (
    echo ============================================
    echo  BUILD SUCCESSFUL!
    echo  Output: dist\PhotoExtractor.exe
    echo ============================================
) else (
    echo BUILD FAILED. Check output above for errors.
)
pause
