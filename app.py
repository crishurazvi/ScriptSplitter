import streamlit as st
import re

# --- CONFIGURARE PAGINĂ & CSS MODERN ---
st.set_page_config(page_title="Medical AI Splitter", layout="wide", page_icon="🧬")

# CSS Custom pentru un aspect "SaaS Modern"
st.markdown("""
<style>
    /* Import font modern */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Titlu cu Gradient */
    .title-text {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        padding-bottom: 20px;
    }

    /* Stil container principal */
    .stTextArea textarea {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        border-color: #4b6cb7;
        box-shadow: 0 0 0 3px rgba(75, 108, 183, 0.2);
    }

    /* Stil Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f4f6f9;
        border-right: 1px solid #e1e4e8;
    }

    /* Card-uri pentru Output (Expander) */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        font-weight: 600;
        color: #1f2937;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .streamlit-expanderHeader:hover {
        background-color: #f0f4f8;
        color: #4b6cb7;
    }
    
    /* Blocul de cod */
    .stCode {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAȚIA PROMPTULUI ORIGINAL (LOGICA PĂSTRATĂ) ---
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

def clean_transcript(text):
    """Elimină timestamp-urile de tip (2:58:54) și spațiile inutile."""
    text = re.sub(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_text_into_chunks(text, max_chars=8000):
    """Împarte textul în bucăți care nu depășesc max_chars."""
    words = text.split(' ')
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# --- SIDEBAR MODERN ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=60)
    st.markdown("### ⚙️ Setări Procesare")
    st.markdown("---")
    chunk_size = st.slider(
        "Lungime Chunk (caractere)", 
        min_value=2000, 
        max_value=20000, 
        value=15000, 
        step=500,
        help="Ajustează dimensiunea textului trimis la AI."
    )
    st.markdown("---")
    st.info("**Sfat:** Pentru GPT-4 poți folosi valori mari (12k-15k). Pentru GPT-3.5 limitează la 6k.")

# --- LAYOUT PRINCIPAL ---

# Header Custom
st.markdown('<h1 class="title-text">Medical Transcript AI Splitter</h1>', unsafe_allow_html=True)
st.markdown("Transformă transcripturi lungi în prompt-uri perfecte pentru ChatGPT/Claude, gata de copiat.")

# Zona de Input
col1, col2 = st.columns([3, 1])
with col1:
    raw_text = st.text_area("✍️ Introdu textul brut aici", height=200, placeholder="Lipește transcriptul lung aici...")

# Zona de Status (partea dreapta)
with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    if raw_text:
        cleaned_len = len(clean_transcript(raw_text))
        st.metric(label="Caractere Totale", value=f"{cleaned_len:,}")
        st.success("Text detectat!")
    else:
        st.info("Aștept input...")

# --- PROCESARE ȘI AFIȘARE ---

if raw_text:
    # 1. Procesare
    cleaned_text = clean_transcript(raw_text)
    chunks = split_text_into_chunks(cleaned_text, max_chars=chunk_size)
    
    st.divider()
    
    # Header secțiune rezultate
    st.markdown(f"### 🚀 Prompt-uri Generate ({len(chunks)} părți)")
    st.markdown("Deschide fiecare secțiune de mai jos și copiază codul folosind butonul din colțul dreapta-sus al blocului negru.")

    # 2. Generare Interfață Compactă
    for i, chunk in enumerate(chunks):
        part_num = i + 1
        is_first = (i == 0)
        
        # Logică construire prompt (neschimbată)
        if is_first:
            final_prompt = f"""{SYSTEM_INSTRUCTIONS}

INPUT TEXT (PART {part_num}/{len(chunks)}):
{chunk}

INSTRUCTIONS FOR THIS PART:
Please adhere strictly to the ROLE and STRUCTURE defined above. 
Start writing the Textbook Chapter based on this text.
"""
            label_icon = "1️⃣"
            label_text = "START: Primul Prompt (Instrucțiuni Master)"
            color_border = "border: 2px solid #4b6cb7;"
        else:
            final_prompt = f"""{SYSTEM_INSTRUCTIONS}

CONTEXT:
You are currently writing a medical textbook chapter based on a transcript.
You have already processed the previous parts.

INPUT TEXT (PART {part_num}/{len(chunks)}):
{chunk}

INSTRUCTIONS FOR THIS PART:
**CONTINUE** the textbook chapter from where you left off.
- Do NOT create a new Title or a new Introduction.
- Maintain the same formatting (H2/H3, bolding) as the previous part.
- Treat this text as a direct continuation of the previous segment.
"""
            label_icon = f"🔄"
            label_text = f"CONTINUARE: Partea {part_num} din {len(chunks)}"

        # 3. Afișare Compactă (Expander)
        # Folosim expander pentru a nu ocupa loc. 
        # Expanded=True doar pentru primul ca să fie evident.
        with st.expander(f"{label_icon} {label_text}", expanded=is_first):
            st.markdown("Copiază textul de mai jos:")
            # st.code are buton de copy automat în dreapta sus
            st.code(final_prompt, language="text")
            
            # Opțiune de verificare text sursă (subtil)
            with st.popover("🔍 Vezi fragmentul original curățat"):
                st.caption(f"Fragment din textul sursă (Partea {part_num})")
                st.text(chunk[:1000] + "...") 

else:
    # Placeholder vizual când nu e text
    st.markdown("")
    st.markdown("""
    <div style="text-align: center; color: #888; margin-top: 50px;">
        <h3>👈 Începe prin a lipi textul în stânga sus</h3>
    </div>
    """, unsafe_allow_html=True)
