from typing import TypedDict, List, Optional, Dict, Any

class InterviewState(TypedDict):
    session_id: str
    problem_name: str
    user_answers: List[Dict[str, Any]]   # List of {role, content, score?}
    current_step: int
    is_complete: bool
    architecture_summary: Optional[str]
    # Temporary fields for a single turn:
    current_question: str
    current_answer: str
    retrieved_chunks: List[str]
    feedback: Optional[str]
    next_question: Optional[str]
    error: Optional[str]