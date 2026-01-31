# app.py
import re
import streamlit as st

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

    # Collapse all whitespace (spaces, tabs, newlines) into single spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_text_into_chunks(text: str, max_chars: int) -> list[str]:
    """
    Split by words and build chunks that do not exceed max_chars.
    Simple, robust behavior:
    - Works even if there are very long "words" by slicing them.
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
        # If a single word exceeds max_chars, slice it
        if len(w) > max_chars:
            flush_current()
            start = 0
            while start < len(w):
                chunks.append(w[start : start + max_chars])
                start += max_chars
            continue

        candidate = w if not current else f"{current} {w}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            flush_current()
            current = w

    flush_current()
    return chunks


# Sidebar
with st.sidebar:
    st.header("Setări")
    chunk_size = st.slider(
        "Lungimea unei bucăți (caractere)",
        min_value=2000,
        max_value=20000,
        value=20000,
        step=500,
        help="6000-8000 este ideal pentru ChatGPT 4. Pentru GPT-3.5 folosește mai puțin.",
    )
    st.info(
        "Pași de utilizare:\n"
        "1. Lipește textul brut în zona principală.\n"
        "2. Aplicația curăță timestamp-urile și generează prompturi pe bucăți.\n"
        "3. Copiază PASUL 1 în AI și procesează.\n"
        "4. Când termini, copiază PASUL 2, apoi PASUL 3, etc."
    )

# Main page
st.title("📚 Medical Transcript to Textbook AI Splitter")
st.write(
    "Această aplicație curăță timestamp-urile dintr-un transcript medical, îl împarte în bucăți "
    "și generează prompturi gata de copiat, optimizate pentru ChatGPT/Claude, astfel încât să "
    "procesezi textul pas cu pas într-un capitol tip manual."
)

raw_text = st.text_area("Lipește Transcriptul Brut Aici:", height=300)

if raw_text.strip():
    cleaned = clean_transcript(raw_text)
    chunks = split_text_into_chunks(cleaned, chunk_size)
    total = len(chunks)

    st.write(f"### 🎉 Rezultat: Textul a fost împărțit în {total} părți.")

    for idx, chunk in enumerate(chunks, start=1):
        st.subheader(f"📝 PASUL {idx} (Copiază acest prompt în AI)")

        if idx == 1:
            final_prompt = (
                f"{SYSTEM_INSTRUCTIONS}\n\n"
                f"INPUT TEXT (PART {idx}/{total}):\n"
                f"{chunk}\n\n"
                "INSTRUCTIONS FOR THIS PART:\n"
                "- Start writing the textbook chapter now based ONLY on this part.\n"
                "- Use H2/H3 headings, bold key terms, and keep a clean textbook style.\n"
                "- Do not invent information.\n"
                "- If the content feels incomplete, stop naturally and continue in the next parts.\n"
            )
        else:
            final_prompt = (
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

        st.code(final_prompt, language="text")

        with st.expander(f"Vezi textul brut curățat pentru Partea {idx}"):
            st.write(chunk)
else:
    st.warning("Aștept transcriptul...")
