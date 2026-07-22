
# LangSmith Observability test and setup validator

import os
from langsmith import Client

def check_langsmith_connection():
    """Verify that LangSmith API Key & Environment Tracing variables are configured"""
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("⚠️ Warning: LANGCHAIN_API_KEY not found in environment. Tracing disabled.")
        return False
    
    try:
        client = Client()
        projects = list(client.list_projects(limit=1))
        print("✅ LangSmith Tracing Active! Connected to Project:", os.getenv("LANGCHAIN_PROJECT"))
        return True
    except Exception as e:
        print(f"⚠️ LangSmith Connection Failed: {e}")
        return False

if __name__ == "__main__":
    check_langsmith_connection()