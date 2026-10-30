"""
Astrophotography Command Dashboard (Dev 3: UI / alerts / auto-refresh)

Run with: streamlit run app.py
Needs Streamlit >= 1.37 (for st.fragment and st.audio autoplay)
"""

import io
import math
import struct
import wave
from datetime import datetime, timedelta

import streamlit as st

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
REFRESH_SECONDS = 5     # Task 3: how mostly the live panel reestimates its data 
ALERT_THRESHOLD = 15    # Task 2: alert when countdown is <= 15 seconds or more

st.set_page_config(page_title="Astro Command", page_icon="🔭", layout="wide")


# -----------------------------------------------------------------------
# Task 1: Night-mode styling
# (The base theme lives in .streamlit/config.toml; this CSS adds the 
#  extra touches the config file cannot do.)
# -----------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Hide bright default chrome and black */
    header[data-testid="stHeader"] { background: #720000; }
    footer { visibility: hidden; }

    /* Large countdown card */
    .count-card {
        background: #FFFF00;
        color: #FF0071;
        border: 2px solid #00005A;
        border-color: #00FF00;
        border-radius: 14px;
        padding: 1.2rem 1 rem;
        text-align: center;
        font-size: 2rem;
    }
    .count-label { font-size: 1.5rem; letter-spacing: 0.3em; opacity: 1.0; }
    .count-time  { font-size: 5rem; font-weight: 800; line-height: 1.1; }

    /* Task 2: flashing alert state (stays in the red family, never white or black) */
    .count-card.alert {
        animation: flash 0.5s steps(1, end) infinite;
    }
    @keyframes flash {
        0%, 100% { background: #FFFF00; }
        50% { background: #FF0000; }
    }
    
    /* Done state */
    .count-card.done {background: #00FF00; color: #FF0071; border-color: #00FF00}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# Audio help: builds a 3-beep WAV in memory (no files needed)
# ----------------------------------------------------------------------
@st.cache_data
def make_alert_wav(freq: int = 880, beeps: int = 3) -> bytes:
    rate = 22250
    beep_len, gap_len = int(rate * 0.30), int(rate * 0.15)
    frames = bytearray()
    for _ in range(beeps):
        for i in range(beep_len):
            sample = int(15000.0 * math.sin(2.0 * math.pi * freq * (i / rate)))
            frames.extend(struct.pack("<h", sample))
        frames += b"\x00\x00" * gap_len
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return buf.getvalue()


# ----------------------------------------------------------------------
# Plug-in point: raw variables from Dev 1 and Dev 2
# Replace these placeholder values with the real ones.
# ----------------------------------------------------------------------
def get_dev_inputs() -> dict:
    return {
        "target": "M31 Andromeda Galaxy",      # from Dev 1 (placeholder)
        "exposure_s": 120,                     # from Dev 1 (placeholder)
        "frames_total": 40,                    # from Dev 1 (placeholder)
        "altitude_deg": 54.6,                  # from Dev 2 (placeholder)
        "moon_phase": "Waning Crescent",       # from Dev 2 (placeholder)
    }


def run_calculations(data: dict, elapsed_s: float) -> dict:
    """Re-runs every refresh. Swap in the real calculation loop here."""
    frames_done = min(data["frames_total"], int(elapsed_s / data["exposure_s"]))
    return {
        "frames_done": frames_done,
        "integration_min": frames_done * data["exposure_s"] / 60,
    }


# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
if "target_time" not in st.session_state:
    st.session_state.target_time = datetime.now() + timedelta(seconds=REFRESH_SECONDS * 10 or 30) # placeholder for the real target time
    st.session_state.start_time = datetime.now()
    st.session_state.alerted = False

with st.sidebar: 
    st.header("Controls")
    sound_on = st.toggle("🔔 Enable alert sound", value=True,
                         help="Click once so the browser allows audio.")
    secs = st.number_input("Countdown length(seconds)", 10, 12000, 20, step=5)
    if st.button("Reset countdown"):
        st.session_state.start_time = datetime.now()
        st.session_state.target_time = datetime.now() + timedelta(seconds=int(secs))
        st.session_state.alert_played = False
        st.rerun()

st.title("🔭 ASTRO COMMAND")


# ----------------------------------------------------------------------
# Task 3: self-refreshing panel (reruns only this function every REFRESH_SECONDS)
# ----------------------------------------------------------------------
@st.fragment(run_every=REFRESH_SECONDS)
def live_panel():
    now = datetime.now()
    remaining = (st.session_state.target_time - now).total_seconds()
    elapsed = (now - st.session_state.start_time).total_seconds()

    data = get_dev_inputs()
    calc = run_calculations(data, elapsed)

    in_alert = 0 < remaining <= ALERT_THRESHOLD
    done = remaining <= 0

    # Countdown card (color changes dynamically)
    css_class = "done" if done else ("alert" if in_alert else "")
    shown = max(0, int(remaining))
    hh, rem = divmod(shown, 3600)
    mm, ss = divmod(rem, 60)
    label = "SEQUENCE COMPLETE" if done else ("!! T-MINUS ALERT !!" if in_alert else "T-MINUS")
    st.markdown(
        f"""
        <div class="count-card {css_class}">
            <div class="count-label">{label}</div>
            <div class="count-time">{hh:02d}:{mm:02d}:{ss:02d}</div>
            </div>
            """,
            unsafe_allow_html=True,
    )

    # Fire the sound once per countdown, when it first crosses the threshold
    if in_alert and not st.session_state.alerted:
        st.session_state.alerted = True
        if sound_on:
            st.audio(make_alert_wav(), format="audio/wav", autoplay=True)
    if remaining > ALERT_THRESHOLD:
        st.session_state.alerted = False

    # Dashboard readouts
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Target", data["target"])
    c2.metric("Altitude", f"{data['altitude_deg']}°")
    c3.metric("Frames", f"{calc['frames_done']} / {data['frames_total']}")
    c4.metric("Integration", f"{calc['integration_min']:.1f} min")
    st.caption(f"Moon phase: {data['moon_phase']}  | Auto-refresh every {REFRESH_SECONDS}s | 
               f"Last update {now:%H:%M:%S}")


live_panel()
