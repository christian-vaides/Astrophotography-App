import os
import time
import requests
from datetime import datetime

class DataManager:
    def __init__(self, cache_file="tle_cache.txt", fallback_file="offline_fallback_tles.txt"):
        self.cache_file = cache_file
        self.fallback_file = fallback_file
        # Fixed live URL endpoint from CelesTrak (Task 1)
        self.tle_url = "https://celestrak.org"

    def fetch_live_tles(self) -> bool:
        """Attempts to pull fresh data from CelesTrak. Returns True if successful."""
        try:
            response = requests.get(self.tle_url, timeout=5)
            if response.status_code == 200 and len(response.text) > 100:
                with open(self.cache_file, "w") as f:
                    f.write(response.text)
                return True
            return False
        except (requests.RequestException, Exception):
            return False

    def load_tles(self) -> list:
        """
        Loads raw data lines from cache or fallback, and filters them 
        to only keep large, bright, highly trackable objects.
        """
        # Task 1: Check cache age and fetch updates automatically
        cache_exists = os.path.exists(self.cache_file)
        cache_expired = cache_exists and (time.time() - os.path.getmtime(self.cache_file) > 86400)
        
        if not cache_exists or cache_expired:
            self.fetch_live_tles()
            
        raw_lines = []
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                raw_lines = f.readlines()

        # Task 1 Offline Fallback: If cache is empty or missing, read local asset
        if not raw_lines and os.path.exists(self.fallback_file):
            with open(self.fallback_file, "r") as f:
                raw_lines = f.readlines()

        # =========================================================================
        # TASK 2 IMPLEMENTATION: Satellite Filtering
        # Loops through the TLE data triplets and strips out faint space debris.
        # Keeps Starlink, OneWeb, ISS, Tiangong, and bright science satellites (HST).
        # =========================================================================
        filtered_lines = []
        i = 0
        while i < len(raw_lines) - 2:
            # Verify it's a valid 3-line TLE format block (Name, Line 1, Line 2)
            if raw_lines[i+1].startswith('1 ') and raw_lines[i+2].startswith('2 '):
                name = raw_lines[i].strip().upper()
                line1 = raw_lines[i+1]
                line2 = raw_lines[i+2]
                
                # Keywords for major highly reflective constellations or structures
                is_starlink = "STARLINK" in name
                is_oneweb = "ONEWEB" in name
                is_station = "ISS" in name or "ZARYA" in name or "TIANGONG" in name
                is_science = "HST" in name or "HUBBLE" in name or "NOAA" in name
                
                if is_starlink or is_oneweb or is_station or is_science:
                    filtered_lines.extend([raw_lines[i], line1, line2])
                i += 3
            else:
                i += 1
                
        return filtered_lines

    # =========================================================================
    # TASK 3 IMPLEMENTATION: Data Age Status Indicator
    # Returns a user-friendly timestamp showing how old your satellite data is.
    # =========================================================================
    def get_data_age_string(self) -> str:
        """Returns a string indicating exactly when your satellite database was updated."""
        if os.path.exists(self.cache_file):
            mod_time = os.path.getmtime(self.cache_file)
            last_update = datetime.fromtimestamp(mod_time)
            return f"🟢 Data updated on: {last_update.strftime('%Y-%m-%d %H:%M:%S')} (Local Time)"
        elif os.path.exists(self.fallback_file):
            return "⚠️ Running on OFFLINE Baseline Fallback Data (No internet)"
        return "❌ No satellite telemetry data found"