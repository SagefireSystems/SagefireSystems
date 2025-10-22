import os
import time
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
from typing import Optional
import requests
import markdown2

# Optional OpenAI SDK v1
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "exports"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Load prompts
PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "diagnostic_system.txt").read_text(encoding="utf-8")
INSTRUCTIONS_TMPL = (PROMPTS_DIR / "diagnostic_instructions.txt").read_text(encoding="utf-8")

st.set_page_config(page_title="SAGEFIRE Reflex Engine", layout="wide")
st.title("🜂 SAGEFIRE Reflex Engine — Educational Diagnostic")
st.caption("Paste any conversation/transcript and generate a professional deep-dive diagnostic (with Trio + Handler).")

with st.sidebar:
    st.header("Run Settings")
    provider = st.radio("Provider", ["OpenAI", "Ollama"], index=0 if OPENAI_API_KEY else 1)
    if provider == "OpenAI":
        model = st.text_input("OpenAI Model", value=DEFAULT_OPENAI_MODEL, help="e.g., gpt-4o-mini, gpt-4o, etc.")
        api_key = st.text_input("OPENAI_API_KEY", value=OPENAI_API_KEY, type="password")
    else:
        model = st.text_input("Ollama Model", value=OLLAMA_MODEL or "llama3")
        api_key = ""

    st.markdown("---")
    note_title = st.text_input("Note Title", value="Deep Educational Diagnostic")
    author = st.text_input("Author", value="Gabe Haddad")
    run_button = st.button("Run Diagnostic", type="primary", use_container_width=True)

st.subheader("Input")
input_mode = st.radio("Provide transcript as:", ["Paste text", "Upload .txt"], horizontal=True)
transcript_text = ""
if input_mode == "Paste text":
    transcript_text = st.text_area("Transcript / Conversation Text", height=260, placeholder="Paste here…")
else:
    uploaded = st.file_uploader("Upload a .txt transcript", type=["txt"])
    if uploaded:
        transcript_text = uploaded.read().decode("utf-8")

def call_openai(system_prompt: str, user_prompt: str, model_name: str, key: str) -> str:
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK not installed. Check requirements.txt")
    client = OpenAI(api_key=key if key else None)
    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=2000,
    )
    return resp.choices[0].message.content

def call_ollama(system_prompt: str, user_prompt: str, model_name: str) -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "options": {"temperature": 0.2}
    }
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    # Ollama may stream; handle both streaming and non-streaming
    if r.headers.get("Content-Type", "").startswith("application/x-ndjson"):
        text = ""
        for line in r.iter_lines():
            if not line:
                continue
            try:
                j = json.loads(line)
                text += j.get("message", {}).get("content", "")
            except Exception:
                pass
        return text
    else:
        j = r.json()
        return j.get("message", {}).get("content", "")

def render_markdown(md: str):
    # Convert to HTML for nicer display in Streamlit (still safe subset)
    html = markdown2.markdown(md, extras=["tables", "fenced-code-blocks"])
    st.markdown(html, unsafe_allow_html=True)

def export_to_obsidian(md: str, title: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
    filename = f"{timestamp} — {safe_title}.md"
    out_path = OUTPUT_DIR / filename
    out_path.write_text(md, encoding="utf-8")
    return out_path

analysis_md = ""

if run_button:
    if not transcript_text.strip():
        st.error("Please provide a transcript.")
    else:
        with st.spinner("Generating diagnostic…"):
            final_user_prompt = INSTRUCTIONS_TMPL.format(transcript=transcript_text.strip())
            try:
                if provider == "OpenAI":
                    if not (api_key or OPENAI_API_KEY):
                        st.error("Please provide OPENAI_API_KEY in the sidebar or .env")
                    else:
                        analysis_md = call_openai(SYSTEM_PROMPT, final_user_prompt, model, api_key or OPENAI_API_KEY)
                else:
                    analysis_md = call_ollama(SYSTEM_PROMPT, final_user_prompt, model)
            except Exception as e:
                st.exception(e)
                analysis_md = ""

        if analysis_md:
            st.success("Diagnostic generated.")
            st.subheader("Output")
            render_markdown(analysis_md)
            colA, colB = st.columns(2)
            with colA:
                if st.button("Export to Obsidian", use_container_width=True):
                    path = export_to_obsidian(analysis_md, note_title)
                    st.success(f"Saved to {path}")
                    st.download_button("Download Markdown", data=analysis_md, file_name=path.name, mime="text/markdown", use_container_width=True)
            with colB:
                st.download_button("Download Raw Markdown", data=analysis_md, file_name="diagnostic.md", mime="text/markdown", use_container_width=True)

st.markdown("---")
st.caption("Tip: You can fine-tune the prompts under ./prompts for domain-specific analyses (lab SOPs, politics, audio engineering, etc.).")
