"""
All prompt templates for the 9-node research pipeline.
Each prompt is designed for structured JSON output where applicable.
"""

# ─── N1: Query Intake ─────────────────────────────────────────────
QUERY_INTAKE_PROMPT = """You are a research query analyst. Your job is to take a raw user query and produce a clear, unambiguous, research-ready version.

**Raw Query:** {query}

**Instructions:**
1. Remove ambiguity and vague phrasing
2. Expand abbreviations
3. Add necessary context for web search
4. Keep the core intent intact
5. Make it suitable for academic-style research

**Respond with ONLY a JSON object:**
{{
    "refined_query": "your refined query here",
    "reasoning": "brief explanation of changes made"
}}"""


# ─── N2: Query Decomposition ─────────────────────────────────────
DECOMPOSITION_PROMPT = """You are a research strategist. Decompose the following research query into exactly 4 sub-questions that will ensure comprehensive coverage.

**Research Query:** {refined_query}

**Each sub-question must target a different dimension:**
1. **mechanism** — How does this work? What are the underlying processes?
2. **impact** — What are the effects, consequences, or outcomes?
3. **evidence** — What does the data/research say? What are the key findings?
4. **contradictions** — What are the opposing views, limitations, or debates?

**Respond with ONLY a JSON object:**
{{
    "sub_questions": [
        {{"id": "sq1", "question": "...", "type": "mechanism"}},
        {{"id": "sq2", "question": "...", "type": "impact"}},
        {{"id": "sq3", "question": "...", "type": "evidence"}},
        {{"id": "sq4", "question": "...", "type": "contradictions"}}
    ]
}}"""


# ─── N3: Autonomous Retrieval Agent ──────────────────────────────
RETRIEVAL_AGENT_PROMPT = """You are an autonomous **retrieval strategist** — NOT a summarizer. Your mission is to gather diverse, high-quality, non-redundant evidence for a set of research sub-questions.

**Research Query:** {refined_query}

**Sub-Questions to investigate:**
{sub_questions_formatted}

**YOUR BEHAVIOR:**
1. Perform MULTIPLE searches — do not stop after one search per question
2. Explore different perspectives on each sub-question
3. Ensure diversity in sources (different domains, viewpoints)
4. Prioritize depth over quantity

**YOUR STRATEGY:**
- Vary query types for each sub-question:
  - Factual queries (what, how, when)
  - Analytical queries (why, impact, analysis)
  - Opposing queries (criticisms, limitations, debates)
- Rephrase queries if initial results are insufficient
- Search for specific data, statistics, and expert opinions

**STOPPING CONDITIONS — stop ONLY when ALL are met:**
- You have ≥ 3 sources per sub-question
- You have ≥ 2 unique domains across results
- Results cover multiple perspectives (not just one viewpoint)
- Minimal redundancy (new searches add new information)

**CONSTRAINTS:**
- Maximum {max_tool_calls} tool calls total
- NEVER submit duplicate search queries
- Do NOT summarize — just retrieve
- Track which sub-question each search targets

**After completing all searches, compile your final output as a JSON object:**
{{
    "search_results": {{
        "sq1": [{{"title": "...", "content": "...", "url": "...", "domain": "..."}}],
        "sq2": [...],
        "sq3": [...],
        "sq4": [...]
    }},
    "retrieval_stats": {{
        "total_searches": <number>,
        "total_sources": <number>,
        "queries_made": ["query1", "query2", ...]
    }}
}}

Begin your systematic retrieval now."""


# ─── N4: Source Processing ────────────────────────────────────────
PROCESSING_PROMPT = """You are a source analysis expert. Process the following search results into structured analytical data.

**Research Query:** {refined_query}

**Search Results:**
{search_results_formatted}

**Your tasks:**

1. **Claim Extraction:** Extract key claims from each source. Each claim must reference its source URL.

2. **Agreement Detection:** Identify claims that multiple sources agree on.

3. **Contradiction Detection:** Identify claims where sources disagree or present opposing views.

4. **Source Scoring:** Rate each source on a 1-10 scale for:
   - **credibility** — is this a reputable source?
   - **recency** — is the information current?
   - **depth** — how detailed is the coverage?

**Respond with ONLY a JSON object:**
{{
    "claims": [
        {{"claim": "...", "source_url": "...", "source_title": "...", "sub_question_id": "..."}}
    ],
    "agreements": [
        {{"claim": "...", "supporting_sources": ["url1", "url2"], "strength": "strong|moderate|weak"}}
    ],
    "contradictions": [
        {{
            "claim_a": "...",
            "source_a": "...",
            "claim_b": "...",
            "source_b": "...",
            "nature": "brief description of the contradiction"
        }}
    ],
    "sources_with_scores": [
        {{
            "url": "...",
            "title": "...",
            "credibility": 1-10,
            "recency": 1-10,
            "depth": 1-10,
            "overall": 1-10
        }}
    ]
}}"""


# ─── N5: Synthesis ────────────────────────────────────────────────
SYNTHESIS_PROMPT = """You are a research synthesizer. Combine all processed data into coherent insights.

**Research Query:** {refined_query}

**Processed Data:**
- **Claims:** {claims_formatted}
- **Agreements:** {agreements_formatted}
- **Contradictions:** {contradictions_formatted}

**Your tasks:**
1. Identify overarching **themes** across all sub-questions
2. Determine **dominant views** (what most sources agree on)
3. Identify **minority views** (important but less-supported perspectives)
4. Map **conflicts** (unresolved disagreements)
5. Assign **confidence levels** (high/medium/low) to each insight based on evidence strength

**Respond with ONLY a JSON object:**
{{
    "themes": [
        {{"theme": "...", "description": "...", "related_sub_questions": ["sq1", "sq2"]}}
    ],
    "dominant_views": [
        {{"view": "...", "supporting_evidence": "...", "confidence": "high|medium|low"}}
    ],
    "minority_views": [
        {{"view": "...", "supporting_evidence": "...", "why_important": "..."}}
    ],
    "conflicts": [
        {{"topic": "...", "positions": ["position_a", "position_b"], "resolution_status": "unresolved|partially_resolved"}}
    ],
    "confidence_levels": {{
        "overall": "high|medium|low",
        "reasoning": "..."
    }}
}}"""


# ─── N6: Outline ──────────────────────────────────────────────────
OUTLINE_PROMPT = """You are a research report architect. Create a structured outline for a comprehensive research report.

**Research Query:** {refined_query}

**Available Insights:**
- **Themes:** {themes_formatted}
- **Dominant Views:** {dominant_views_formatted}
- **Conflicts:** {conflicts_formatted}

**Create an outline with:**
1. A compelling **title**
2. A concise **abstract** (2-3 sentences)
3. Logical **sections** that flow naturally from introduction to conclusion
4. Each section should map to specific themes/insights

**Respond with ONLY a JSON object:**
{{
    "title": "...",
    "abstract": "...",
    "sections": [
        {{
            "heading": "...",
            "purpose": "...",
            "key_points": ["...", "..."],
            "maps_to_themes": ["theme_name"]
        }}
    ]
}}"""


# ─── N7: Draft ────────────────────────────────────────────────────
DRAFT_PROMPT = """You are a research writer. Generate a comprehensive, evidence-backed research report.

**Outline:**
{outline_formatted}

**Full Insights:**
{insights_formatted}

**Processed Data (for citations):**
{processed_data_formatted}

**Writing Guidelines:**
1. Follow the outline structure exactly
2. Every claim must be backed by a citation [Source: URL]
3. Acknowledge contradictions and opposing views
4. Use clear, academic but accessible language
5. Include specific data/statistics where available
6. End each section with a brief synthesis
7. Write a proper introduction and conclusion

**Format as a well-structured Markdown document.**

{review_feedback_section}

Write the complete report now:"""


# ─── N8: Review ───────────────────────────────────────────────────
REVIEW_PROMPT = """You are a strict research quality reviewer. Evaluate the following draft report against rigorous standards.

**Original Query:** {refined_query}

**Draft Report:**
{draft}

**Review Checklist:**
1. **Coverage:** Are all sub-questions adequately addressed?
2. **Evidence:** Is every major claim backed by a source citation?
3. **Contradictions:** Are opposing views acknowledged and discussed?
4. **Vague Language:** Are there instances of "some say", "it is believed", "many think" without specific sources?
5. **Structure:** Does the report flow logically?
6. **Depth:** Is the analysis superficial or genuinely insightful?

**Respond with ONLY a JSON object:**
{{
    "passed": true/false,
    "overall_quality": "excellent|good|needs_improvement|poor",
    "gaps": [
        {{"area": "...", "description": "...", "severity": "critical|moderate|minor"}}
    ],
    "issues": [
        {{"type": "unsourced_claim|vague_language|missing_perspective|structural", "location": "...", "description": "..."}}
    ],
    "improvements": [
        "specific improvement suggestion 1",
        "specific improvement suggestion 2"
    ]
}}"""


# ─── N9: Refinement ───────────────────────────────────────────────
REFINEMENT_PROMPT = """You are a research editor. Refine the following draft into a polished final report.

**Draft Report:**
{draft}

**Review Feedback:**
{review_feedback_formatted}

**Your tasks:**
1. Address ALL issues identified in the review
2. Fill any gaps in coverage
3. Strengthen evidence where needed
4. Improve clarity and flow
5. Ensure all citations are properly formatted [Source: URL]
6. Add a final "Sources" section listing all referenced URLs

**Produce the final, polished report in Markdown format.**"""
