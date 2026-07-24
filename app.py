# Streamlit Web Interface for Multi-Agent Research Paper Analyzer

import streamlit as st
import tempfile
import os
from src.pdf_parser import extract_text_from_pdf, download_and_extract_pdf_from_url, chunk_text
from src.graph import create_workflow
from src.tracing import setup_langsmith_tracing, check_langsmith_connection, get_langsmith_tracer

# Initialize LangSmith Tracing at startup
setup_langsmith_tracing()

# Page Configuration
st.set_page_config(
    page_title="AI Research Paper Analyzer",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling (Glassmorphism & Sleek Dark Palette)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%); color: white; border-radius: 8px; border: none; font-weight: bold; padding: 10px 24px; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); }
    .status-badge { padding: 6px 12px; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ AI-Powered Research Paper Analyzer")
st.caption("Multi-Agent LangGraph Workflow with Quality Control Reviewer & Live Sub-Agent Visualizer")

# Sidebar - Settings & User API Key Input
with st.sidebar:
    st.header("⚙️ Configuration")
    user_groq_key = st.text_input("Enter your Groq API Key", type="password", help="Enter your personal Groq API Key (gsk_...)")
    groq_key = user_groq_key.strip() or os.getenv("GROQ_API_KEY", "")
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
        
    user_langsmith_key = st.text_input("Enter your LangSmith API Key", type="password", help="Required API Key for LangSmith observability & tracing (lsv2_...)")
    langsmith_key = user_langsmith_key.strip() or os.getenv("LANGSMITH_API_KEY", "")
    if langsmith_key:
        setup_langsmith_tracing(langsmith_key)
    else:
        setup_langsmith_tracing()

    st.markdown("---")
    
    # LangSmith Tracing Visual Indicator Badge
    is_tracing = setup_langsmith_tracing(langsmith_key) and bool(os.getenv("LANGSMITH_API_KEY"))
    if is_tracing:
        project_name = os.getenv("LANGSMITH_PROJECT", "research-paper-analyzer")
        st.success(f"📊 **LangSmith Tracing: Active**\n\nProject: `{project_name}`")
        st.markdown("👉 [**Open LangSmith Dashboard 🔗**](https://smith.langchain.com/projects)")
    else:
        st.error("⚠️ **LangSmith Tracing: Inactive** (API Key Required)")

    st.info("💡 **Security Notice**: Your API keys are processed securely in your local session and never hardcoded or stored.")

# Input mode selection: PDF File Upload OR PDF URL
input_method = st.radio("Choose Input Method:", ["Upload PDF File(s)", "Enter PDF URL (e.g., arXiv / Academic Link)"], horizontal=True)

paper_items = [] # tuples of (name/url, paper_text)

if input_method == "Upload PDF File(s)":
    uploaded_files = st.file_uploader("Upload Academic Papers (PDF)", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} paper(s) successfully!")
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            p_text = extract_text_from_pdf(tmp_path)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
            if p_text.strip():
                paper_items.append((uploaded_file.name, p_text))
            else:
                st.warning(f"Could not extract text from {uploaded_file.name}. It might be a scanned image PDF.")
else:
    pdf_url = st.text_input("Enter Research Paper PDF URL:", placeholder="e.g. https://arxiv.org/pdf/1706.03762.pdf or https://arxiv.org/abs/1706.03762")
    if pdf_url:
        if st.button("📥 Fetch Paper from URL"):
            with st.spinner("Downloading and parsing PDF from URL..."):
                try:
                    p_text = download_and_extract_pdf_from_url(pdf_url)
                    if p_text.strip():
                        st.session_state["fetched_url_paper"] = (pdf_url, p_text)
                        st.success("Successfully fetched paper from URL!")
                    else:
                        st.error("Failed to extract text from the downloaded PDF URL.")
                except Exception as e:
                    st.error(f"Error downloading PDF from URL: {str(e)}")

        if "fetched_url_paper" in st.session_state:
            url_name, p_text = st.session_state["fetched_url_paper"]
            paper_items.append((url_name, p_text))

if paper_items:
    if st.button("🚀 Analyze Papers with Multi-Agent System"):
        if not groq_key or not langsmith_key:
            st.error("⚠️ Both Groq API Key and LangSmith API Key are required to run analysis and generate LangSmith traces.")
            st.stop()

            
        # Create collapsible workflow downbar for live sub-agent visualization
        with st.expander("🔍 View Live Sub-Agent Workflow Execution & Node Tracing", expanded=True):
            workflow_status_area = st.container()
            
        for file_idx, (paper_name, paper_text) in enumerate(paper_items):
            st.markdown(f"### 📄 Processing: **{paper_name}**")
            
            try:
                # Step 1: Initialize State & Graph
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

                # Step 2: Instantiate Workflow Graph
                app_graph = create_workflow(api_key=groq_key)

                # Dynamic Node Streaming Visualization using LangGraph app_graph.stream()
                node_labels = {
                    "analyzer": "🤖 **[Sub-Agent 1: Paper Analyzer]** Extracting methodology & core algorithms...",
                    "summarizer": "📌 **[Sub-Agent 2: Executive Summarizer]** Drafting scientific executive summary...",
                    "citation_extractor": "📚 **[Sub-Agent 3: Citation Extractor]** Collecting benchmarks & references...",
                    "key_insights": "💡 **[Sub-Agent 4: Key Insights]** Identifying practical takeaways & limitations...",
                    "reviewer": "🔍 **[Sub-Agent 5: Peer Reviewer]** Conducting quality evaluation...",
                    "boss_agent": "👑 **[Sub-Agent 6: Boss Combiner]** Synthesizing Executive Brief..."
                }

                status_placeholders = {}
                with workflow_status_area:
                    st.write(f"📥 **[Parser Engine]** Extracted text from `{paper_name}` ({len(paper_text)} characters)...")
                    for node_key, label in node_labels.items():
                        status_placeholders[node_key] = st.empty()
                        status_placeholders[node_key].markdown(f"⏳ {label}")

                final_output = dict(initial_state)
                tracer = get_langsmith_tracer(api_key=langsmith_key)
                graph_config = {"callbacks": [tracer]} if tracer else {}

                # Stream nodes real-time with explicit LangSmith tracer
                for event in app_graph.stream(initial_state, config=graph_config):
                    for node_name, node_state in event.items():
                        if node_name in status_placeholders:
                            if node_name == "reviewer":
                                score = node_state.get("review_score", 0)
                                feedback = node_state.get("review_feedback", "")
                                retries = node_state.get("retry_count", 0)
                                if score >= 7:
                                    status_placeholders[node_name].markdown(f"✅ **[Sub-Agent 5: Peer Reviewer]** Passed with Score: **{score}/10**")
                                else:
                                    status_placeholders[node_name].markdown(f"🔄 **[Sub-Agent 5: Peer Reviewer]** Score: **{score}/10** (< 7 threshold) → Triggering Retry #{retries+1} for Analyzer...")
                            else:
                                label = node_labels.get(node_name, f"Running {node_name}...")
                                status_placeholders[node_name].markdown(f"✅ {label}")

                        # Accumulate state updates
                        for k, v in node_state.items():
                            if v:
                                final_output[k] = v

                with workflow_status_area:
                    score = final_output.get("review_score", 0)
                    retries = final_output.get("retry_count", 0)
                    feedback = final_output.get("review_feedback", "")
                    
                    if score >= 7:
                        st.success(f"✅ **Quality Control Status**: Approved with Score: **{score}/10** (Retries used: {retries})")
                    else:
                        st.warning(f"⚠️ **Quality Control Status**: Completed with Score: **{score}/10** (Max retry limit 2 reached)")
                        st.info(f"Reviewer Feedback: {feedback}")
                        
                    st.success("👑 **[Sub-Agent 6: Boss Combiner Engine]** Final Executive Brief Synthesized Successfully!")


                # Results Dashboard
                col1, col2, col3 = st.columns(3)
                col1.metric("Quality Review Score", f"{final_output['review_score']} / 10")
                col2.metric("Review Retries", f"{final_output['retry_count']}")
                col3.metric("Status", "Approved ✅" if final_output['review_score'] >= 7 else "Completed with Limit ⚠️")

                # Multi-Tab Dashboard Display
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Final Brief", "🔬 Methodology", "📌 Executive Summary", "💡 Insights", "📚 Citations"])
                
                with tab1:
                    st.markdown(final_output.get("final_brief", "No brief generated."))
                    st.download_button(
                        label=f"📥 Download Complete Brief for {paper_name} (.md)",
                        data=final_output.get("final_brief", ""),
                        file_name=f"{paper_name.split('/')[-1]}_research_brief.md",
                        mime="text/markdown",
                        key=f"download_{file_idx}"
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
                        
                st.markdown("---")

            except Exception as e:
                st.error(f"❌ Error processing {paper_name}: {str(e)}")
                with workflow_status_area:
                    st.error(f"Execution Error at Sub-Agent Pipeline: {str(e)}")