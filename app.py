import streamlit as st

st.set_page_config(
    page_title="Reflex Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚙️ Reflex Engine")
st.subheader("Human–AI workflow cockpit (starter template)")

st.markdown(
    """
Welcome! This is a minimal, **batteries-included** starter for your Reflex Engine.
Use the sidebar to switch pages:
- **🧠 Daily Workflow** — plan your day and capture quick logs.
- **📦 Obsidian Exporter** — generate Obsidian‑ready Markdown with YAML front matter.
- **🎤 Overtone Analyzer** — upload a WAV/FLAC file and get simple spectral diagnostics.

> Tip: This is a scaffold — keep what you like, delete the rest, and extend!
    """
)

st.info(
    "Secrets (API keys, etc.) can be stored in `.streamlit/secrets.toml`. "
    "See README for details. This template does not require any keys."
)

st.caption("Reflex Engine • Streamlit template • v0.1")
