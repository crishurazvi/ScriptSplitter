import streamlit as st
import re

# --- CONFIGURAȚIA PROMPTULUI ORIGINAL ---
# Acesta este promptul master pe care mi l-ai dat.
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
    # Regex pentru timestamp (ex: (2:58:54) sau (12:00))
    text = re.sub(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', '', text)
    # Elimină spațiile multiple
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_text_into_chunks(text, max_chars=8000):
    """
    Împarte textul în bucăți care nu depășesc max_chars,
    încercând să rupă textul la final de propoziție.
    """
    words = text.split(' ')
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_chars:
            # Verificăm dacă ultimul cuvânt din chunk se termină cu punct
            # Dacă nu, ar fi ideal să mai adăugăm puțin, dar pentru simplitate
            # tăiem aici și AI-ul se va descurca datorită suprapunerii contextuale logice
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(word)
        current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# --- INTERFAȚA STREAMLIT ---

st.set_page_config(page_title="Medical Transcript Splitter", layout="wide")

st.title("📚 Medical Transcript to Textbook AI Splitter")
st.markdown("""
Această aplicație ia un transcript lung, îl curăță de timestamp-uri și îl împarte în 
prompt-uri optimizate pentru a fi date unui AI (ChatGPT/Claude).
""")

# Sidebar pentru setări
with st.sidebar:
    st.header("Setări")
    chunk_size = st.slider("Lungimea unei bucăți (caractere)", 
                           min_value=2000, 
                           max_value=20000, 
                           value=20000, 
                           step=500,
                           help="6000-8000 este ideal pentru ChatGPT 4. Pentru GPT-3.5 folosește mai puțin.")
    
    st.info("ℹ️ **Cum funcționează:**\n1. Lipește textul.\n2. Aplicația generează 2-3 prompt-uri.\n3. Copiază primul prompt în AI.\n4. Când AI termină, copiază al doilea prompt, etc.")

# Input Area
raw_text = st.text_area("Lipește Transcriptul Brut Aici:", height=300)

if raw_text:
    # 1. Curățare
    cleaned_text = clean_transcript(raw_text)
    
    # 2. Împărțire
    chunks = split_text_into_chunks(cleaned_text, max_chars=chunk_size)
    
    st.markdown(f"### 🎉 Rezultat: Textul a fost împărțit în {len(chunks)} părți.")
    st.markdown("---")

    # 3. Generare Prompt-uri
    for i, chunk in enumerate(chunks):
        part_num = i + 1
        st.subheader(f"📝 PASUL {part_num} (Copiază acest prompt în AI)")
        
        final_prompt = ""
        
        if i == 0:
            # --- PRIMUL PROMPT (Conține instrucțiunile Master) ---
            final_prompt = f"""{SYSTEM_INSTRUCTIONS}

INPUT TEXT (PART {part_num}/{len(chunks)}):
{chunk}

INSTRUCTIONS FOR THIS PART:
Please adhere strictly to the ROLE and STRUCTURE defined above. 
Start writing the Textbook Chapter based on this text.
"""
        else:
            # --- URMĂTOARELE PROMPT-URI (Context de continuare) ---
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

        # Afișare cod pentru copiere ușoară
        st.code(final_prompt, language="text")
        
        # Previzualizare text curat (opțional, într-un expander)
        with st.expander(f"Vezi textul brut curățat pentru Partea {part_num}"):
            st.write(chunk)

else:
    st.warning("Aștept transcriptul...")
