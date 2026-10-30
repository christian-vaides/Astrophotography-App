
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
    "https://celestrak.org/NORAD/elements/"
    "gp.php?GROUP=active&FORMAT=JSON"
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

def download_satellites():

    if os.path.exists(CACHE_FILE):

        modified = datetime.fromtimestamp(
            os.path.getmtime(CACHE_FILE),
            tz=timezone.utc
        )

        age = datetime.now(timezone.utc) - modified

        if age < CACHE_DURATION:
            print("Using cached CelesTrak data.")

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


# ==========================================
# FIELD OF VIEW CALCULATION
# ==========================================

def angular_separation(
    target_azimuth,
    target_elevation,
    satellite_azimuth,
    satellite_elevation
):

    # Convert degrees to radians.
    az1 = math.radians(target_azimuth)
    el1 = math.radians(target_elevation)

    az2 = math.radians(satellite_azimuth)
    el2 = math.radians(satellite_elevation)

    # Spherical angular separation.
    cosine = (
        math.sin(el1) * math.sin(el2)
        +
        math.cos(el1) * math.cos(el2)
        * math.cos(az2 - az1)
    )

    cosine = max(-1.0, min(1.0, cosine))

    return math.degrees(math.acos(cosine))


def is_in_fov(
    target_azimuth,
    target_elevation,
    satellite_azimuth,
    satellite_elevation,
    field_of_view
):

    separation = angular_separation(
        target_azimuth,
        target_elevation,
        satellite_azimuth,
        satellite_elevation
    )

    # FOV is the full angular diameter.
    return separation <= field_of_view / 2, separation


# ==========================================
# SATELLITE POSITION CALCULATION
# ==========================================

def check_satellites(
    records,
    latitude,
    longitude,
    target_azimuth,
    target_elevation,
    field_of_view
):

    ts = load.timescale()

    current_time = datetime.now(timezone.utc)
    t = ts.from_datetime(current_time)

    observer = wgs84.latlon(
        latitude_degrees=latitude,
        longitude_degrees=longitude
    )

    visible_satellites = []

    for record in records:

        try:

            satellite = EarthSatellite.from_omm(
                ts,
                record
            )

            # Calculate satellite position relative to observer.
            difference = satellite - observer

            topocentric = difference.at(t)

            elevation, azimuth, distance = (
                topocentric.altaz()
            )

            satellite_azimuth = azimuth.degrees
            satellite_elevation = elevation.degrees

            # Ignore satellites below the horizon.
            if satellite_elevation <= 0:
                continue

            inside, separation = is_in_fov(
                target_azimuth,
                target_elevation,
                satellite_azimuth,
                satellite_elevation,
                field_of_view
            )

            if inside:

                visible_satellites.append(record)
                # visible_satellites.append({
                #     "name": record.get(
                #         "OBJECT_NAME", "Unknown"
                #     ),

                #     "norad_id": record.get(
                #         "NORAD_CAT_ID", "Unknown"
                #     ),

                #     "azimuth": satellite_azimuth,

                #     "elevation": satellite_elevation,

                #     "distance_km": distance.km,

                #     "separation": separation
                # })

        except Exception as error:
            print(
                f"Skipping {record.get('OBJECT_NAME', 'Unknown')}: "
                f"{error}"
            )

    return visible_satellites


# ==========================================
# MAIN APPLICATION
# ==========================================

def main():

    print("\n===================================")
    print("       LEO SATELLITE TRACKER")
    print("===================================\n")

    # Observer coordinates.
    # latitude = float(input("Observer latitude: "))
    # longitude = float(input("Observer longitude: "))


    latitude = 34.1478   # North is positive, South is negative
    longitude = -118.1445 # East is positive, West is negative (Pasadena, CA)
    observer_elevation_m = 264.0 

    # Target pointing coordinates.
    # target_azimuth = float(input("Target azimuth (degrees): "))
    # target_elevation = float(input("Target altitude/elevation (degrees): "))
    target_azimuth = 180
    target_elevation = 45

    # Full angular diameter of the FOV.
    # field_of_view = float(input("Field of view (degrees): "))
    field_of_view = 20

    if not (-90 <= latitude <= 90):
        raise ValueError("Latitude must be between -90 and 90.")

    if not (-180 <= longitude <= 180):
        raise ValueError("Longitude must be between -180 and 180.")

    if not (0 <= target_azimuth < 360):
        raise ValueError("Azimuth must be between 0 and 360.")

    if not (-90 <= target_elevation <= 90):
        raise ValueError("Elevation must be between -90 and 90.")

    if not (0 < field_of_view <= 360):
        raise ValueError("FOV must be greater than 0 and at most 360.")

    # Retrieve orbital data.
    all_satellites = download_satellites()

    # Filter for LEO satellites.
    leo_satellites = filter_leo_satellites(
        all_satellites
    )

    # NOTE: potentially move this function into another file
    # Determine which satellites are inside the FOV.
    results = check_satellites(
        leo_satellites,
        latitude,
        longitude,
        target_azimuth,
        target_elevation,
        field_of_view
    )

    # for every satelitte in the field of view,
    # we want to know if it will stay in the field of view for the newwt 2 hours evry 10 minutes
    if not results:
        pass
    else:
        for satellite in results:
            import satellite_predictions as sp
            stay_in_fov: bool = sp.check_future(satellite)
            if stay_in_fov:
                print('satellite stays in field of vision')

    # Display results.
    # print("\n===================================")
    # print("         FOV DETECTION RESULTS")
    # print("===================================\n")

    # if not results:

    #     print("No LEO satellites currently detected in FOV.")

    # else:

    #     results.sort(
    #         key=lambda satellite: satellite["separation"]
    #     )

    #     for satellite in results:

    #         print(f"Satellite: {satellite['name']}")
    #         print(f"NORAD ID: {satellite['norad_id']}")

    #         print(
    #             f"Azimuth: {satellite['azimuth']:.2f} degrees"
    #         )

    #         print(
    #             f"Elevation: {satellite['elevation']:.2f} degrees"
    #         )

    #         print(
    #             f"Distance: {satellite['distance_km']:.2f} km"
    #         )

    #         print(
    #             f"Angular separation: "
    #             f"{satellite['separation']:.3f} degrees"
    #         )

    #         print("-----------------------------------")

    #     print(f"\nTotal satellites inside FOV: {len(results)}")


if __name__ == "__main__":
    main()

