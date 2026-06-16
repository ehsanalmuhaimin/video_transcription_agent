import streamlit as st
import os
from pathlib import Path
from fpdf import FPDF
from datetime import datetime

# Import backend logic handles securely
from main import run_pipeline, pipeline_reset_workspace
from core.rag_engine import ask_question

# --- UTILITY: PDF GENERATOR (SANITIZED & ROBUST) ---
def clean_pdf_text(text):
    if not text:
        return ""
    replacements = {
        "“": '"', "”": '"',
        "‘": "'", "’": "'",
        "—": "-", "–": "-",
        "•": "*", "…": "..."
    }
    for bad_char, good_char in replacements.items():
        text = text.replace(bad_char, good_char)
    return text.encode('latin-1', 'ignore').decode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, 'AI Meeting Insight Report', ln=1, align='C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, ln=1, align='L', fill=True)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 11)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf(res):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 16)
    cleaned_title = clean_pdf_text(res.get('title', 'Meeting Report'))
    pdf.multi_cell(0, 10, f"Video Title: {cleaned_title}")
    pdf.ln(10)
    
    pdf.chapter_title("Executive Summary")
    pdf.chapter_body(clean_pdf_text(res.get('summary', '')))
    
    pdf.chapter_title("Action Items")
    pdf.chapter_body(clean_pdf_text(res.get('action_items', '')))
    
    pdf.chapter_title("Key Decisions")
    pdf.chapter_body(clean_pdf_text(res.get('key_decisions', '')))
    
    pdf.chapter_title("Open Questions")
    pdf.chapter_body(clean_pdf_text(res.get('open_questions', '')))
    
    return bytes(pdf.output())

def generate_chat_log(history):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"Chat Session Log - {timestamp}\n" + "="*50 + "\n\n"
    for role, text in history:
        log_text += f"[{role.upper()}]: {text}\n\n"
    return log_text

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Video Agent Pro", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_paused" not in st.session_state:
    st.session_state.chat_paused = False

# --- UNIFIED WORKSPACE MASTER RESET CONTROL ---
def master_reset_agent():
    """Wipes vector db storage blocks and cleans app state memory completely."""
    st.session_state.pipeline_results = None
    st.session_state.chat_history = []
    st.session_state.chat_paused = False
    
    try:
        pipeline_reset_workspace()
        st.toast("Database & workspace successfully cleared!", icon="🧼")
    except Exception as e:
        st.sidebar.error(f"Storage clearance failed: {e}")

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=50)
    st.title("Video Agent ⚡")
    st.markdown("---")
    
    st.subheader("1. Source Material")
    source_input = st.text_input("🔗 YouTube URL or File Path", placeholder="https://youtube.com/...")
    
    st.subheader("2. AI Settings")
    language_input = st.selectbox("Audio Language", ["english", "hinglish"])
    
    st.markdown("---")
    
    process_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    
    st.button("🧼 Reset Workspace / Clear Locks", type="secondary", use_container_width=True, on_click=master_reset_agent)
    
    st.markdown("---")
    st.markdown("##### System Status")
    if st.session_state.pipeline_results:
        st.success("System: Ready")
    else:
        st.info("System: Idle")

# --- MAIN LOGIC PIPELINE ---
if process_btn:
    if not source_input.strip():
        st.toast("⚠️ Please enter a valid URL or path", icon="⚠️")
    else:
        final_source = source_input.strip()
        if not final_source.startswith(("http://", "https://")):
            final_source = str(Path(final_source).absolute())

        with st.spinner("🔄 Downloading, Transcribing, and analyzing... this may take a moment."):
            try:
                st.session_state.pipeline_results = run_pipeline(final_source, language_input)
                st.session_state.chat_history = [] 
                st.session_state.chat_paused = False
                st.toast("Analysis Complete!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Critical Pipeline Error: {e}")
                st.info("💡 Action Required: Click the 'Reset Workspace / Clear Locks' button above to release locked database processes.")

# --- DASHBOARD LAYOUT ---
if st.session_state.pipeline_results:
    res = st.session_state.pipeline_results
    
    st.markdown(f"## 🎬 {res['title']}")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Processing Time", "Done")
    m2.metric("Language", language_input.title())
    m3.metric("Action Items", res['action_items'].count('\n') if res['action_items'] else 0)
    m4.metric("Key Decisions", res['key_decisions'].count('\n') if res['key_decisions'] else 0)
    
    st.markdown("---")

    col_insights, col_chat = st.columns([1.2, 1])

    # --- LEFT COLUMN: INSIGHTS & EXPORTS ---
    with col_insights:
        st.subheader("📑 Meeting Intel")
        
        tab_sum, tab_act, tab_dec, tab_raw = st.tabs(["Summary", "✅ Actions", "🔑 Decisions", "📜 Transcript"])
        
        with tab_sum:
            st.info(res['summary'])
            
        with tab_act:
            st.success(res['action_items'])
            
        with tab_dec:
            st.warning(res['key_decisions'])
            
        with tab_raw:
            st.text_area("Raw Text", res['transcript'], height=400)
            
        st.markdown("---")
        st.markdown("### 📥 Export Reports")
        
        pdf_bytes = generate_pdf(res)
        st.download_button(
            label="📄 Download Full PDF Report",
            data=pdf_bytes,
            file_name=f"Meeting_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # --- RIGHT COLUMN: RAG CHAT ---
    with col_chat:
        st.subheader("🤖 AI Assistant")
        
        c1, c2, c3 = st.columns([1,1,1])
        if c1.button("🧼 Clear All", use_container_width=True):
            master_reset_agent()
            st.rerun()
            
        if c2.button("⏸️ Pause", use_container_width=True):
            st.session_state.chat_paused = not st.session_state.chat_paused
            st.rerun()

        chat_log = generate_chat_log(st.session_state.chat_history)
        c3.download_button(
            "💾 Save", 
            data=chat_log, 
            file_name="chat_history.txt", 
            mime="text/plain",
            use_container_width=True
        )

        if st.session_state.chat_paused:
            st.warning("🔴 Chat is currently PAUSED. Unpause to resume.")
        else:
            st.caption("🟢 Chat is ACTIVE. Ask specific questions about the video.")

        chat_container = st.container(height=500)
        
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown("*No messages yet. Ask me anything about the video!*")
            
            for role, text in st.session_state.chat_history:
                with st.chat_message(role):
                    st.write(text)

        if not st.session_state.chat_paused:
            if user_query := st.chat_input("Ask a question..."):
                # 1. Immediately append and render user query locally
                st.session_state.chat_history.append(("user", user_query))
                with chat_container:
                    with st.chat_message("user"):
                        st.write(user_query)

                # 2. Extract the RAG chain safely from state context
                current_rag_chain = st.session_state.pipeline_results['rag_chain']

                # 3. Generate and append assistant response without losing context handles
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            answer = ask_question(current_rag_chain, user_query)
                            st.write(answer)
                
                st.session_state.chat_history.append(("assistant", answer))
                st.rerun()

else:
    st.markdown("""
    <div style='text-align: center; padding-top: 50px;'>
        <h1>👋 Welcome to Video Agent Pro</h1>
        <p>Turn hours of video content into actionable insights in seconds.</p>
        <p style='color: gray;'>Supports YouTube Links & Local Video/Audio Files</p>
    </div>
    """, unsafe_allow_html=True)