from langgraph.graph import StateGraph, END
from app.agents.state import InterviewState
from app.agents.nodes import process_answer

def build_interview_graph():
    """Build and compile the LangGraph for the interview."""
    workflow = StateGraph(InterviewState)
    
    # Add nodes
    workflow.add_node("process_answer", process_answer)
    
    # Set entry point
    workflow.set_entry_point("process_answer")
    
    # Add edge to end (linear)
    workflow.add_edge("process_answer", END)
    
    return workflow.compile()