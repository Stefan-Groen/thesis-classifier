"""
Organization 1 Custom Prompt Configuration

This is an EXAMPLE custom prompt for a specific organization.
You can customize the system prompt, analysis aspects, and response format here.
"""


def get_classification_prompt(company_context: str, title: str, summary: str):
    """
    Returns the complete prompt body for article classification
    CUSTOM prompt for Organization 1 - focused on technology and innovation
    """
    return {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "You are a strategic business analyst specializing in technology innovation, digital transformation, and competitive intelligence. Your task is to analyze news articles and assess their potential impact on a technology-forward company."
            },
            {
                "role": "user",
                "content": f"""COMPANY CONTEXT:
{company_context}
==================================================
NEWS ARTICLE TO ANALYZE:
Title: {title}
Summary: {summary}
==================================================
TASK:
Analyze the news article in relation to the company context as a decision-support assistant. 
Your goal is not to make decisions, but to support human judgement through structured, transparent reasoning.

Follow the analytical stages below explicitly:

STAGE 1 – IDENTIFICATION
Determine whether the article contains a potentially relevant development for the company.
If relevant, assess whether it primarily represents:
- A potential threat
- A potential opportunity
- Or no significant direct impact

STAGE 2 – MULTI-DIMENSIONAL ASSESSMENT
If relevant, assess the development across multiple analytical dimensions:
- Likely impact (low / medium / high)
- Scope of impact (operational, tactical, strategic)
- Timing (short-term vs longer-term implications)
- Degree of controllability by the company (low / medium / high)

STAGE 3 – EVIDENCE AND UNCERTAINTY
For your assessment:
- Identify which elements are strongly supported by the article (high confidence)
- Identify which elements involve ambiguity or assumptions (medium confidence)
- Identify which elements are speculative or weakly supported (low confidence)
Clearly distinguish between these confidence levels in your reasoning.

STAGE 4 – HUMAN JUDGEMENT EMPHASIS
Explicitly reflect on where human expertise is particularly important, such as:
- Contextual knowledge not present in the article
- Industry-specific nuances
- Strategic trade-offs or organizational constraints
Indicate where managerial judgement is required rather than algorithmic inference.

==================================================

CLASSIFICATION OPTIONS:
- Threat: Could negatively impact the company's business, supply chain, reputation, or operations
- Opportunity: Could benefit the company or present a strategic opportunity
- Neutral: No significant direct impact on the company

==================================================

OUTPUT FORMAT:
Provide your response as a valid JSON object with the following structure:

{
  "classification": "Threat" | "Opportunity" | "Neutral",
  "summary": "3–4 sentences summarizing what the article is about, without interpretation or impact analysis",
  "explanation": "2–3 sentences explaining the potential impact on the company, clearly distinguishing between high-, medium-, and low-confidence elements and referencing relevant aspects of the company context",
  "advice": "2–3 sentences outlining actionable recommendations, explicitly noting where human judgement or additional information is required"
}

IMPORTANT:
- Do not overstate certainty
- Make uncertainty and assumptions explicit
- Support human verification rather than automated decision-making
- Return ONLY the JSON object, without additional text or formatting
"""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }
