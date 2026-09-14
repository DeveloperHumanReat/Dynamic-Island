import os
import subprocess

class SystemEngine:
    @staticmethod
    def get_battery_info():
        """Pil yüzdesini ve şarj durumunu okur."""
        try:
            power_path = "/sys/class/power_supply"
            bats = [d for d in os.listdir(power_path) if d.startswith("BAT")]
            if not bats:
                return None
            
            bat_dir = os.path.join(power_path, bats[0])
            with open(os.path.join(bat_dir, "capacity"), "r") as f:
                capacity = int(f.read().strip())
            with open(os.path.join(bat_dir, "status"), "r") as f:
                status = f.read().strip() # Charging, Discharging, Full
                
            return {"capacity": capacity, "charging": status == "Charging"}
        except Exception:
            return None

    @staticmethod
    def get_volume():
        """PipeWire / WirePlumber (wpctl) üzerinden ses seviyesini çeker."""
        try:
            output = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], text=True).strip()
            # Örnek çıktı: "Volume: 0.45" veya "Volume: 0.45 [MUTED]"
            parts = output.split()
            vol = int(float(parts[1]) * 100)
            is_muted = "[MUTED]" in output
            return vol, is_muted
        except Exception:
            return 50, False
