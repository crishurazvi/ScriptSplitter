Iată codul final. Am combinat exact funcționalitatea scriptului tău medical (logica de split, regex, instrucțiunile master vs. continuare) cu designul vizual NeuroSplit (tema dark, glassmorphism, culori neon, layout pe 2 coloane).

Ce am făcut:

Design NeuroSplit: Am portat CSS-ul din exemplul tău HTML în Streamlit.

Layout: În stânga ai setările (Slider pentru lungime chunk), în dreapta input-ul de text.

Output Grid: Rezultatele apar jos sub formă de carduri elegante, pe 2 coloane, pentru a nu da scroll la infinit.

Funcționalitate: Am păstrat intacte funcțiile clean_transcript, split_text_into_chunks și logica de construire a prompturilor (Master vs Context).

code
Python
download
content_copy
expand_less
import streamlit as st
import re

# --- 1. CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Medical Architect | NeuroSplit Style", layout="wide", page_icon="🧬")

# --- 2. DESIGN NEUROSPLIT (CSS AVANSAT) ---
st.markdown("""
<style>
    /* IMPORT FONT MODERN */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* VARIABILE TEMA DARK (NEUROSPLIT) */
    :root {
        --bg-body: #09090b;
        --panel-bg: rgba(24, 24, 27, 0.75);
        --panel-border: rgba(255, 255, 255, 0.08);
        --input-bg: rgba(255, 255, 255, 0.03);
        --accent-primary: #8b5cf6; /* Violet */
        --accent-secondary: #2dd4bf; /* Teal */
        --text-main: #f4f4f5;
        --text-muted: #a1a1aa;
    }

    /* BACKGROUND GLOBAL */
    .stApp {
        background-color: var(--bg-body);
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 90% 80%, rgba(45, 212, 191, 0.15) 0%, transparent 50%);
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
    }

    /* TITLU GRADIENT */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 2rem;
        background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
    }

    /* PANELURI (GLASSMORPHISM) */
    .glass-panel {
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 20px;
        padding: 24px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        height: 100%;
    }

    /* TITLURI SECȚIUNI */
    .section-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-muted);
        margin-bottom: 20px;
        border-bottom: 1px solid var(--panel-border);
        padding-bottom: 10px;
        font-weight: 600;
    }

    /* INPUT-URI PERSONALIZATE */
    .stTextArea textarea {
        background-color: var(--input-bg) !important;
        border: 1px solid var(--panel-border) !important;
        color: var(--text-main) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
    }

    /* BUTON GENERARE */
    div.stButton > button {
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        color: white;
        border: none;
        padding: 14px 24px;
        border-radius: 12px;
        font-weight: bold;
        text-transform: uppercase;
        width: 100%;
        margin-top: 20px;
        transition: transform 0.2s, box-shadow 0.2s;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
        color: white;
    }

    /* CARDS OUTPUT */
    .output-card {
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        padding: 15px;
        margin-bottom: 15px;
        animation: slideUp 0.5s ease forwards;
        transition: border-color 0.3s;
    }
    .output-card:hover {
        border-color: rgba(139, 92, 246, 0.3);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--panel-border);
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--accent-secondary);
    }

    /* COD PREVIEW */
    .stCode {
        background-color: rgba(0,0,0,0.3) !important;
        border-radius: 8px !important;
    }

    @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    
    /* MODIFICĂRI SLIDER */
    .stSlider label { color: var(--text-muted) !important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- 3. LOGICA ORIGINALĂ (PĂSTRATĂ EXACT) ---

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
    text = re.sub(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_text_into_chunks(text, max_chars=8000):
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

# --- 4. INTERFAȚA VIZUALĂ (LAYOUT) ---

st.markdown('<div class="brand-title">NeuroSplit | Medical Architect</div>', unsafe_allow_html=True)

# Layout pe 2 Coloane (Stânga = Setări, Dreapta = Input)
col_settings, col_input = st.columns([1, 2], gap="large")

with col_settings:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚙️ CONFIGURARE</div>', unsafe_allow_html=True)
    
    # Slider
    chunk_size = st.slider(
        "Lungime Chunk (caractere)", 
        min_value=2000, max_value=20000, value=15000, step=500
    )
    st.caption("Pentru GPT-4 recomand 12k-15k. Pentru GPT-3.5 folosește sub 6k.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Buton Generare
    generate_btn = st.button("⚡ PROCESEAZĂ TRANSCRIPT")
    st.markdown('</div>', unsafe_allow_html=True)

with col_input:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📄 MATERIAL SURSĂ</div>', unsafe_allow_html=True)
    raw_text = st.text_area(
        "Input", 
        height=350, 
        placeholder="Lipește aici transcriptul brut...", 
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. GENERARE ȘI AFIȘARE CARDURI ---

if generate_btn and raw_text:
    # Logică procesare
    cleaned_text = clean_transcript(raw_text)
    chunks = split_text_into_chunks(cleaned_text, max_chars=chunk_size)
    
    st.markdown("---")
    st.subheader(f"🧩 REZULTATE ({len(chunks)} PĂRȚI)")
    
    # Grid Layout pentru rezultate (2 carduri pe rând pentru a reduce scroll-ul)
    grid_cols = st.columns(2)
    
    for i, chunk in enumerate(chunks):
        part_num = i + 1
        
        # Selectare coloană (stânga sau dreapta)
        current_col = grid_cols[i % 2]
        
        # Logică Construire Prompt
        if i == 0:
            # PRIMUL PROMPT
            final_prompt = f"""{SYSTEM_INSTRUCTIONS}

INPUT TEXT (PART {part_num}/{len(chunks)}):
{chunk}

INSTRUCTIONS FOR THIS PART:
Please adhere strictly to the ROLE and STRUCTURE defined above. 
Start writing the Textbook Chapter based on this text.
"""
            card_label = "🚀 START (MASTER PROMPT)"
            color_style = "color: #8b5cf6;" # Violet
        else:
            # URMĂTOARELE PROMPTURI
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
            card_label = f"🔄 CONTINUARE (PARTEA {part_num})"
            color_style = "color: #2dd4bf;" # Teal

        # Afișare Card în Grid
        with current_col:
            st.markdown(f"""
            <div class="output-card">
                <div class="card-header">
                    <span style="{color_style}">{card_label}</span>
                    <span style="font-size:0.7rem; opacity:0.6;">{len(chunk)} chars</span>
                </div>
                <div style="font-size: 0.8rem; color: #a1a1aa; margin-bottom: 5px;">
                    Copiază folosind butonul din colțul blocului de cod:
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Blocul de cod nativ (are copy button)
            # Limităm vizual înălțimea dacă e prea mult text, dar userul poate copia tot
            st.code(final_prompt, language="text")

elif generate_btn and not raw_text:
    st.error("⚠️ Te rog lipește un text în panoul din dreapta.")
