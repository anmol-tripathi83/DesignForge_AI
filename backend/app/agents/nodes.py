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


def extract_json_from_text(text: str) -> dict | None:
    """
    Aggressively extract JSON from a string using multiple strategies.
    """
    if not text:
        return None
    
    # Clean the text
    text = text.strip()
    
    # Strategy 1: Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code block
    code_block_patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]
    for pattern in code_block_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
    
    # Strategy 3: Find the first { and last } and extract
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and start < end:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try to fix common issues
            # Fix 1: Remove trailing commas before closing braces
            candidate = re.sub(r',\s*}', '}', candidate)
            # Fix 2: Add missing closing braces
            open_braces = candidate.count('{')
            close_braces = candidate.count('}')
            if open_braces > close_braces:
                candidate += '}' * (open_braces - close_braces)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
    
    # Strategy 4: Manual extraction of key-value pairs (fallback)
    try:
        feedback_match = re.search(r'"feedback"\s*:\s*"([^"]*)"', text)
        next_question_match = re.search(r'"next_question"\s*:\s*"([^"]*)"', text)
        is_complete_match = re.search(r'"is_complete"\s*:\s*(true|false)', text)
        arch_summary_match = re.search(r'"architecture_summary"\s*:\s*("[^"]*"|null)', text)
        
        if feedback_match:
            result = {
                "feedback": feedback_match.group(1),
                "next_question": next_question_match.group(1) if next_question_match else "Can you elaborate?",
                "is_complete": is_complete_match.group(1) == "true" if is_complete_match else False,
                "architecture_summary": None
            }
            if arch_summary_match:
                arch_value = arch_summary_match.group(1)
                if arch_value != "null":
                    result["architecture_summary"] = arch_value.strip('"')
            return result
    except Exception:
        pass
    
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

    # Build the prompt
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
2. The next question to ask, OR if enough information has been gathered, provide an architecture summary.
3. A boolean flag `is_complete` (true if you're ready to give the architecture summary, else false).
4. **CRITICAL: If `is_complete` is true, you MUST provide a non-null `architecture_summary`.** 
   The summary must include a Mermaid diagram (in a code block with ```mermaid) describing the high-level architecture. 
   Keep the summary concise but include key components, data flow, and interactions.
   If `is_complete` is false, set `architecture_summary` to null.

IMPORTANT: Return ONLY valid JSON. No markdown, no explanation, no extra text outside the JSON.
The JSON must have exactly these keys: feedback, next_question, is_complete, architecture_summary.

Example (complete):
{{"feedback": "Good, you covered caching.", "next_question": "", "is_complete": true, "architecture_summary": "Here is the architecture diagram:\n```mermaid\ngraph TD\n    A[Client] --> B[Load Balancer]\n    B --> C[App Servers]\n    C --> D[Database]\n```"}}

Example (not complete):
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
                        temperature=0.3,
                        max_output_tokens=1024,
                    )
                )
            ),
            timeout=30.0
        )
        raw = response.text.strip()
        logger.info(f"Gemini raw response (first 500 chars): {raw[:500]}...")

        # ---- Extract JSON ----
        parsed = extract_json_from_text(raw)

        if parsed is None:
            logger.warning("No valid JSON found, using fallback.")
            # Try to extract feedback manually as last resort
            feedback = raw[:200] + "..." if len(raw) > 200 else raw
            parsed = {
                "feedback": feedback,
                "next_question": "Can you elaborate?",
                "is_complete": False,
                "architecture_summary": None
            }
        else:
            logger.info("✅ Successfully parsed JSON.")
            # Ensure all keys exist
            parsed = {
                "feedback": parsed.get("feedback", ""),
                "next_question": parsed.get("next_question", "Can you elaborate?"),
                "is_complete": parsed.get("is_complete", False),
                "architecture_summary": parsed.get("architecture_summary"),
            }

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