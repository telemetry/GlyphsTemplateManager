#!/bin/sh
# Install (copy) the plugin into the Glyphs Plugins folder.
# A copy is used instead of a symlink: macOS privacy protection (TCC) blocks
# Glyphs from following symlinks into Desktop/Documents/Downloads.
set -e

BUNDLE="TemplateManager.glyphsPlugin"
SRC="$(cd "$(dirname "$0")" && pwd)/$BUNDLE"

SUPPORT="$HOME/Library/Application Support/Glyphs 3"
DEST_DIR="$SUPPORT/Plugins"
mkdir -p "$DEST_DIR"
DEST="$DEST_DIR/$BUNDLE"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"
rm -rf "$DEST/Contents/Resources/__pycache__"
echo "Installed to: $DEST"

echo "Done. Quit (⌘Q) and relaunch Glyphs to load the plugin."
