#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.local/share/dynamic-island"
BIN_DIR="$HOME/.local/bin"
SERVICE_DIR="$HOME/.config/systemd/user"

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$SERVICE_DIR"
cp -r src data requirements.txt "$INSTALL_DIR/"

python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip > /dev/null
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" > /dev/null

# KDE KWin Görev Çubuğu ve Panel Gizleme Kuralı
KWIN_CONFIG="$HOME/.config/kwinrulesrc"
if [ -f "$KWIN_CONFIG" ]; then
    if ! grep -q "dynamic-island-overlay" "$KWIN_CONFIG"; then
        cat << 'KWIN_EOF' >> "$KWIN_CONFIG"

[DynamicIslandRule]
Description=Dynamic Island Rule
title=dynamic-island-overlay
titlematch=1
skiptaskbar=true
skiptaskbarrule=2
skippager=true
skippagerrule=2
skipswitcher=true
skipswitcherrule=2
above=true
aboverule=2
focusable=false
focusablerule=2
KWIN_EOF
        qdbus6 org.kde.KWin /KWin reconfigure 2>/dev/null || qdbus org.kde.KWin /KWin reconfigure 2>/dev/null || true
    fi
fi

rm -rf "$BIN_DIR/dynamic-island"
cat << 'OUTER_EOF' > "$BIN_DIR/dynamic-island"
#!/usr/bin/env bash
INSTALL_DIR="$HOME/.local/share/dynamic-island"

export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export QT_QPA_PLATFORM="wayland;xcb"

cd "$INSTALL_DIR"
export PYTHONPATH="$INSTALL_DIR:$PYTHONPATH"

exec "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/src/main.py" "$@"
OUTER_EOF
chmod +x "$BIN_DIR/dynamic-island"

cp data/dynamic-island.service "$SERVICE_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now dynamic-island.service
