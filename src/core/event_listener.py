import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
import subprocess
import pyudev
from PyQt6.QtCore import QThread, pyqtSignal

class ClipboardListener(QThread):
    clipboard_signal = pyqtSignal(str)

    def run(self):
        last_clip = ""
        while True:
            try:
                text = ""
                res = subprocess.run(["wl-paste", "-n", "--no-newline"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0:
                    text = res.stdout
                else:
                    res_x = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=1)
                    if res_x.returncode == 0:
                        text = res_x.stdout

                if text and text.strip() and text != last_clip:
                    last_clip = text
                    self.clipboard_signal.emit(text.strip())
            except Exception:
                pass
            time.sleep(0.5)

class EventListenerThread(QThread):
    media_changed = pyqtSignal(dict)

    def run(self):
        while True:
            try:
                cmd = ["playerctl", "metadata", "--format", "{{title}}|||{{artist}}|||{{mpris:artUrl}}"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
                if res.returncode == 0 and res.stdout.strip():
                    parts = res.stdout.strip().split("|||")
                    title = parts[0].strip() if len(parts) > 0 else ""
                    artist = parts[1].strip() if len(parts) > 1 else ""
                    art_url = parts[2].strip() if len(parts) > 2 else ""
                    
                    if title:
                        self.media_changed.emit({"title": title, "artist": artist, "artUrl": art_url})
                    else:
                        self.media_changed.emit({"title": "", "artist": "", "artUrl": ""})
                else:
                    self.media_changed.emit({"title": "", "artist": "", "artUrl": ""})
            except Exception:
                self.media_changed.emit({"title": "", "artist": "", "artUrl": ""})
            time.sleep(1.2)

class HardwareEventListener(QThread):
    hud_signal = pyqtSignal(str, str, int)
    battery_status_signal = pyqtSignal(dict)
    recent_file_signal = pyqtSignal(str)

    def get_recent_file(self):
        xbel_path = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(xbel_path):
            try:
                tree = ET.parse(xbel_path)
                root = tree.getroot()
                bookmarks = root.findall("bookmark")
                valid_files = []

                for b in bookmarks:
                    href = b.attrib.get("href", "")
                    if not href.startswith("file://"):
                        continue

                    # Klasörleri ve sistem mount isimlerini (VTOYEFI vb.) filtrele
                    mime_elem = b.find(".//mime-type")
                    if mime_elem is not None:
                        m_type = mime_elem.attrib.get("type", "")
                        if m_type in ["inode/directory", "x-scheme-handler/file"]:
                            continue

                    path = urllib.parse.unquote(urllib.parse.urlparse(href).path)
                    
                    # Sadece var olan gerçek dosyaları al
                    if os.path.isfile(path):
                        filename = os.path.basename(path)
                        if filename and not filename.startswith("."):
                            timestamp = b.attrib.get("modified", b.attrib.get("visited", ""))
                            valid_files.append((timestamp, filename))

                if valid_files:
                    valid_files.sort(key=lambda x: x[0], reverse=True)
                    return valid_files[0][1]
            except Exception:
                pass
        return "Henüz dosya açılmadı"

    def run(self):
        last_vol = -1
        last_muted = False
        last_charging = None
        last_brightness = -1
        last_recent_file = ""
        first_run = True

        # PyUdev Netlink Monitor
        try:
            context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.filter_by(subsystem='block')
            monitor.filter_by(subsystem='usb')
            monitor.start()
        except Exception:
            monitor = None

        while True:
            # 1. USB Takılma / Çıkarılma Dinleyicisi
            if monitor:
                try:
                    device = monitor.poll(timeout=0.05)
                    if device is not None:
                        devtype = device.get('DEVTYPE')
                        action = device.action
                        if action == 'add' and devtype in ['partition', 'disk', 'usb_device']:
                            label = device.get('ID_FS_LABEL') or device.get('ID_MODEL') or "USB Diski"
                            self.hud_signal.emit("🔌", f"USB Takıldı: {label}", -1)
                        elif action == 'remove' and devtype in ['partition', 'disk', 'usb_device']:
                            self.hud_signal.emit("⏏️", "USB Aygıtı Çıkarıldı", -1)
                except Exception:
                    pass

            # 2. Parlaklık Dinleyicisi
            try:
                import glob
                b_files = glob.glob("/sys/class/backlight/*/brightness")
                mb_files = glob.glob("/sys/class/backlight/*/max_brightness")
                if b_files and mb_files:
                    with open(b_files[0], "r") as f:
                        cur_b = int(f.read().strip())
                    with open(mb_files[0], "r") as f:
                        max_b = int(f.read().strip())
                    b_pct = int((cur_b / max_b) * 100)
                    if not first_run and last_brightness != -1 and abs(b_pct - last_brightness) >= 2:
                        self.hud_signal.emit("☀️", f"Parlaklık: %{b_pct}", b_pct)
                        last_brightness = b_pct
                    elif first_run:
                        last_brightness = b_pct
            except Exception:
                pass

            # 3. Ses Seviyesi Dinleyicisi
            try:
                res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=0.5)
                muted_res = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=0.5)
                muted = "yes" in muted_res.stdout
                out = res.stdout
                if "/" in out:
                    vol = int(out.split("/")[1].strip().replace("%", ""))
                    if not first_run and last_vol != -1 and (vol != last_vol or muted != last_muted):
                        icon = "🔇" if muted else ("🔊" if vol > 50 else "🔉")
                        self.hud_signal.emit(icon, f"Ses: %{vol}", vol)
                    last_vol = vol
                    last_muted = muted
            except Exception:
                pass

            # 4. Batarya Durumu Dinleyicisi
            try:
                import glob
                for ps in glob.glob("/sys/class/power_supply/*"):
                    type_file = os.path.join(ps, "type")
                    if os.path.exists(type_file):
                        with open(type_file, "r") as tf:
                            if tf.read().strip().lower() != "battery":
                                continue

                    cap_file = os.path.join(ps, "capacity")
                    stat_file = os.path.join(ps, "status")
                    if os.path.exists(cap_file):
                        with open(cap_file, "r") as f:
                            pct = int(f.read().strip())
                        charging = False
                        if os.path.exists(stat_file):
                            with open(stat_file, "r") as f:
                                charging = (f.read().strip().lower() == "charging")

                        self.battery_status_signal.emit({"battery_pct": pct, "charging": charging})

                        if not first_run and last_charging is not None and charging != last_charging:
                            if charging:
                                self.hud_signal.emit("⚡", f"Şarj Takıldı (%{pct})", pct)
                            else:
                                self.hud_signal.emit("🔋", f"Şarj Söküldü (%{pct})", pct)
                        last_charging = charging
                        break
            except Exception:
                pass

            # 5. Son Dosya Kontrolü
            recent_file = self.get_recent_file()
            if recent_file != last_recent_file:
                last_recent_file = recent_file
                self.recent_file_signal.emit(recent_file)

            first_run = False
            time.sleep(0.3)
