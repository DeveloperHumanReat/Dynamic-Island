import subprocess

class DBusEngine:
    def __init__(self):
        self.sudo_password = None

    def verify_sudo(self, password: str) -> bool:
        cmd = subprocess.run(
            ["sudo", "-S", "-v"],
            input=f"{password}\n",
            text=True,
            capture_output=True
        )
        return cmd.returncode == 0

    def get_media_info(self):
        """Aktif oynatıcıdan şarkı ve sanatçı bilgisini çeker."""
        try:
            artist = subprocess.check_output(
                ["playerctl", "metadata", "artist"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            title = subprocess.check_output(
                ["playerctl", "metadata", "title"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            status = subprocess.check_output(
                ["playerctl", "status"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            return {"artist": artist, "title": title, "status": status}
        except Exception:
            return None

    def play_pause(self):
        subprocess.run(["playerctl", "play-pause"], stderr=subprocess.DEVNULL)

    def next_track(self):
        subprocess.run(["playerctl", "next"], stderr=subprocess.DEVNULL)

    def prev_track(self):
        subprocess.run(["playerctl", "previous"], stderr=subprocess.DEVNULL)
