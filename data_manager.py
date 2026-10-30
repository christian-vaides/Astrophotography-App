import os
import time
import requests

class DataManager:
    def __init__(self, cache_file="tle_cache.txt", fallback_file="offline_fallback_tles.txt"):
        self.cache_file = cache_file
        self.fallback_file = fallback_file
        # Live active satellites URL endpoint from CelesTrak
        self.tle_url = "https://celestrak.org"

    def fetch_live_tles(self) -> bool:
        """Attempts to pull fresh data from CelesTrak. Returns True if successful."""
        try:
            # Short timeout so the app doesn't hang indefinitely if cell signal is poor
            response = requests.get(self.tle_url, timeout=5)
            if response.status_code == 200 and len(response.text) > 100:
                with open(self.cache_file, "w") as f:
                    f.write(response.text)
                return True
            return False
        except (requests.RequestException, Exception):
            # Gracefully handle missing internet or server timeouts without crashing
            return False

    def load_tles(self) -> list:
        """
        UPGRADED LOGIC: Tries to get fresh data, uses cache if network fails,
        and falls back to hardcoded asset files if completely stranded offline.
        """
        cache_exists = os.path.exists(self.cache_file)
        cache_expired = cache_exists and (time.time() - os.path.getmtime(self.cache_file) > 86400)
        
        if not cache_exists or cache_expired:
            self.fetch_live_tles()
            
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                lines = f.readlines()
                if len(lines) > 0:
                    return lines

        if os.path.exists(self.fallback_file):
            with open(self.fallback_file, "r") as f:
                return f.readlines()

        return []
