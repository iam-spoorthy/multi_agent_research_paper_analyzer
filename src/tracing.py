# LangSmith Observability test and setup validator

import os
from typing import Optional
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.tracers.langchain import LangChainTracer

def setup_langsmith_tracing(api_key: str = None, project: str = None) -> bool:
    """Configures environment variables for automatic LangChain / LangGraph tracing to LangSmith using LANGSMITH_API_KEY."""
    load_dotenv()
    
    key = api_key or os.getenv("LANGSMITH_API_KEY")
    if key and key != "your_langsmith_api_key_here":
        os.environ["LANGSMITH_API_KEY"] = key
        os.environ["LANGCHAIN_API_KEY"] = key # Internal compatibility for LangChain SDK
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
        os.environ["LANGSMITH_PROJECT"] = project or os.getenv("LANGSMITH_PROJECT", os.getenv("LANGCHAIN_PROJECT", "research-paper-analyzer"))
        os.environ["LANGCHAIN_PROJECT"] = os.environ["LANGSMITH_PROJECT"]
        return True
    return False

def get_langsmith_tracer(api_key: str = None, project: str = None) -> Optional[LangChainTracer]:
    """Returns an explicit LangChainTracer instance to guarantee trace delivery to LangSmith."""
    if setup_langsmith_tracing(api_key, project):
        project_name = project or os.getenv("LANGSMITH_PROJECT", "research-paper-analyzer")
        try:
            return LangChainTracer(project_name=project_name)
        except Exception:
            return None
    return None

def check_langsmith_connection(api_key: str = None) -> bool:
    """Verify that LangSmith API Key & Environment Tracing variables are configured and active."""
    setup_langsmith_tracing(api_key)
    key = os.getenv("LANGSMITH_API_KEY")
    
    if not key or key == "your_langsmith_api_key_here":
        print("⚠️ Warning: Valid LANGSMITH_API_KEY not found. Tracing disabled.")
        return False
    
    try:
        client = Client(api_key=key)
        projects = list(client.list_projects(limit=1))
        project_name = os.getenv("LANGSMITH_PROJECT", "research-paper-analyzer")
        print("✅ LangSmith Tracing Active! Connected to Project:", project_name)
        return True
    except Exception as e:
        print(f"⚠️ LangSmith Connection Failed: {e}")
        return False

if __name__ == "__main__":
    check_langsmith_connection()