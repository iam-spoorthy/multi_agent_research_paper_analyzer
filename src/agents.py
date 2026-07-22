import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.state import ResearchState

load_dotenv()

# groq llm instance
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def paper_analyzer_agent(state: ResearchState) -> Dict[str, Any]:
    """
    Agent 1: Extracts methodology, Main Experiments and Core Concepts
    """
    prompt = ChatPromptTemplate.from_template(
        "You are an expert Research Analyst. Extract methodology, core algorithms and datasets from this paper:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:8000]}) # Truncate safety
    return {"methodology_analysis":response.content}

def summary_generator_agent(state: ResearchState) -> Dict[str, Any]:
    """Agent 2: Generates Executive Summary"""
    prompt = ChatPromptTemplate.from_template(
        "You are a Scientific Executive Summarizer. Write a concise executive summary based on:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:8000]})
    return {"executive_summary": response.content}

def citation_extractor_agent(state: ResearchState) -> Dict[str, Any]:
    """Agent 3: Extracts references and key citations"""
    prompt = ChatPromptTemplate.from_template(
        "Extract all major citations, prior works and reference benchmarks mentioned in this text:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:8000]})
    # extract lines as list
    citations_list = [c.strip() for c in response.content.split("\n") if c.strip()]
    return {"citations": citations_list}

def key_insights_agent(state: ResearchState) -> Dict[str, Any]:
    """Agent 4: Identifies core practical takeaways and limitatios"""
    prompt = ChatPromptTemplate.from_template(
        "Extract practical takeaways, key findings, and limitations from this paper:\n\n{paper_text}"
    )
    chain = prompt | llm
    response = chain.invoke({"paper_text": state["paper_text"][:8000]})
    return {"key_insights": response.content}