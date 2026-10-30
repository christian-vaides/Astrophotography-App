"""
Shared data for the Astro Command dashboard.

Dev 1 and Dev 2: replace the placeholder values below with your real 
variables or function calls. Dev 3 (UI) reads them through get_dev_inputs()
in app.py, so you never need to edit app.py.

Keep the key names the same, or tell Dev 3 if you rename or add one.
"""

# ----------------------------------------------------------------------
# Dev 1: imaging plan 
# ----------------------------------------------------------------------
TARGET = "M31 Andromeda Galaxy"   # name of the object being photographed
EXPOSURE_S = 150                  # seconds per frame
FRAMES_TOTAL = 40                 # how many frames are planned

# ----------------------------------------------------------------------
# Dev 2: sky conditions
# ----------------------------------------------------------------------
ALTITUDE_DEG = 54.6               # target height above the horizon, in degrees
MOON_PHASE = "Waning Crescent"    # text label for the moon


def get_dev_inputs() -> dict:
    """Called by app.py on every refresh. Return the latest values here.
    
    If a value alters over time (for instance altitude), calculate it
    inside this function so it is fresh each time the dashboard refreshes.
    """

    return {
        "target": TARGET,
        "exposure_s": EXPOSURE_S,
        "frames_total": FRAMES_TOTAL,
        "altitude_deg": ALTITUDE_DEG,
        "moon_phase": MOON_PHASE,
    }