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
Analyze this news article as a decision-support assistant for senior management at Ahold Delhaize, with specific attention to the role of Ahold Delhaize Inbound Logistics (ADIL).

Do NOT stop at obvious or first-order effects (e.g. direct price changes, generic trade impacts).
Instead, explicitly reason one level deeper by asking:
- How could this development indirectly affect inbound logistics decisions, planning trade-offs, or operational tensions?
- How might second-order effects propagate through forecasting, inventory positioning, warehouse operations, or multi-banner allocation?
- How could this development create knock-on effects that are not immediately visible from the article itself?

You may apply limited, reasoned creativity to explore plausible second-order consequences, but clearly distinguish between:
- Effects that are strongly implied by the article
- Effects that are plausible but uncertain

When relevant, consider the perspective of a senior logistics or supply chain executive (e.g. head of inbound logistics), rather than a generic market analyst.

==================================================

ANALYTICAL GUIDANCE:
When forming your assessment, consider indirect implications such as:
- Timing mismatches between inbound flows and warehouse or distribution capacity
- Changes in variability rather than average demand or lead time
- Effects on consolidation decisions (e.g. full container utilization vs flexibility)
- Impacts on safety stock assumptions or buffer strategies
- Differences in impact across retail banners served by ADIL
- Trade-offs between cost efficiency, service levels, and resilience

==================================================

CLASSIFICATION OPTIONS:
- Threat: Likely to create risks or negative second-order consequences for ADIL or the wider Ahold Delhaize supply chain
- Opportunity: Likely to enable beneficial second-order effects or strategic advantages
- Neutral: No meaningful second-order implications for ADIL or Ahold Delhaize operations

==================================================

OUTPUT FORMAT:
Provide your response as a valid JSON object with the following structure:

{
  "classification": "Threat" | "Opportunity" | "Neutral",
  "summary": "3–4 sentences summarizing what the article is about, without impact analysis",
  "explanation": "2–3 sentences explaining the second-order implications for Ahold Delhaize or ADIL, explicitly moving beyond obvious first-order effects",
  "advice": "2–3 sentences with concrete, actionable recommendations for management, indicating where judgement, monitoring, or scenario analysis is required"
}

IMPORTANT:
- Focus on second-order and indirect effects rather than obvious impacts
- Clearly separate implied effects from more speculative but plausible consequences
- Keep reasoning grounded in the provided company context
- Return ONLY the JSON object, without additional text or formatting
"""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }
