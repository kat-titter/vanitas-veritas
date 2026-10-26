#!/bin/bash
# sink.sh: run vanitas on its own Mac mini, for good. The spring and the screen start at login and come back if they stop.
#   bash code/sink.sh install     start now and at every login (needs Google Chrome in /Applications; asks for the
#                                 password once, to keep the Mac awake and start it again after a power cut)
#   bash code/sink.sh status      is it running? the last lines the spring wrote
#   bash code/sink.sh restart     stop and start both
#   bash code/sink.sh remove      stop, and no longer start at login
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd); PY="$ROOT/.venv/bin/python"; LA="$HOME/Library/LaunchAgents"; LOG="$HOME/Library/Logs/vanitas"
SPRING=vanitas.veritas.spring; SCREEN=vanitas.veritas.screen
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p "$LA" "$LOG"

plist() {  # label, then the program and its arguments
  local label=$1; shift
  { echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
    echo "<plist version=\"1.0\"><dict><key>Label</key><string>$label</string><key>ProgramArguments</key><array>"
    for a in "$@"; do printf '<string>%s</string>' "$(printf '%s' "$a" | sed 's/&/\&amp;/g')"; done
    echo "</array><key>RunAtLoad</key><true/><key>KeepAlive</key><true/><key>ThrottleInterval</key><integer>10</integer>"
    echo "<key>WorkingDirectory</key><string>$ROOT</string>"
    echo "<key>StandardOutPath</key><string>$LOG/$label.log</string><key>StandardErrorPath</key><string>$LOG/$label.log</string>"
    echo "</dict></plist>"; } > "$LA/$label.plist"
}

case "${1:-}" in
  install)
    [ -x "$PY" ] || { echo "Run bash code/setup_sink.sh first."; exit 1; }
    [ -x "$CHROME" ] || { echo "Install Google Chrome into /Applications first."; exit 1; }
    mkdir -p spring_feed; [ -s spring_feed/key ] || "$PY" -c "import secrets; print(secrets.token_urlsafe(18))" > spring_feed/key
    KEY=$(tr -d '[:space:]' < spring_feed/key)   # the same key the spring reads: only this screen may send the camera's frame
    URL="http://127.0.0.1:8770/sync.html?spring=feed/&sink&camera&key=$KEY"
    sudo pmset -a sleep 0 disksleep 0 autorestart 1   # never sleep; power back on by itself when the power returns
    plist $SPRING /usr/bin/caffeinate -dims "$PY" code/sink.py --public
    plist $SCREEN /bin/bash -c "until curl -sf http://127.0.0.1:8770/feed/now.json >/dev/null || curl -sf http://127.0.0.1:8770/ >/dev/null; do sleep 2; done; exec \"$CHROME\" --kiosk --noerrdialogs --disable-session-crashed-bubble --disable-infobars --no-first-run --autoplay-policy=no-user-gesture-required --use-fake-ui-for-media-stream --user-data-dir=\"$HOME/.vanitas-chrome\" \"$URL\""
    for l in $SPRING $SCREEN; do launchctl bootout gui/$(id -u)/$l 2>/dev/null || true; launchctl bootstrap gui/$(id -u) "$LA/$l.plist"; done
    echo "Installed. The screen opens when the spring answers (about a minute). Logs: $LOG"
    echo "Last step, by hand: System Settings > Users & Groups > Automatically log in as this user (FileVault must be off)." ;;
  status)
    for l in $SPRING $SCREEN; do launchctl print gui/$(id -u)/$l 2>/dev/null | grep -E '^\s*(state|pid) =' | sed "s/^/$l: /" || echo "$l: not installed"; done
    tail -n 5 "$LOG/$SPRING.log" 2>/dev/null || true ;;
  restart)
    for l in $SPRING $SCREEN; do launchctl kickstart -k gui/$(id -u)/$l; done; echo "Restarted." ;;
  remove)
    for l in $SPRING $SCREEN; do launchctl bootout gui/$(id -u)/$l 2>/dev/null || true; rm -f "$LA/$l.plist"; done; echo "Removed." ;;
  *) sed -n '2,7p' "$0" ;;
esac
