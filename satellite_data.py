
import json
import math
import os
from datetime import datetime, timezone, timedelta

import requests

from skyfield.api import EarthSatellite, load, wgs84


# ==========================================
# CONFIGURATION
# ==========================================

CELESTRAK_URL = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=JSON"
)

CACHE_FILE = "satellite_data.json"

# CelesTrak data should not be repeatedly downloaded.
CACHE_DURATION = timedelta(hours=2)

EARTH_RADIUS_KM = 6378.137
EARTH_MU = 398600.4418

MIN_LEO_ALTITUDE_KM = 160
MAX_LEO_ALTITUDE_KM = 2000


# ==========================================
# DOWNLOAD SATELLITE DATA
# ==========================================

def download_satellites(use_cached_data=True):

    if os.path.exists(CACHE_FILE) and use_cached_data:

        # modified = datetime.fromtimestamp(
            # os.path.getmtime(CACHE_FILE),
            # tz=timezone.utc
        # )

        # age = datetime.now(timezone.utc) - modified

        # if age < CACHE_DURATION:
            # print("Using cached CelesTrak data.")

            with open(CACHE_FILE, "r") as file:
                return json.load(file)

    print("Downloading satellite data from CelesTrak...")

    response = requests.get(
        CELESTRAK_URL,
        timeout=30,
        headers={"User-Agent": "LEO-FOV-Tracker/1.0"}
    )

    response.raise_for_status()

    satellites = response.json()

    with open(CACHE_FILE, "w") as file:
        json.dump(satellites, file)

    print(f"Downloaded {len(satellites)} orbital records.")

    return satellites


# ==========================================
# IDENTIFY LOW EARTH ORBIT SATELLITES
# ==========================================

def calculate_orbital_altitude(record):

    mean_motion = float(record["MEAN_MOTION"])
    eccentricity = float(record["ECCENTRICITY"])

    # Convert revolutions per day to radians per second.
    mean_motion_rad = (
        mean_motion * 2 * math.pi / 86400
    )

    # Approximate semi-major axis using Kepler's law.
    semi_major_axis = (
        EARTH_MU / mean_motion_rad**2
    ) ** (1 / 3)

    perigee = (
        semi_major_axis * (1 - eccentricity)
        - EARTH_RADIUS_KM
    )

    apogee = (
        semi_major_axis * (1 + eccentricity)
        - EARTH_RADIUS_KM
    )

    mean_altitude = (
        perigee + apogee
    ) / 2

    return mean_altitude, perigee, apogee


def filter_leo_satellites(records):

    leo_satellites = []

    for record in records:

        try:

            mean_altitude, perigee, apogee = (
                calculate_orbital_altitude(record)
            )

            if (
                MIN_LEO_ALTITUDE_KM
                <= mean_altitude
                <= MAX_LEO_ALTITUDE_KM
            ):

                leo_satellites.append(record)

        except (KeyError, ValueError, ZeroDivisionError):
            continue

    print(f"Identified {len(leo_satellites)} LEO satellites.")

    return leo_satellites

