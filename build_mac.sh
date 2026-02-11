#!/bin/bash
set -e

echo "=== Photo Extractor macOS Build ==="
echo

# ── Step 1: Ensure FFmpeg binaries are in ffmpeg/ ──────────────────────
if [ -f "ffmpeg/ffmpeg" ] && [ -f "ffmpeg/ffprobe" ]; then
    echo "FFmpeg binaries found in ffmpeg/ directory."
else
    echo "FFmpeg not found in ffmpeg/ directory."
    mkdir -p ffmpeg

    if command -v ffmpeg &>/dev/null && command -v ffprobe &>/dev/null; then
        echo "Copying system FFmpeg binaries..."
        cp "$(command -v ffmpeg)" ffmpeg/ffmpeg
        cp "$(command -v ffprobe)" ffmpeg/ffprobe
    else
        echo "Installing FFmpeg via Homebrew..."
        brew install ffmpeg
        cp "$(command -v ffmpeg)" ffmpeg/ffmpeg
        cp "$(command -v ffprobe)" ffmpeg/ffprobe
    fi

    chmod +x ffmpeg/ffmpeg ffmpeg/ffprobe
    echo "FFmpeg binaries copied."
    echo

    # ── Bundle non-system dylibs so the .app works on machines without Homebrew ──
    echo "Bundling dynamic libraries for standalone distribution..."

    bundle_dylibs() {
        local binary="$1"
        local dest_dir="$2"

        while read -r lib; do
            # Skip system/Apple libraries and already-rewritten references
            case "$lib" in
                /usr/lib/*|/System/*|@*|"") continue ;;
            esac

            local lib_name
            lib_name=$(basename "$lib")

            # Copy the library if we haven't already
            if [ ! -f "$dest_dir/$lib_name" ]; then
                echo "  Bundling: $lib_name"
                cp "$lib" "$dest_dir/$lib_name"
                chmod +w "$dest_dir/$lib_name"
                # Set the library's own install name to @loader_path
                install_name_tool -id "@loader_path/$lib_name" "$dest_dir/$lib_name" 2>/dev/null || true
                # Recursively handle this library's own dependencies
                bundle_dylibs "$dest_dir/$lib_name" "$dest_dir"
            fi

            # Rewrite the reference in the binary we're processing
            install_name_tool -change "$lib" "@loader_path/$lib_name" "$binary" 2>/dev/null || true
        done < <(otool -L "$binary" 2>/dev/null | tail -n +2 | awk '{print $1}')
    }

    bundle_dylibs ffmpeg/ffmpeg ffmpeg/
    bundle_dylibs ffmpeg/ffprobe ffmpeg/
    echo "Dynamic libraries bundled."
fi
echo

# ── Step 2: Install PyInstaller ────────────────────────────────────────
if ! command -v pyinstaller &>/dev/null; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
fi
echo

# ── Step 3: Build the .app bundle ─────────────────────────────────────
echo "Building PhotoExtractor.app..."
pyinstaller \
    --noconfirm \
    --onedir \
    --windowed \
    --name "PhotoExtractor" \
    --osx-bundle-identifier "com.milehighsecure.photoextractor" \
    --add-data "ffmpeg:ffmpeg" \
    photo_extractor.py
echo

# ── Step 4: Create .dmg with Applications shortcut ────────────────────
echo "Creating PhotoExtractor.dmg..."
rm -rf dmg_staging
mkdir -p dmg_staging
cp -R dist/PhotoExtractor.app dmg_staging/
ln -s /Applications dmg_staging/Applications

rm -f dist/PhotoExtractor.dmg
hdiutil create \
    -volname "Photo Extractor" \
    -srcfolder dmg_staging \
    -ov -format UDZO \
    dist/PhotoExtractor.dmg
rm -rf dmg_staging

echo
if [ -f "dist/PhotoExtractor.dmg" ]; then
    echo "============================================"
    echo " BUILD SUCCESSFUL!"
    echo " Output: dist/PhotoExtractor.dmg"
    echo "============================================"
else
    echo "BUILD FAILED. Check output above for errors."
fi
