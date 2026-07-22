from typing import TypedDict , List, Optional , Dict, Any

class ResearchState(TypedDict):
    """
    State object passed btw nodes in LangGraph workflow
    """
    paper_text: str 
    methodology_analysis: str
    executive_summary: str
    citations: List[str]
    key_insights: str
    review_score: int
    review_feedback: str
    retry_count: int
    final_brief: str

    