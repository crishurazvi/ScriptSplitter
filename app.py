# app.py
import hashlib
import json
import re

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Medical Transcript Splitter", layout="wide")

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
    - Remove timestamps like (2:58:54) or (12:00)
    - Collapse whitespace/newlines into single spaces
    - Strip ends
    """
    if not text:
        return ""

    timestamp_pattern = r"\(\d{1,2}:\d{2}(?::\d{2})?\)"
    text = re.sub(timestamp_pattern, " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text_into_chunks(text: str, max_chars: int) -> list[str]:
    """
    Split by words and build chunks that do not exceed max_chars.
    Robust behavior:
    - If a single "word" exceeds max_chars, it is sliced.
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
    Renders a compact HTML button that copies `text_to_copy` to clipboard via JS.
    Note: st.components.v1.html() does NOT accept `key` in many Streamlit versions.
    """
    payload = json.dumps(text_to_copy)
    safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", dom_id)

    html = f"""
    <div style="display:flex;align-items:center;gap:10px;margin:0;padding:0;">
      <button id="{safe_id}"
              style="
                border:1px solid #d0d0d0;
                padding:8px 12px;
                border-radius:10px;
                background:white;
                cursor:pointer;
                font-size:14px;
                line-height:1;
              ">
        {label}
      </button>
      <span id="{safe_id}_msg" style="font-size:12px;color:#666;line-height:1;"></span>
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
            btn.innerText = "✅ Copiat!";
            msg.textContent = "";
            setTimeout(() => {{
              btn.innerText = originalText;
            }}, 1200);
          }} catch (e) {{
            msg.textContent = "Copiere automată indisponibilă aici. Deschide promptul și folosește icon-ul Copy.";
          }}
        }});
      }})();
    </script>
    """
    components.html(html, height=50)


# Sidebar
with st.sidebar:
    st.header("Setări")
    chunk_size = st.slider(
        "Lungimea unei bucăți (caractere)",
        min_value=2000,
        max_value=20000,
        value=6000,
        step=500,
        help="6000-8000 este ideal pentru ChatGPT 4. Pentru GPT-3.5 folosește mai puțin.",
    )
    show_cleaned_toggle = st.toggle("Arată textul (opțional)", value=False)
    st.info(
        "Pași de utilizare:\n"
        "1. Lipește textul brut în zona principală.\n"
        "2. Apasă butonul de generare.\n"
        "3. Copiază PASUL 1 în AI și procesează.\n"
        "4. Apoi mergi la PASUL 2, PASUL 3, etc."
    )

# Session state
st.session_state.setdefault("last_digest", "")
st.session_state.setdefault("generated", False)
st.session_state.setdefault("cleaned", "")
st.session_state.setdefault("chunks", [])
st.session_state.setdefault("prompts", [])
st.session_state.setdefault("current_step", 1)

# Main page
st.title("📚 Medical Transcript to Textbook AI Splitter")
st.write(
    "Această aplicație curăță timestamp-urile dintr-un transcript medical, îl împarte în bucăți "
    "și generează prompturi gata de copiat, optimizate pentru ChatGPT/Claude, astfel încât să "
    "procesezi textul pas cu pas într-un capitol tip manual."
)

raw_text = st.text_area("Lipește Transcriptul Brut Aici:", height=300)

raw_text_stripped = raw_text.strip()
current_digest = _digest(raw_text_stripped) if raw_text_stripped else ""

# Auto-reset generation when input changes
if current_digest and current_digest != st.session_state["last_digest"]:
    st.session_state["last_digest"] = current_digest
    st.session_state["generated"] = False
    st.session_state["cleaned"] = ""
    st.session_state["chunks"] = []
    st.session_state["prompts"] = []
    st.session_state["current_step"] = 1

btn_col1, btn_col2, _ = st.columns([1, 1, 3])
with btn_col1:
    generate_clicked = st.button("🚀 Generează chunk-uri", type="primary", use_container_width=True)
with btn_col2:
    reset_clicked = st.button("🧹 Reset", use_container_width=True)

if reset_clicked:
    st.session_state["generated"] = False
    st.session_state["cleaned"] = ""
    st.session_state["chunks"] = []
    st.session_state["prompts"] = []
    st.session_state["current_step"] = 1
    st.rerun()

if generate_clicked:
    cleaned = clean_transcript(raw_text_stripped)
    chunks = split_text_into_chunks(cleaned, chunk_size)
    prompts = [build_prompt(i + 1, len(chunks), ch) for i, ch in enumerate(chunks)]

    st.session_state["cleaned"] = cleaned
    st.session_state["chunks"] = chunks
    st.session_state["prompts"] = prompts
    st.session_state["generated"] = True
    st.session_state["current_step"] = 1
    st.rerun()

if not raw_text_stripped:
    st.warning("Aștept transcriptul...")
elif not st.session_state["generated"]:
    st.info("Text introdus. Apasă „Generează chunk-uri” ca să obții prompturile.")
else:
    chunks = st.session_state["chunks"]
    prompts = st.session_state["prompts"]
    total = len(chunks)

    st.write(f"### 🎉 Rezultat: Textul a fost împărțit în {total} părți.")

    if total == 0:
        st.warning("Nu am putut genera părți. Verifică dacă transcriptul are conținut după curățare.")
    else:
        nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([1, 1, 1, 6])

        with nav_c1:
            if st.button("⬅️ Înapoi", use_container_width=True, disabled=st.session_state["current_step"] <= 1):
                st.session_state["current_step"] = max(1, st.session_state["current_step"] - 1)
                st.rerun()

        with nav_c2:
            if st.button("➡️ Înainte", use_container_width=True, disabled=st.session_state["current_step"] >= total):
                st.session_state["current_step"] = min(total, st.session_state["current_step"] + 1)
                st.rerun()

        with nav_c3:
            step = st.number_input("", min_value=1, max_value=total, value=int(st.session_state["current_step"]), step=1)
            if int(step) != int(st.session_state["current_step"]):
                st.session_state["current_step"] = int(step)
                st.rerun()

        idx = int(st.session_state["current_step"])
        prompt = prompts[idx - 1]
        chunk = chunks[idx - 1]

        st.subheader(f"📝 PASUL {idx} (Copiază acest prompt în AI)")

        copy_button(
            prompt,
            "📋 Copy prompt",
            dom_id=f"copy_prompt_{idx}_{st.session_state['last_digest'][:8]}",
        )

        if show_cleaned_toggle:
            with st.expander("Vezi promptul (opțional)", expanded=False):
                st.code(prompt, language="text")
            with st.expander(f"Vezi textul brut curățat pentru Partea {idx} (opțional)", expanded=False):
                st.write(chunk)
