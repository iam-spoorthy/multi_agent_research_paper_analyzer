
# Streamlit Web Interface for AI-Powered Research Paper Analyzer

import streamlit as st
import tempfile
import os
from src.pdf_parser import extract_text_from_pdf
from src.graph import app_graph

# Page Configuration
st.set_page_config(
    page_title="AI Research Paper Analyzer",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling (Glassmorphism & Modern Palette)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%); color: white; border-radius: 8px; border: none; font-weight: bold; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ AI-Powered Research Paper Analyzer")
st.caption("Multi-Agent LangGraph Workflow with Automated Review & Quality Control")

# Sidebar - Settings & Keys
with st.sidebar:
    st.header("⚙️ Configuration")
    groq_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    st.info("Built for Vilambo Technical Assignment")

# PDF File Uploader
uploaded_file = st.file_uploader("Upload Academic Paper (PDF)", type=["pdf"])

if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")
    
    if st.button("🚀 Analyze Paper with Multi-Agents"):
        with st.spinner("Processing PDF and Initializing LangGraph Workflow..."):
            # Save uploaded file to temp path
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Extract PDF text
            paper_text = extract_text_from_pdf(tmp_path)
            os.remove(tmp_path)
            
            # Initialize State
            initial_state = {
                "paper_text": paper_text,
                "methodology_analysis": "",
                "executive_summary": "",
                "citations": [],
                "key_insights": "",
                "review_score": 0,
                "review_feedback": "",
                "retry_count": 0,
                "final_brief": ""
            }
            
            # Run Graph Workflow
            final_output = app_graph.invoke(initial_state)
            
            # Metrics Row
            col1, col2, col3 = st.columns(3)
            col1.metric("Quality Review Score", f"{final_output['review_score']} / 10")
            col2.metric("Review Retries", f"{final_output['retry_count']}")
            col3.metric("Status", "Approved ✅" if final_output['review_score'] >= 7 else "Completed with Limit ⚠️")
            
            # Multi-Tab Dashboard Display
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Final Brief", "🔬 Methodology", "📌 Executive Summary", "💡 Insights", "📚 Citations"])
            
            with tab1:
                st.markdown(final_output.get("final_brief", "No brief generated."))
                st.download_button(
                    label="📥 Download Complete Brief (.md)",
                    data=final_output.get("final_brief", ""),
                    file_name=f"{uploaded_file.name}_research_brief.md",
                    mime="text/markdown"
                )
                
            with tab2:
                st.write(final_output.get("methodology_analysis", ""))
            with tab3:
                st.write(final_output.get("executive_summary", ""))
            with tab4:
                st.write(final_output.get("key_insights", ""))
            with tab5:
                for cite in final_output.get("citations", []):
                    st.markdown(f"- {cite}")