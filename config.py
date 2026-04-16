"""
Centralized configuration for the Agentic AI Research Assistant.
All tunable parameters are defined here.
"""

# ─── LLM Configuration ───────────────────────────────────────────
MODEL_NAME = "llama-3.3-70b-versatile"

# Temperature strategy per node (from the system blueprint)
TEMPERATURES = {
    "query_intake": 0.3,
    "decomposition": 0.8,
    "retrieval": 0.7,
    "processing": 0.4,
    "synthesis": 0.5,
    "outline": 0.5,
    "draft": 0.7,
    "review": 0.2,
    "refinement": 0.5,
}

# ─── Retrieval Configuration ─────────────────────────────────────
MAX_TOOL_CALLS = 15          # Hard cap on retrieval agent tool invocations
MIN_SOURCES_PER_QUESTION = 3 # Minimum sources before considering stopping
MIN_UNIQUE_DOMAINS = 2       # Minimum unique domains for diversity
MAX_SEARCH_RESULTS = 5       # Results per Tavily search call
SUB_QUESTION_COUNT = 4       # Number of sub-questions to generate

# ─── Review Loop ─────────────────────────────────────────────────
MAX_REVIEW_RETRIES = 1       # Maximum times draft can be re-generated

# ─── Node Names (for state tracking) ─────────────────────────────
NODE_NAMES = {
    "query_intake": "Query Intake",
    "decomposition": "Query Decomposition",
    "retrieval": "Autonomous Retrieval",
    "processing": "Source Processing",
    "synthesis": "Insight Synthesis",
    "outline": "Report Outline",
    "draft": "Draft Generation",
    "review": "Quality Review",
    "refinement": "Final Refinement",
}

# Ordered list for UI pipeline tracker
NODE_ORDER = [
    "query_intake",
    "decomposition",
    "retrieval",
    "processing",
    "synthesis",
    "outline",
    "draft",
    "review",
    "refinement",
]
