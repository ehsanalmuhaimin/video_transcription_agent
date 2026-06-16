import streamlit as st
import os
from pathlib import Path
from fpdf import FPDF
from datetime import datetime

# Import backend logic
from main import run_pipeline
from core.rag_engine import ask_question

# --- UTILITY: PDF GENERATOR ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'AI Meeting Insight Report', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf(res):
    pdf = PDFReport()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.multi_cell(0, 10, f"Video Title: {res['title']}")
    pdf.ln(10)
    
    # Summary
    pdf.chapter_title("Executive Summary")
    pdf.chapter_body(res['summary'])
    
    # Action Items
    pdf.chapter_title("Action Items")
    pdf.chapter_body(res['action_items'])
    
    # Decisions
    pdf.chapter_title("Key Decisions")
    pdf.chapter_body(res['key_decisions'])
    
    # Questions
    pdf.chapter_title("Open Questions")
    pdf.chapter_body(res['open_questions'])
    
    return pdf.output(dest='S').encode('latin-1')

def generate_chat_log(history):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"Chat Session Log - {timestamp}\n" + "="*50 + "\n\n"
    for role, text in history:
        log_text += f"[{role.upper()}]: {text}\n\n"
    return log_text

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Agent Pro", page_icon="⚡", layout="wide")

# Custom CSS to hide default Streamlit clutter
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
    
    st.markdown("##### System Status")
    if "pipeline_results" in st.session_state and st.session_state.pipeline_results:
        st.success("System: Ready")
    else:
        st.info("System: Idle")

# --- SESSION STATE INITIALIZATION ---
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_paused" not in st.session_state:
    st.session_state.chat_paused = False

# --- MAIN LOGIC PIPELINE ---
if process_btn:
    if not source_input.strip():
        st.toast("⚠️ Please enter a valid URL or path", icon="⚠️")
    else:
        # Cross-platform path handling for local files
        final_source = source_input.strip()
        if not final_source.startswith(("http://", "https://")):
            final_source = str(Path(final_source).absolute())

        with st.spinner("🔄 Downloading, Transcribing, and analyzing... this may take a moment."):
            try:
                # Run the backend
                st.session_state.pipeline_results = run_pipeline(final_source, language_input)
                st.session_state.chat_history = [] # Reset memory
                st.session_state.chat_paused = False
                st.toast("Analysis Complete!", icon="✅")
            except Exception as e:
                st.error(f"Critical Pipeline Error: {e}")

# --- DASHBOARD LAYOUT ---
if st.session_state.pipeline_results:
    res = st.session_state.pipeline_results
    
    # 1. Header Section
    st.markdown(f"## 🎬 {res['title']}")
    
    # Quick Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Processing Time", "Done")
    m2.metric("Language", language_input.title())
    m3.metric("Action Items", res['action_items'].count('\n') if res['action_items'] else 0)
    m4.metric("Key Decisions", res['key_decisions'].count('\n') if res['key_decisions'] else 0)
    
    st.markdown("---")

    # 2. Split View: Insights vs Chat
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
        
        # PDF Generation Button
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
        
        # Chat Control Toolbar
        c1, c2, c3 = st.columns([1,1,1])
        if c1.button("🧹 Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
        if c2.button("⏸️ Pause", use_container_width=True):
            st.session_state.chat_paused = not st.session_state.chat_paused
            st.rerun()

        # Chat History Export
        chat_log = generate_chat_log(st.session_state.chat_history)
        c3.download_button(
            "💾 Save", 
            data=chat_log, 
            file_name="chat_history.txt", 
            mime="text/plain",
            use_container_width=True
        )

        # Status Indicator
        if st.session_state.chat_paused:
            st.warning("🔴 Chat is currently PAUSED. Unpause to resume.")
        else:
            st.caption("🟢 Chat is ACTIVE. Ask specific questions about the video.")

        # Chat Container (Scrollable)
        chat_container = st.container(height=500)
        
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown("*No messages yet. Ask me anything about the video!*")
            
            for role, text in st.session_state.chat_history:
                with st.chat_message(role):
                    st.write(text)

        # Chat Input
        if not st.session_state.chat_paused:
            if user_query := st.chat_input("Ask a question..."):
                # Append user message
                st.session_state.chat_history.append(("user", user_query))
                with chat_container:
                    with st.chat_message("user"):
                        st.write(user_query)

                # Process AI Response
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            answer = ask_question(res['rag_chain'], user_query)
                            st.write(answer)
                
                # Append AI message
                st.session_state.chat_history.append(("assistant", answer))
                st.rerun()

else:
    # Empty State - Hero Section
    st.markdown("""
    <div style='text-align: center; padding-top: 50px;'>
        <h1>👋 Welcome to Video Agent Pro</h1>
        <p>Turn hours of video content into actionable insights in seconds.</p>
        <p style='color: gray;'>Supports YouTube Links & Local Video/Audio Files</p>
    </div>
    """, unsafe_allow_html=True)
