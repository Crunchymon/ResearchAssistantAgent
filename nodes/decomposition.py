"""
N2: Query Decomposition Node
Generates 4 sub-questions targeting: mechanism, impact, evidence, contradictions.
Temperature: 0.8 (high creativity for diverse question generation)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import DECOMPOSITION_PROMPT


def decomposition(state: ResearchState) -> dict:
    """Decompose the refined query into 4 targeted sub-questions."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["decomposition"],
    )

    prompt = DECOMPOSITION_PROMPT.format(refined_query=state["refined_query"])
    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        sub_questions = result.get("sub_questions", [])
    except (json.JSONDecodeError, AttributeError):
        # Fallback: generate basic sub-questions
        sub_questions = [
            {"id": "sq1", "question": f"How does {state['refined_query']} work?", "type": "mechanism"},
            {"id": "sq2", "question": f"What is the impact of {state['refined_query']}?", "type": "impact"},
            {"id": "sq3", "question": f"What research evidence exists for {state['refined_query']}?", "type": "evidence"},
            {"id": "sq4", "question": f"What are the criticisms of {state['refined_query']}?", "type": "contradictions"},
        ]

    return {
        "sub_questions": sub_questions,
        "current_node": "decomposition",
        "node_outputs": [{
            "node": "decomposition",
            "status": "complete",
            "message": f"Generated {len(sub_questions)} sub-questions",
            "data": {"sub_questions": sub_questions},
        }],
    }
