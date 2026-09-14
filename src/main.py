import sys
from PyQt6.QtWidgets import QApplication
from src.core.window_engine import WindowEngine
from src.ui.island_widget import DynamicIslandWidget
from src.core.event_listener import EventListenerThread, HardwareEventListener, ClipboardListener
from src.core.i18n import i18n

def main():
    app = QApplication(sys.argv)

    island = DynamicIslandWidget()
    WindowEngine.apply_window_flags(island)

    # 1. Medya Dinleyicisi
    media_thread = EventListenerThread()
    media_thread.media_changed.connect(island.update_media)
    media_thread.start()

    # 2. Donanım ve USB / Son Dosya Dinleyicisi
    hw_thread = HardwareEventListener()
    hw_thread.hud_signal.connect(island.trigger_hud_toast)
    hw_thread.battery_status_signal.connect(
        lambda data: island.status_label.setText(f"%{data['battery_pct']}")
    )
    hw_thread.recent_file_signal.connect(
        lambda fname: island.recent_file_label.setText(f"📄 {i18n.t('recent_file')}: {fname}")
    )
    hw_thread.start()

    # 3. Pano Dinleyicisi
    clip_thread = ClipboardListener()
    clip_thread.clipboard_signal.connect(
        lambda text: island.trigger_hud_toast("📋", f"{i18n.t('clipboard')}: {text[:20]}...", -1)
    )
    clip_thread.start()

    island.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
