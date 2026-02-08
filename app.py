import hashlib
import json
import re

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Medical Transcript Splitter", layout="wide")

# --- CONFIGURARE ȘI LOGICĂ ---

SYSTEM_INSTRUCTIONS = """
ROLE:
You are an expert medical content analyst, academic editor, and medical educator.

OBJECTIVE:
Transform the provided raw transcript into a structured, high-quality medical course chapter,
as if it were part of a professional medical textbook or a PDF course handout.

LANGUAGE:
Keep the output strictly in the ORIGINAL LANGUAGE of the transcript (French).

CORE TASKS:
Remove noise (repetitions, hesitations, irrelevant digressions).
Preserve ALL medically relevant details, mechanisms, examples, and clinical reasoning.
Reorganize the content into a clear didactic structure optimized for learning.
Do NOT summarize excessively or oversimplify.

STRUCTURE REQUIREMENTS:
Organize the content as a textbook chapter using:
- Title of the chapter (If this is the first part)
- Logical sections and subsections (H2 / H3 style)
- Use bullet points ONLY when they improve clarity
- Bold key concepts, definitions, and take-home ideas

PEDAGOGICAL OPTIMIZATION:
- Explicitly define important terms when first introduced
- Highlight cause-effect relationships and clinical reasoning

CONSTRAINTS:
- Do NOT invent information not present in the transcript
- Do NOT reference guidelines not mentioned
- No emojis, no casual tone.
- FINAL OUTPUT: A clean, structured, textbook-level medical course chapter.
"""

def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def clean_transcript(text: str) -> str:
    """
    Elimină timestamp-urile și spațiile inutile.
    """
    if not text:
        return ""
    timestamp_pattern = r"\(\d{1,2}:\d{2}(?::\d{2})?\)"
    text = re.sub(timestamp_pattern, " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def split_text_into_chunks(text: str, max_chars: int) -> list[str]:
    """
    Împarte textul în bucăți care nu depășesc max_chars, fără a tăia cuvintele la jumătate.
    """
    if not text:
        return []

    words = text.split()
    chunks: list[str] = []
    current = ""

    def flush_current():
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    for w in words:
        if len(w) > max_chars:
            flush_current()
            for start in range(0, len(w), max_chars):
                chunks.append(w[start : start + max_chars])
            continue

        candidate = w if not current else f"{current} {w}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            flush_current()
            current = w

    flush_current()
    return chunks

def build_prompt(idx: int, total: int, chunk: str) -> str:
    if idx == 1:
        return (
            f"{SYSTEM_INSTRUCTIONS}\n\n"
            f"INPUT TEXT (PART {idx}/{total}):\n"
            f"{chunk}\n\n"
            "INSTRUCTIONS FOR THIS PART:\n"
            "- Start writing the textbook chapter now based ONLY on this part.\n"
            "- Use H2/H3 headings, bold key terms, and keep a clean textbook style.\n"
            "- Do not invent information.\n"
            "- If the content feels incomplete, stop naturally and continue in the next parts.\n"
        )
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        "CONTEXT:\n"
        "We are continuing the SAME textbook chapter. Previous parts have already been processed.\n\n"
        f"INPUT TEXT (PART {idx}/{total}):\n"
        f"{chunk}\n\n"
        "INSTRUCTIONS FOR THIS PART:\n"
        "- CONTINUE from where you left off.\n"
        "- Do NOT create a new Title or a new Introduction.\n"
        "- Maintain the SAME formatting (H2/H3, bolding, bullet rules).\n"
        "- Treat this as a direct continuation of the same chapter.\n"
        "- Do not repeat already-covered content unless needed for clarity.\n"
    )

def copy_button(text_to_copy: str, label: str, dom_id: str) -> None:
    """
    Renders a compact HTML button that copies text via JS.
    """
    payload = json.dumps(text_to_copy)
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", dom_id)

    html = f"""
    <div style="display:flex;align-items:center;gap:10px;margin:0;padding:0;">
      <button id="{safe_id}"
              style="
                border:1px solid #d0d0d0;
                padding:8px 16px;
                border-radius:8px;
                background:#f0f2f6;
                color:#31333F;
                font-weight:600;
                cursor:pointer;
                font-size:14px;
                line-height:1.5;
                transition: background 0.2s;
              "
              onmouseover="this.style.background='#e0e2e6'"
              onmouseout="this.style.background='#f0f2f6'"
      >
        {label}
      </button>
      <span id="{safe_id}_msg" style="font-size:13px;color:#00cc66;font-weight:bold;line-height:1;"></span>
    </div>

    <script>
      (function() {{
        const btn = document.getElementById("{safe_id}");
        const msg = document.getElementById("{safe_id}_msg");
        if (!btn) return;

        const originalText = btn.innerText;

        btn.addEventListener("click", async () => {{
          try {{
            await navigator.clipboard.writeText({payload});
            msg.textContent = "✅ Copiat!";
            setTimeout(() => {{
              msg.textContent = "";
            }}, 2000);
          }} catch (e) {{
            msg.style.color = "red";
            msg.textContent = "Eroare copy. Deschide manual.";
          }}
        }});
      }})();
    </script>
    """
    components.html(html, height=50)


# --- INTERFAȚA ---

# Sidebar
with st.sidebar:
    st.header("Setări")
    chunk_size = st.slider(
        "Lungimea unei bucăți (caractere)",
        min_value=2000,
        max_value=20000,
        value=6000,
        step=500,
        help="6000-8000 este ideal pentru ChatGPT 4.",
    )
    show_cleaned_toggle = st.toggle("Arată textul promptului (Debugging)", value=False)
    st.info(
        "Instrucțiuni:\n"
        "1. Lipește textul.\n"
        "2. Apasă 'Generează'.\n"
        "3. Copiază pe rând fiecare 'CHUNK' și dă-l lui ChatGPT."
    )

# Session state initialization
st.session_state.setdefault("last_digest", "")
st.session_state.setdefault("generated", False)
st.session_state.setdefault("chunks", [])
st.session_state.setdefault("prompts", [])

# Main page layout
st.title("📚 Medical Transcript Splitter (List View)")
st.write("Transformă transcriptul în prompturi secvențiale, afișate unul sub altul.")

raw_text = st.text_area("Lipește Transcriptul Brut Aici:", height=200)

raw_text_stripped = raw_text.strip()
current_digest = _digest(raw_text_stripped) if raw_text_stripped else ""

# Auto-reset generation when input changes
if current_digest and current_digest != st.session_state["last_digest"]:
    st.session_state["last_digest"] = current_digest
    st.session_state["generated"] = False
    st.session_state["chunks"] = []
    st.session_state["prompts"] = []

col1, col2 = st.columns([1, 4])
with col1:
    generate_clicked = st.button("🚀 Generează", type="primary", use_container_width=True)
with col2:
    if st.button("🧹 Reset", use_container_width=False):
        st.session_state["generated"] = False
        st.session_state["chunks"] = []
        st.session_state["prompts"] = []
        st.rerun()

if generate_clicked:
    cleaned = clean_transcript(raw_text_stripped)
    chunks = split_text_into_chunks(cleaned, chunk_size)
    prompts = [build_prompt(i + 1, len(chunks), ch) for i, ch in enumerate(chunks)]

    st.session_state["chunks"] = chunks
    st.session_state["prompts"] = prompts
    st.session_state["generated"] = True
    st.rerun()

# --- AFIȘAREA REZULTATELOR (LISTA) ---

if not raw_text_stripped:
    st.warning("Aștept transcriptul...")
elif not st.session_state["generated"]:
    st.info("Transcript detectat. Apasă butonul pentru a genera prompturile.")
else:
    prompts = st.session_state["prompts"]
    chunks = st.session_state["chunks"]
    total = len(prompts)

    st.success(f"Text împărțit în {total} părți. Copiază-le pe rând mai jos:")
    st.divider()

    # Iterăm prin toate prompturile și le afișăm unul sub altul
    for i, prompt in enumerate(prompts):
        idx = i + 1
        
        # Container vizual pentru fiecare pas
        with st.container():
            st.subheader(f"🔹 CHUNK {idx} din {total}")
            
            # Afișăm butonul de copiere
            copy_button(
                text_to_copy=prompt,
                label=f"📋 CLICK AICI PENTRU A COPIA CHUNK {idx}",
                dom_id=f"copy_btn_{idx}_{st.session_state['last_digest'][:6]}"
            )

            # Opțional: afișăm textul dacă utilizatorul a bifat toggle-ul
            if show_cleaned_toggle:
                with st.expander(f"Vezi conținutul promptului {idx} (Opțional)"):
                    st.code(prompt, language="text")
            
            st.divider() # Linie despărțitoare între pași
