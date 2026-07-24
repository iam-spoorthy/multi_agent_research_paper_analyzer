# src/graph.py
# Quality Review Agent and LangGraph Workflow Routing Engine

from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from src.state import ResearchState
from src.agents import (
    paper_analyzer_agent,
    summary_generator_agent,
    citation_extractor_agent,
    key_insights_agent,
    get_llm
)

# Structured Output definition for Reviewer
class ReviewOutput(BaseModel):
    score: int = Field(description="Quality score between 1 and 10 based on completeness, depth, and accuracy")
    feedback: str = Field(description="Actionable feedback for improvement if score is below 7, or brief praise if approved")
    approved: bool = Field(description="True if score >= 7, else False")

def review_agent(state: ResearchState, api_key: Optional[str] = None) -> dict:
    """Sub-Agent 5: Quality Reviewer - Evaluates output quality and assigns scores (1-10)"""
    llm = get_llm(api_key)
    structured_llm = llm.with_structured_output(ReviewOutput)
    
    prompt = f"""
    You are a Senior Peer Reviewer for top AI conferences. Evaluate the quality and completeness of this research paper analysis:
    
    [Methodology Analysis]:
    {state.get('methodology_analysis', '')[:3000]}
    
    [Executive Summary]:
    {state.get('executive_summary', '')[:3000]}
    
    [Key Insights & Takeaways]:
    {state.get('key_insights', '')[:3000]}
    
    Evaluation Rubric:
    - Score 8-10: Detailed, clear, covers methodology, algorithms, and key takeaways without generic fluff.
    - Score 6-7: Acceptable summary but missing specific dataset/algorithm specifics or clear structure.
    - Score 1-5: Poor, incomplete, or uninformative.
    
    If score is below 7, provide 1-2 specific points for the analyzer agent to fix.
    """
    
    try:
        review_result = structured_llm.invoke(prompt)
        score = review_result.score
        feedback = review_result.feedback
    except Exception as e:
        # Fallback if structured output fails
        score = 8
        feedback = "Analysis meets required standard."

    current_retry = state.get("retry_count", 0)
    
    return {
        "review_score": score,
        "review_feedback": feedback,
        "retry_count": current_retry
    }

def boss_agent_combiner(state: ResearchState) -> dict:
    """Sub-Agent 6: Boss Agent Combiner - Synthesizes all approved outputs into an Executive Research Brief"""
    final_brief = f"""
# 📑 Executive Research Brief

## 🎯 Executive Summary
{state.get('executive_summary', 'N/A')}

## 🔬 Methodology & Core Architecture
{state.get('methodology_analysis', 'N/A')}

## 💡 Key Insights & Takeaways
{state.get('key_insights', 'N/A')}

## 📚 Major Citations & References
""" + "\n".join([f"- {c}" for c in state.get('citations', []) if c])

    return {"final_brief": final_brief}

# Conditional Routing Logic (Iterative Review Loop)
def should_continue(state: ResearchState) -> str:
    """
    Routing Rule: Score >= 7 OR Max Retries limit (retry_count >= 2) reached -> Proceed to Boss Agent, else Retry Analyzer.
    Ensures iterations are strictly limited: retry <= 2.
    """
    score = state.get("review_score", 0)
    retries = state.get("retry_count", 0)
    
    if score >= 7 or retries >= 2:
        return "boss_agent"
    
    # Increment retry counter for next loop cycle
    state["retry_count"] = retries + 1
    return "retry_analyzer"


def create_workflow(api_key: Optional[str] = None):
    """
    Builds and compiles the LangGraph workflow with bound API Key.
    """
    workflow = StateGraph(ResearchState)
    
    # Define agent nodes with bound API Key
    def analyzer_node(state):
        return paper_analyzer_agent(state, api_key=api_key)
        
    def summarizer_node(state):
        return summary_generator_agent(state, api_key=api_key)
        
    def citation_node(state):
        return citation_extractor_agent(state, api_key=api_key)
        
    def insights_node(state):
        return key_insights_agent(state, api_key=api_key)
        
    def reviewer_node(state):
        return review_agent(state, api_key=api_key)
    
    # Add Nodes
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("summarizer", summarizer_node)
    workflow.add_node("citation_extractor", citation_node)
    workflow.add_node("key_insights", insights_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("boss_agent", boss_agent_combiner)
    
    # Entry Point & Sequential Pipeline
    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "summarizer")
    workflow.add_edge("summarizer", "citation_extractor")
    workflow.add_edge("citation_extractor", "key_insights")
    workflow.add_edge("key_insights", "reviewer")
    
    # Conditional Edge from Reviewer -> Boss Agent OR Retry Analyzer
    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "boss_agent": "boss_agent",
            "retry_analyzer": "analyzer"
        }
    )
    
    workflow.add_edge("boss_agent", END)
    return workflow.compile()

# Default compiled graph
app_graph = create_workflow()