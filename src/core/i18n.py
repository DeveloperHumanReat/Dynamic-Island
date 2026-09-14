import locale
from PyQt6.QtCore import QLocale

TRANSLATIONS = {
    "en": {
        "app_title": "Dynamic Island",
        "media_player": "Media Player",
        "recent_file": "Recent File",
        "clipboard": "Clipboard",
        "no_media": "No media playing",
        "battery": "Battery"
    },
    "tr": {
        "app_title": "Dinamik Ada",
        "media_player": "Medya Oynatıcı",
        "recent_file": "Son Dosya",
        "clipboard": "Pano",
        "no_media": "Medya oynatılmıyor",
        "battery": "Pil"
    }
}

class I18n:
    def __init__(self):
        # Sistem dil kodunu al (ör. "en", "tr")
        sys_lang = QLocale.system().name().split('_')[0].lower()
        self.lang = sys_lang if sys_lang in TRANSLATIONS else "en"

    def t(self, key, **kwargs):
        text = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

i18n = I18n()
