import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import ResearchState

load_dotenv()

def get_llm(api_key: Optional[str] = None) -> ChatGroq:
    """
    Dynamic LLM Factory: Instantiates Groq LLM with provided or environment key.
    Uses llama-3.1-8b-instant for high-speed multi-agent workflow execution without rate limits.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("Groq API Key missing! Please enter a valid API key in the sidebar.")
    return ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0.2,
        groq_api_key=key
    )

def paper_analyzer_agent(state: ResearchState, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Sub-Agent 1: Paper Analyzer
    Extracts methodology, Core Algorithms, Datasets, and addresses prior review feedback on retries.
    """
    llm = get_llm(api_key)
    feedback = state.get("review_feedback", "")
    
    extra_instruction = ""
    if feedback:
        extra_instruction = f"\n\n[IMPORTANT: Previous Peer Reviewer Feedback to address: {feedback}]\nPlease improve accuracy and completeness based on this feedback."

    prompt = ChatPromptTemplate.from_template(
        "You are an expert Scientific Research Analyst. Analyze this paper and extract methodology, core algorithms, dataset metrics, and experimental setups in detail:\n\n{paper_text}{extra_instruction}"
    )
    chain = prompt | llm
    response = chain.invoke({
        "paper_text": state["paper_text"][:14000],
        "extra_instruction": extra_instruction
    })
    return {"methodology_analysis": response.content}

def summary_generator_agent(state: ResearchState, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Sub-Agent 2: Executive Summarizer
    Generates structured scientific executive summary.
    """
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(
        "You are a Scientific Executive Summarizer. Write a clear, structured executive summary highlighting problem statement, novel contributions, and main findings:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:14000]})
    return {"executive_summary": response.content}

def citation_extractor_agent(state: ResearchState, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Sub-Agent 3: Citation Extractor
    Extracts major prior works, datasets, and literature benchmarks.
    """
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(
        "Extract all major citations, prior foundational works, and reference benchmarks from this paper. Format as a clean bulleted list:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:14000]})
    citations_list = [c.strip() for c in response.content.split("\n") if c.strip() and not c.strip().startswith("Here")]
    return {"citations": citations_list}

def key_insights_agent(state: ResearchState, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Sub-Agent 4: Key Insights Extractor
    Identifies core takeaways, real-world implications, and paper limitations.
    """
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(
        "Extract practical takeaways, key technical findings, and limitations/future work from this paper:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:14000]})
    return {"key_insights": response.content}