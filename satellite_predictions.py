import datetime
import requests
from skyfield.api import EarthSatellite, load, wgs84


import pandas as pd

def check_future_path(satellite):
    # 1. Define the Ground Station Observer Location
    # Replace these with your own latitude, longitude, and elevation (in meters)
    # Pasadena, CA
    observer_lat = 34.1478   # North is positive, South is negative
    observer_lon = -118.1445 # East is positive, West is negative (Pasadena, CA)
    observer_elevation_m = 264.0 
    satellite_name = satellite.get('OBJECT_NAME', 'UNKNOWN')

    # 2. Fetch real-time TLE data from CelesTrak (ISS - NORAD ID: 25544)
    # norad_id = 25544
    # celestrak_url = f"https://celestrak.org{norad_id}&FORMAT=TLE"
    # 
    # print(f"Fetching TLE for NORAD ID {norad_id} from CelesTrak...")
    # response = requests.get(celestrak_url)
    # if response.status_code != 200:
    #     raise RuntimeError("Failed to fetch data from CelesTrak")
    # 
    # tle_lines = [line.strip() for line in response.text.strip().split('\n')]
    # if len(tle_lines) < 3:
    #     raise ValueError("Invalid TLE data received. Check the NORAD ID.")

    # 3. Load Skyfield timescales and initialize objects
    ts = load.timescale()
    # NOTE: What is this?
    # satellite = EarthSatellite(tle_lines[1], tle_lines[2], tle_lines[0], ts)
    satellite = EarthSatellite.from_omm(ts, satellite)

    # Define the ground station position using the WGS84 ellipsoid
    ground_station = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_elevation_m)

    # 4. Define the time window for the prediction (Every 10 minutes for the next 2 hours)
    start_time = datetime.datetime.now(datetime.timezone.utc)
    print(f"\nObserver Location: Lat {observer_lat}, Lon {observer_lon}")
    print(f"Propagating orbit starting from: {start_time}")
    print(f"{'Time (UTC)':<22} | {'Azimuth (°)':<12} | {'Elevation (°)':<13} | {'Distance (km)':<13}")
    print("-" * 70)

    data_list = []

    for minutes_ahead in range(0, 121, 10):  # Checked every 10 minutes
        current_dt = start_time + datetime.timedelta(minutes=minutes_ahead)
        t = ts.from_datetime(current_dt)

        # 5. Calculate position relative to the ground station
        difference = satellite - ground_station
        topocentric = difference.at(t)

        # 6. Extract AltAzimuth coordinates
        alt, az, distance = topocentric.altaz()

        # Optional: Highlight rows where the satellite is actually above the horizon
        visibility = "Visible" if alt.degrees > 0 else "Below Horizon"

        print(f"{current_dt.strftime('%Y-%m-%d %H:%M:%S'):<22} | "
              f"{az.degrees:>11.2f} | "
              f"{alt.degrees:>12.2f} | "
              f"{distance.km:>12.1f} ({visibility})")
        row_dict = {
                "name": satellite_name, 
                "current dt": current_dt.strftime('%Y-%m-%d %H:%M:%S'),
                "az deg": az.degrees,
                "alt deg": alt.degrees,
                "distance km": distance.km,
                "visibility": visibility,
                }
        data_list.append(row_dict)

    return pd.DataFrame(data_list)

