# backend/app/agents/nodes.py
import asyncio
import json
import re
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.logging import logger
from app.rag.retrieval import retrieve_relevant_chunks
from app.agents.state import InterviewState

# Initialize Gemini client
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


def try_parse_json(text: str) -> dict | None:
    """Attempt to parse JSON from a string with multiple strategies."""
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code block
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find the first { and last } and try to close missing braces
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try to fix common issues: trailing commas, missing closing braces
            candidate = re.sub(r',\s*}', '}', candidate)
            # Count braces
            open_braces = candidate.count('{')
            close_braces = candidate.count('}')
            if open_braces > close_braces:
                candidate += '}' * (open_braces - close_braces)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    # Strategy 4: Try to extract just the JSON keys using regex
    feedback_match = re.search(r'"feedback"\s*:\s*"([^"]*)"', text)
    next_question_match = re.search(r'"next_question"\s*:\s*"([^"]*)"', text)
    is_complete_match = re.search(r'"is_complete"\s*:\s*(true|false)', text)
    if feedback_match and next_question_match:
        return {
            "feedback": feedback_match.group(1),
            "next_question": next_question_match.group(1),
            "is_complete": is_complete_match.group(1) == "true" if is_complete_match else False,
            "architecture_summary": None
        }

    return None


async def process_answer(state: InterviewState) -> InterviewState:
    """
    Process the user's answer:
    - Retrieve relevant chunks.
    - Generate prompt with context and conversation history.
    - Call Gemini.
    - Parse the response (feedback, next question, or architecture).
    - Return updated state.
    """
    problem = state["problem_name"]
    question = state["current_question"]
    answer = state["current_answer"]

    logger.info(f"Processing: problem={problem}, question={question[:50]}...")

    # Retrieve relevant chunks
    try:
        logger.info("Retrieving relevant chunks from Qdrant...")
        chunks = await retrieve_relevant_chunks(f"{problem} design: {answer}", top_k=3)
        state["retrieved_chunks"] = chunks
        logger.info(f"Retrieved {len(chunks)} chunks.")
    except Exception as e:
        logger.error(f"Failed to retrieve chunks: {e}")
        chunks = []

    # Build conversation history
    history = state["user_answers"]
    history_text = ""
    for turn in history:
        history_text += f"{turn['role']}: {turn['content']}\n"

    # Build the prompt – ask for short JSON to keep within token limits
    prompt = f"""
You are a senior system design interviewer. The candidate is designing {problem}.

Conversation so far:
{history_text}

Now the candidate answered the following question:
Question: {question}
Answer: {answer}

Relevant knowledge (from reference material):
{chr(10).join(chunks) if chunks else "No relevant knowledge retrieved."}

Based on the candidate's answer and the reference knowledge, provide:
1. Feedback on the candidate's answer (strengths, weaknesses, suggestions) – keep it concise (max 3 sentences).
2. The next question to ask, OR if enough information has been gathered, provide an architecture summary – keep it brief.
3. A boolean flag `is_complete` (true if you're ready to give the architecture summary, else false).

IMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no extra text.
The JSON must have exactly these keys: feedback, next_question, is_complete, architecture_summary.

Example:
{{"feedback": "Good, but you missed caching.", "next_question": "How would you handle caching?", "is_complete": false, "architecture_summary": null}}
"""

    # Call Gemini with timeout
    try:
        logger.info("Calling Gemini API with timeout (30s)...")
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: gemini_client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,           # Lower for more deterministic output
                        max_output_tokens=1024,    # Increased to allow complete JSON
                    )
                )
            ),
            timeout=30.0
        )
        raw = response.text.strip()
        logger.info(f"Gemini raw response (first 500 chars): {raw[:500]}...")

        # ---- Parse JSON ----
        parsed = try_parse_json(raw)

        if parsed is None:
            logger.warning("No valid JSON found, using fallback.")
            feedback = raw[:200] + "..." if len(raw) > 200 else raw
            parsed = {
                "feedback": feedback,
                "next_question": "Can you elaborate?",
                "is_complete": False,
                "architecture_summary": None
            }
        else:
            logger.info("✅ Successfully parsed JSON.")

        # Update state
        state["feedback"] = parsed.get("feedback", "")
        state["next_question"] = parsed.get("next_question", "")
        state["is_complete"] = parsed.get("is_complete", False)
        state["architecture_summary"] = parsed.get("architecture_summary")

    except asyncio.TimeoutError:
        logger.error("Gemini API call timed out after 30 seconds.")
        state["error"] = "API timeout"
        state["feedback"] = "The request took too long. Please try again."
        state["next_question"] = "Let's move on. What are the key components of this system?"
        state["is_complete"] = False
        state["architecture_summary"] = None

    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        state["error"] = str(e)
        state["feedback"] = "I encountered an error. Please try again."
        state["next_question"] = "Let's move on. What are the key components of this system?"
        state["is_complete"] = False
        state["architecture_summary"] = None

    return state