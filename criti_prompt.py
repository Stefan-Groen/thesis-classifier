"""
Criticality Score Prompt Configuration

This module contains the prompt templates and scoring matrix for the criticality assessment
of article classifications. The criticality score evaluates the quality and reliability of
the original LLM's classification, explanation, advice, and reasoning.

The scoring is performed by a second LLM (Minimax M2) acting as a critical evaluator.
"""

def get_api_config(api_key: str):
    """
    Get the API configuration for Chutes AI with Minimax M2 model.

    Args:
        api_key: Chutes API key from environment

    Returns:
        Dictionary with API URL and headers
    """
    return {
        "url": "https://llm.chutes.ai/v1/chat/completions",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    }


def calculate_criticality_score(scores: dict) -> int:
    """
    Calculate the final criticality score from individual criterion scores.

    Takes the 6 individual scores from the LLM and applies weights to compute
    a final criticality score (0-100).

    Args:
        scores: Dictionary containing the 6 criterion scores:
            - correctness_factual_soundness
            - relevance_alignment
            - reasoning_transparency
            - practical_usefulness_actionability
            - clarity_communication_quality
            - safety_bias_appropriateness

    Returns:
        Final criticality score (0-100) as an integer

    Weighting Strategy:
        Each criterion is weighted based on its importance for business intelligence quality.
        The weights must sum to 1.0 (100%).

    Current Weights:
        - Correctness/Factual Soundness: 25% (most critical - must be accurate)
        - Relevance & Alignment: 20% (must be relevant to article)
        - Reasoning Transparency: 20% (must show clear logic)
        - Practical Usefulness: 20% (must be actionable)
        - Clarity & Communication: 10% (important but secondary)
        - Safety/Bias: 5% (baseline requirement, rarely an issue)
    """
    # Define weights for each criterion (must sum to 1.0)
    weights = {
        "correctness_factual_soundness": 0.25,
        "relevance_alignment": 0.20,
        "reasoning_transparency": 0.20,
        "practical_usefulness_actionability": 0.20,
        "clarity_communication_quality": 0.10,
        "safety_bias_appropriateness": 0.05
    }

    # Calculate weighted average
    weighted_sum = 0.0
    for criterion, weight in weights.items():
        score = scores.get(criterion, 0)  # Default to 0 if missing
        weighted_sum += score * weight

    # Round to nearest integer and ensure it's in range [0, 100]
    final_score = int(round(weighted_sum))
    final_score = max(0, min(100, final_score))

    return final_score




def get_criticality_prompt(title: str, summary: str, classification: str,
                           explanation: str, advice: str, reasoning: str, company_context: str):
    """
    Generate the prompt for criticality assessment.

    Args:
        title: Article title
        summary: Article summary
        classification: Original LLM classification (Threat/Opportunity/Neutral)
        explanation: Original LLM explanation
        advice: Original LLM advice
        reasoning: Original LLM reasoning (thinking process)
        company_context: Company-specific context for the organization

    Returns:
        Dictionary containing model and messages for the API request
    """



    return {
    "model": "MiniMaxAI/MiniMax-M2",  # Minimax M2 model via Chutes
    "messages": [
        {
            "role": "system",
            "content": """You are a critical evaluator and quality assurance expert specializing in assessing AI-generated business intelligence classifications in the fields of Operations Management and Supply Chain Management.

Your role is to objectively evaluate the quality, accuracy, and reliability of article classifications produced by another AI system. You must be thorough, analytical, and unbiased in your assessment.

You will evaluate the output using a scoring matrix based on six criteria. For EACH criterion, you must assign an independent score from 0 to 100 (no weighting, no averaging). Another system will later combine these scores into a final weighted score.

The six criteria are:

1. Correctness / Factual Soundness
   - Does the classification and advice correctly reflect the article title and summary?
   - Are there obvious factual errors, hallucinations, or misinterpretations?

2. Relevance & Alignment
   - Is the classification/advice/explanation appropriate to the article topic and summary?
   - Is it clearly linked to the actual content of the article?

3. Reasoning Transparency
   - Is the reasoning clearly laid out, showing how it reached the classification and advice from the article summary?
   - Is the logic explicit, traceable, and non-hand-wavy?

4. Practical Usefulness / Actionability
   - Is the advice meaningful and actionable, especially in an operations/supply-chain/business context?
   - Could a practitioner reasonably use this advice to inform decisions?

5. Clarity & Communication Quality
   - Is the explanation well-structured, readable, and unambiguous?
   - Is the language concise and professional?

6. Safety / Bias / Inappropriate Content
   - Does the output avoid unethical, biased, or inappropriate reasoning or recommendations?
   - Does it avoid harmful or discriminatory assumptions?

For each criterion, independently assign a score from 0 (very poor) to 100 (excellent). Be critical but fair. Award high scores only when truly deserved. Identify specific strengths and weaknesses in a short explanation.

You MUST NOT compute any overall or weighted score. Only provide the per-criterion scores and a textual explanation."""
        },
        {
            "role": "user",
            "content": f"""COMPANY CONTEXT:
{company_context}

ORIGINAL ARTICLE:
Title: {title}
Summary: {summary}

CLASSIFICATION PROVIDED BY AI SYSTEM:
Classification: {classification}
Explanation: {explanation}
Advice: {advice}
Reasoning/Thinking: {reasoning}

TASK:
Critically evaluate this classification and its explanation, advice, and reasoning using the six criteria described in the system message.

IMPORTANT: The classification, explanation, and advice were generated specifically for the company described in the COMPANY CONTEXT above. Evaluate whether the AI system correctly understood and applied this company context in its analysis.

Step-by-step, you should:
1. Carefully compare the classification, explanation, advice, and reasoning against the article title and summary.
2. For EACH of the six criteria, independently:
   a) Assign a score from 0 to 100
   b) Write a brief explanation (2-3 sentences) justifying that specific score

   The six criteria are:
   - Correctness / Factual Soundness
   - Relevance & Alignment
   - Reasoning Transparency
   - Practical Usefulness / Actionability
   - Clarity & Communication Quality
   - Safety / Bias / Inappropriate Content

3. Be strict and consistent: similar quality should lead to similar scores across different articles.
4. Provide an overall summary explanation (3-5 sentences) highlighting the main strengths and weaknesses.

SCORE INTERPRETATION (for your internal guidance per criterion):
- 90-100: Excellent – Very strong on this criterion, no major flaws.
- 75-89:  Good – Strong on this criterion, with minor weaknesses.
- 60-74:  Acceptable – Mixed quality with clear areas for improvement.
- 40-59:  Questionable – Significant concerns on this criterion.
- 0-39:   Poor – Major flaws on this criterion.

Provide your assessment as a JSON object with:
1. A nested object "scores" containing the six per-criterion scores (0-100).
2. A nested object "explanations" containing 2-3 sentence explanations for EACH criterion score.
3. An overall summary explanation string (3-5 sentences).

Output format (valid JSON only):
{{
  "scores": {{
    "correctness_factual_soundness": <number 0-100>,
    "relevance_alignment": <number 0-100>,
    "reasoning_transparency": <number 0-100>,
    "practical_usefulness_actionability": <number 0-100>,
    "clarity_communication_quality": <number 0-100>,
    "safety_bias_appropriateness": <number 0-100>
  }},
  "explanations": {{
    "correctness_factual_soundness": "<2-3 sentence explanation for this score>",
    "relevance_alignment": "<2-3 sentence explanation for this score>",
    "reasoning_transparency": "<2-3 sentence explanation for this score>",
    "practical_usefulness_actionability": "<2-3 sentence explanation for this score>",
    "clarity_communication_quality": "<2-3 sentence explanation for this score>",
    "safety_bias_appropriateness": "<2-3 sentence explanation for this score>"
  }},
  "overall_summary": "<your 3-5 sentence overall summary>"
}}"""
        }
    ],
    "stream": False,
    "max_tokens": 2048,  # Increased to accommodate per-criterion explanations
    "temperature": 0.3
}


