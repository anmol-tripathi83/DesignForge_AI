import asyncio 
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.session import InterviewSession
from app.models.message import Message
from app.agents.graph import build_interview_graph
from app.agents.state import InterviewState
from app.core.logging import logger
from app.schemas.message import MessageResponse

class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = build_interview_graph()

    async def process_answer(self, session_id: UUID, user_answer: str) -> dict:
        """Process user answer, run the agent, and update DB."""
        # Fetch session with messages
        result = await self.db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.messages))
            .where(InterviewSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")

        # Build conversation history from messages
        history = []
        for msg in session.messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
                "score": msg.score,
            })

        # Determine current question: the last question asked by assistant
        last_assistant_msg = next((m for m in reversed(session.messages) if m.role == "assistant"), None)
        current_question = last_assistant_msg.content if last_assistant_msg else f"Describe the high-level architecture of {session.problem_name}."

        # Prepare state
        state: InterviewState = {
            "session_id": str(session.id),
            "problem_name": session.problem_name,
            "user_answers": history,
            "current_step": session.current_step,
            "is_complete": False,
            "architecture_summary": None,
            "current_question": current_question,
            "current_answer": user_answer,
            "retrieved_chunks": [],
            "feedback": None,
            "next_question": None,
            "error": None,
        }

        # Invoke the graph
        logger.info(f"Processing answer for session {session_id}")

        try:
            final_state = await asyncio.wait_for(
                self.graph.ainvoke(state),  # This is the correct async method
                timeout=45.0
            )
        except asyncio.TimeoutError:
            logger.error("Graph execution timed out after 45 seconds.")
            # Create a fallback state
            final_state = state
            final_state["feedback"] = "The response took too long. Please try again or rephrase your answer."
            final_state["next_question"] = "Let's continue. What are the key components of this system?"
            final_state["is_complete"] = False
            final_state["architecture_summary"] = None
        except Exception as e:
            logger.error(f"Graph execution failed: {e}", exc_info=True)
            final_state = state
            final_state["feedback"] = "I encountered an error. Please try again."
            final_state["next_question"] = "Let's continue with the next question."
            final_state["is_complete"] = False
            final_state["architecture_summary"] = None

        # Save user message
        user_msg = Message(
            session_id=session.id,
            role="user",
            content=user_answer,
            score=None,  # We'll compute score later if needed
        )
        self.db.add(user_msg)

        # Save assistant message
        assistant_msg = Message(
            session_id=session.id,
            role="assistant",
            content=final_state.get("feedback", "") + "\n\nNext question: " + final_state.get("next_question", ""),
            score=None,
        )
        self.db.add(assistant_msg)

        # Update session
        if final_state.get("is_complete"):
            session.status = "completed"
            session.current_step = final_state.get("current_step", 0) + 1
        else:
            session.current_step = final_state.get("current_step", 0) + 1

        # If architecture summary is provided, store it (could be in a separate field)
        if final_state.get("architecture_summary"):
            # Optionally store in a separate table or as a message
            # For simplicity, we'll add as assistant message
            arch_msg = Message(
                session_id=session.id,
                role="assistant",
                content=f"Architecture Summary:\n{final_state['architecture_summary']}",
                score=None,
            )
            self.db.add(arch_msg)
            session.status = "completed"

        await self.db.commit()

        # Return response to client
        return {
            "feedback": final_state.get("feedback", ""),
            "next_question": final_state.get("next_question", ""),
            "is_complete": final_state.get("is_complete", False),
            "architecture_summary": final_state.get("architecture_summary"),
        }