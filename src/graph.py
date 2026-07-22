# src/graph.py
# Quality Review Agent and LangGraph Workflow Routing Engine

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from src.state import ResearchState
from src.agents import (
    paper_analyzer_agent,
    summary_generator_agent,
    citation_extractor_agent,
    key_insights_agent,
    llm
)

# Structured Output definition for Reviewer
class ReviewOutput(BaseModel):
    score: int = Field(description="Quality score between 1 and 10 based on completeness and accuracy")
    feedback: str = Field(description="Actionable feedback for improvement if score is below 7")
    approved: bool = Field(description="True if score >= 7, else False")

def review_agent(state: ResearchState) -> dict:
    """Agent 5: Review Agent - Evaluates output quality and assigns scores (1-10)"""
    structured_llm = llm.with_structured_output(ReviewOutput)
    
    prompt = f"""
    You are a Senior Peer Reviewer. Rate the following research paper analysis on a scale of 1-10:
    
    Methodology Analysis: {state.get('methodology_analysis', '')}
    Executive Summary: {state.get('executive_summary', '')}
    Key Insights: {state.get('key_insights', '')}
    
    If any section is weak, incomplete, or uninformative, score below 7 and provide feedback.
    """
    
    review_result = structured_llm.invoke(prompt)
    current_retry = state.get("retry_count", 0) + 1
    
    return {
        "review_score": review_result.score,
        "review_feedback": review_result.feedback,
        "retry_count": current_retry
    }

def boss_agent_combiner(state: ResearchState) -> dict:
    """Agent 6: Boss Agent - Combines all approved agent outputs into a complete Brief"""
    final_brief = f"""
# 📑 Executive Research Brief

## 🎯 Executive Summary
{state.get('executive_summary', 'N/A')}

## 🔬 Methodology & Core Architecture
{state.get('methodology_analysis', 'N/A')}

## 💡 Key Insights & Takeaways
{state.get('key_insights', 'N/A')}

## 📚 Major Citations & References
""" + "\n".join([f"- {c}" for c in state.get('citations', [])])

    return {"final_brief": final_brief}

# Conditional Routing Logic (Iterative Review Loop)
def should_continue(state: ResearchState) -> str:
    """Routing Rule: Score >= 7 or Max Retries (3) reached -> Proceed to Boss Agent, else Retry"""
    if state["review_score"] >= 7 or state["retry_count"] >= 3:
        return "boss_agent"
    return "retry_analyzer"

# Workflow Graph Construction
workflow = StateGraph(ResearchState)

# Add Agent Nodes
workflow.add_node("analyzer", paper_analyzer_agent)
workflow.add_node("summarizer", summary_generator_agent)
workflow.add_node("citation_extractor", citation_extractor_agent)
workflow.add_node("key_insights", key_insights_agent)
workflow.add_node("reviewer", review_agent)
workflow.add_node("boss_agent", boss_agent_combiner)

# Set Entry Point
workflow.set_entry_point("analyzer")

# Node Connections
workflow.add_edge("analyzer", "summarizer")
workflow.add_edge("summarizer", "citation_extractor")
workflow.add_edge("citation_extractor", "key_insights")
workflow.add_edge("key_insights", "reviewer")

# Conditional Edge (Reviewer -> Boss Agent OR Retry)
workflow.add_conditional_edges(
    "reviewer",
    should_continue,
    {
        "boss_agent": "boss_agent",
        "retry_analyzer": "analyzer"
    }
)

workflow.add_edge("boss_agent", END)

# Compile Graph
app_graph = workflow.compile()