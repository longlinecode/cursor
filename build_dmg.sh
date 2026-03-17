#!/usr/bin/env bash
# ============================================================
# build_dmg.sh  —  Build Chess.app and package it as a DMG
# Requirements (macOS only):
#   brew install python create-dmg
#   pip install pyinstaller
# ============================================================
set -euo pipefail

APP_NAME="Chess"
VERSION="1.0.0"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
BUILD_DIR="dist"
APP_PATH="${BUILD_DIR}/${APP_NAME}.app"

echo "======================================"
echo " Building ${APP_NAME} v${VERSION}"
echo "======================================"

# ── 1. Install Python dependencies ──────────────────────────
echo "→ Checking dependencies..."
pip install pyinstaller --quiet

# ── 2. Build .app with PyInstaller ──────────────────────────
echo "→ Running PyInstaller..."
pyinstaller chess.spec --noconfirm --clean

if [ ! -d "${APP_PATH}" ]; then
    echo "✗ Build failed: ${APP_PATH} not found"
    exit 1
fi
echo "✓ ${APP_PATH} created"

# ── 3. Create DMG with create-dmg ───────────────────────────
echo "→ Creating DMG..."

# Check if create-dmg is available
if ! command -v create-dmg &>/dev/null; then
    echo "  create-dmg not found. Falling back to hdiutil..."
    # Fallback: plain hdiutil approach
    STAGING_DIR="dmg_staging"
    rm -rf "${STAGING_DIR}"
    mkdir "${STAGING_DIR}"
    cp -r "${APP_PATH}" "${STAGING_DIR}/"
    # create a symlink to /Applications
    ln -s /Applications "${STAGING_DIR}/Applications"

    hdiutil create \
        -volname "${APP_NAME}" \
        -srcfolder "${STAGING_DIR}" \
        -ov \
        -format UDZO \
        "${DMG_NAME}"

    rm -rf "${STAGING_DIR}"
else
    # Preferred: create-dmg (prettier installer window)
    rm -f "${DMG_NAME}"
    create-dmg \
        --volname "${APP_NAME}" \
        --volicon "${APP_PATH}/Contents/Resources/Chess.icns" 2>/dev/null || true \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 175 190 \
        --hide-extension "${APP_NAME}.app" \
        --app-drop-link 425 190 \
        --no-internet-enable \
        "${DMG_NAME}" \
        "${BUILD_DIR}/"
fi

echo ""
echo "======================================"
echo " Done!  →  ${DMG_NAME}"
echo "======================================"
