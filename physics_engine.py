import datetime
from skyfield.api import Topos, load, EarthSatellite, Angle

class PhysicsEngine:
    def __init__(self):
        # Load standard astronomical models
        self.timescale = load.timescale()
        
        # Deep-sky target registry with RA (Hours) and Dec (Degrees) coordinates
        self.historical_events = [
            {"name": "Messier 42 (The Orion Nebula)", "ra": 5.58, "dec": -5.38, "radius": 3.0, "fact": "First photographed in 1880 by Henry Draper, marking the birth of deep-space astrophotography!"},
            {"name": "Messier 31 (The Andromeda Galaxy)", "ra": 0.73, "dec": 41.27, "radius": 4.0, "fact": "In 1923, Edwin Hubble discovered a Cepheid variable star here, proving that other galaxies exist outside the Milky Way."},
            {"name": "Messier 45 (The Pleiades)", "ra": 3.79, "dec": 24.12, "radius": 4.0, "fact": "This spectacular star cluster is mentioned in Homer's Odyssey; Galileo was the first to view its true abundance through a telescope."},
            {"name": "Crab Nebula (Messier 1)", "ra": 5.58, "dec": 22.01, "radius": 2.0, "fact": "The remnant of a massive supernova recorded by Chinese astronomers in 1054 AD. It was bright enough to see in daylight!"}
        ]

    def _parse_tles(self, raw_lines) -> list:
        """Parses a text stream into active Skyfield objects."""
        satellites = []
        clean = [l.strip() for l in raw_lines if l.strip()]
        i = 0
        while i < len(clean) - 2:
            if clean[i+1].startswith('1 ') and clean[i+2].startswith('2 '):
                try:
                    satellites.append(EarthSatellite(clean[i+1], clean[i+2], clean[i], self.timescale))
                except Exception: 
                    pass
                i += 3
            else: 
                i += 1
        return satellites

    def compute_shutter_safety(self, lat, lon, az, alt, fov, raw_tle_lines) -> dict:
        """
        Runs a predictive look-ahead using separation logic.
        Tracks how many satellites are being screened.
        """
        satellites = self._parse_tles(raw_tle_lines)
        total_sats = len(satellites) 

        if not satellites:
            return {"status": "GREEN", "countdown_seconds": 900, "sat_count": 0}

        observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
        now = datetime.datetime.now(datetime.timezone.utc)
        critical_radius = fov / 2.0

        for offset in range(0, 900, 2):
            t = self.timescale.from_datetime(now + datetime.timedelta(seconds=offset))
            
            for sat in satellites:
                difference = sat - observer
                topocentric = difference.at(t)
                sat_alt, sat_az, _ = topocentric.altaz()
                
                if sat_alt.degrees > 0:
                    alt_diff = abs(alt - sat_alt.degrees)
                    az_diff = abs(az - sat_az.degrees)
                    if az_diff > 180:
                        az_diff = 360 - az_diff
                        
                    angular_separation = (alt_diff**2 + az_diff**2)**0.5
                    
                    if angular_separation <= critical_radius:
                        return {
                            "status": "RED", 
                            "countdown_seconds": offset,
                            "sat_count": total_sats
                        }
                        
        return {"status": "GREEN", "countdown_seconds": 900, "sat_count": total_sats}

    def fetch_sky_history(self, lat, lon, az, alt) -> str:
        """Maps your camera pointing coordinates directly to our historical database matrix."""
        observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
        t = self.timescale.from_datetime(datetime.datetime.now(datetime.timezone.utc))
        pos = observer.at(t).from_altaz(Angle(degrees=alt), Angle(degrees=az))
        ra, dec, _ = pos.radec()
        
        for event in self.historical_events:
            if abs(ra.hours - event["ra"]) <= (event["radius"] / 15.0) and abs(dec.degrees - event["dec"]) <= event["radius"]:
                return f"🌟 **Targeting near {event['name']}**\n\n**Astro-History:** {event['fact']}\n\n*(Calculated Space Address: RA {ra.hours:.2f}h, Dec {dec.degrees:.1f}°)*"
                
        return f"🌌 **Deep Space Target Vector**\n\nNo major historical spaceflight or astronomical discoveries cataloged here.\n\n*(Calculated Space Address: RA {ra.hours:.2f}h, Dec {dec.degrees:.1f}°)*"