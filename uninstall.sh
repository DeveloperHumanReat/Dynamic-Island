#!/usr/bin/env bash

GREEN='\030[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}==> Linux Dynamic Island Sistemden Kaldırılıyor...${NC}"

# Systemd Servisini Durdur ve Devre Dışı Bırak
systemctl --user stop dynamic-island.service 2>/dev/null || true
systemctl --user disable dynamic-island.service 2>/dev/null || true

# Dosyaları Temizle
rm -rf "$HOME/.local/share/dynamic-island"
rm -f "$HOME/.local/bin/dynamic-island"
rm -f "$HOME/.local/share/applications/dynamic-island.desktop"
rm -f "$HOME/.config/systemd/user/dynamic-island.service"

systemctl --user daemon-reload

echo -e "${GREEN}==> Uygulama sisteminizden tamamen kaldırıldı.${NC}"