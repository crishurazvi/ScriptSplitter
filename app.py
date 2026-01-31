Am înțeles. Vom crea o interfață Glassmorphism (Glass UI) – un stil modern, minimalist, bazat pe transparență, blur și fundaluri întunecate, fără emoji-uri "jucăușe".

Ce aduce nou această versiune:

Glassmorphism CSS: Elementele par că plutesc pe un fundal abstract, având efect de sticlă mată (blur).

Configurator Prompt (Sidebar): Promptul nu mai este hardcodat static. Acum ai input-uri și checkbox-uri în stânga pentru a altera "Personalitatea" AI-ului, Limba sau regulile de formatare, care se reflectă direct în promptul final.

Flux de lucru: Input -> Buton Generare -> Carduri jos.

Carduri: Fiecare bucată de text este izolată vizual într-un "card" de sticlă, conținând blocul de cod cu butonul de copy integrat.

code
Python
download
content_copy
expand_less
import streamlit as st
import re

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Procesare Transcript", layout="wide")

# --- DESIGN: GLASSMORPHISM & ULTRA MODERN CSS ---
st.markdown("""
<style>
    /* 1. FUNDAL GLOBAL - Dark Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #172554 100%);
        color: #e2e8f0;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* 2. SIDEBAR - Glass Effect */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 3. INPUT TEXTAREA - Minimalist */
    .stTextArea textarea {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f1f5f9 !important;
        border-radius: 8px;
        backdrop-filter: blur(5px);
    }
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }

    /* 4. CARDS (Output Containers) */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
    }

    /* 5. BUTON GENERARE */
    div.stButton > button {
        background: linear-gradient(90deg, #2563eb, #1d4ed8);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.5px;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8, #1e40af);
        box-shadow: 0 0 15px rgba(37, 99, 235, 0.5);
    }

    /* 6. CODE BLOCK */
    .stCode {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-radius: 8px;
    }

    /* Titluri */
    h1, h2, h3 {
        color: #f8fafc;
        font-weight: 300;
    }
    
    /* Etichete input */
    label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCȚII LOGICE (Păstrate) ---

def clean_transcript(text):
    text = re.sub(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_text_into_chunks(text, max_chars):
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

# --- SIDEBAR: CONFIGURARE PROMPT ---
with st.sidebar:
    st.markdown("### CONFIGURARE PROMPT")
    st.markdown("---")
    
    # 1. Configurare Rol
    st.markdown("<small>ROL AI</small>", unsafe_allow_html=True)
    role_input = st.text_input(
        "Defineste cine este AI-ul", 
        value="Expert medical content analyst, academic editor, and medical educator",
        label_visibility="collapsed"
    )

    # 2. Limbă și Ton
    st.markdown("<br><small>LIMBA & STIL</small>", unsafe_allow_html=True)
    target_lang = st.selectbox("Limba Output", ["ORIGINAL LANGUAGE (French)", "English", "Romanian"], label_visibility="collapsed")
    
    # 3. Parametri Tehnici (Slider)
    st.markdown("<br><small>DIMENSIUNE CHUNK (CARACTERE)</small>", unsafe_allow_html=True)
    chunk_size = st.slider("Selecteaza lungimea", 2000, 25000, 15000, label_visibility="collapsed")
    
    # 4. Constrângeri (Checkboxes)
    st.markdown("<br><small>REGULI</small>", unsafe_allow_html=True)
    no_fluff = st.checkbox("Remove noise & hesitations", value=True)
    textbook_style = st.checkbox("Format Textbook (H2/H3)", value=True)
    bold_keys = st.checkbox("Bold key concepts", value=True)
    no_invent = st.checkbox("Do NOT invent info", value=True)

# --- CONSTRUIREA PROMPTULUI MASTER DIN GUI ---
# Construim dinamic string-ul de instrucțiuni pe baza input-urilor din stânga
constraints_list = []
if no_fluff: constraints_list.append("- Remove noise (repetitions, hesitations, irrelevant digressions).")
if textbook_style: constraints_list.append("- Organize content as a textbook chapter (H2/H3).")
if bold_keys: constraints_list.append("- Bold key concepts and definitions.")
if no_invent: constraints_list.append("- Do NOT invent information not present in the transcript.")

DYNAMIC_SYSTEM_INSTRUCTIONS = f"""
ROLE:
{role_input}

OBJECTIVE:
Transform the raw transcript into a structured course chapter.

LANGUAGE:
Keep the output strictly in: {target_lang}.

CORE TASKS:
{chr(10).join(constraints_list)}

STRUCTURE REQUIREMENTS:
- Use clear didactic structure.
- Define important terms.
- Highlight cause-effect relationships.
- No emojis, professional tone.
"""

# --- ZONA PRINCIPALĂ ---

st.title("GENERATOR PROMPTURI")
st.markdown("<p style='color: #94a3b8; margin-bottom: 30px;'>Lipeste transcriptul, genereaza bucatile si copiaza-le in AI.</p>", unsafe_allow_html=True)

# Container Input
input_container = st.container()
with input_container:
    raw_text = st.text_area("TRANSCRIPT", height=300, placeholder="Lipeste textul aici...", label_visibility="hidden")
    
    col_btn, col_empty = st.columns([1, 3])
    with col_btn:
        generate_clicked = st.button("GENEREAZA CHUNKS")

# --- ZONA OUTPUT (CARDURI) ---

if generate_clicked and raw_text:
    # Procesare
    cleaned_text = clean_transcript(raw_text)
    chunks = split_text_into_chunks(cleaned_text, max_chars=chunk_size)
    
    st.markdown("---")
    st.markdown(f"### REZULTATE ({len(chunks)} PĂRȚI)")
    
    # Iterare și afișare carduri
    for i, chunk in enumerate(chunks):
        part_num = i + 1
        
        # Generare Prompt Specific
        if i == 0:
            prompt_content = f"""{DYNAMIC_SYSTEM_INSTRUCTIONS}

INPUT TEXT (PART {part_num}/{len(chunks)}):
{chunk}

INSTRUCTIONS FOR THIS PART:
Start writing the Textbook Chapter based on this text. Adhere strictly to the ROLE and STRUCTURE.
"""
            card_title = "PROMPT START (PARTEA 1)"
            border_style = "border-left: 4px solid #3b82f6;" # Albastru pentru start
        else:
            prompt_content = f"""{DYNAMIC_SYSTEM_INSTRUCTIONS}

CONTEXT:
You are continuing a chapter. Do not create a new title.

INPUT TEXT (PART {part_num}/{len(chunks)}):
{chunk}

INSTRUCTIONS FOR THIS PART:
CONTINUE the textbook chapter from where you left off. Maintain formatting.
"""
            card_title = f"PROMPT CONTINUARE (PARTEA {part_num})"
            border_style = "border-left: 4px solid #64748b;" # Gri pentru continuare

        # Renderizare HTML Card Container
        st.markdown(f"""
        <div class="glass-card" style="{border_style}">
            <h4 style="margin: 0 0 10px 0; color: white;">{card_title}</h4>
            <p style="font-size: 0.8rem; color: #94a3b8;">Click pe iconita de copy din dreapta-sus a blocului de cod.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Afișare cod (care are buton de copy nativ)
        st.code(prompt_content, language="text")
        
        # Spacer mic între carduri
        st.write("") 

elif generate_clicked and not raw_text:
    st.error("Te rog lipeste un text inainte de a genera.")
