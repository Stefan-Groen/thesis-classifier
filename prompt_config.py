

def get_api_config(api_key: str):
    """
    Returns the API configuration (URL and headers)
    """

    return {
        "url": "https://llm.chutes.ai/v1/chat/completions",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    }


def get_classification_prompt(company_context: str, title: str, summary: str):
    """
    Returns the complete prompt body for article classification
    """
    return {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "You are a business analyst specializing in supply chain management, operations management and strategic analysis for the cycling industry. Your task is to analyze news articles and assess their potential impact on a company in this sector."
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
Based on the detailed company context above, classify this news article and explain its potential impact on the company.

Consider (but do not limit yourself to) these aspects when analyzing:
- Supply chain implications (suppliers, logistics, shipping routes, disruptions)
- Market dynamics (demand trends, competition, regional markets)
- Strategic considerations (sponsorships, brand positioning, expansion plans)
- Operational impacts (production planning, forecasting, efficiency)
- Financial implications (costs, revenues, investments)
- Regulatory and sustainability factors
- Professional cycling developments (team sponsorships, races)
- Component supplier news (Shimano, SRAM, Giant, Kenstone, etc.)
- Geographic factors (Taiwan, China, Japan, Europe, shipping routes)

Classification Options:
- Threat: Could negatively impact the company's business, supply chain, reputation, or operations
- Opportunity: Could benefit the company or presents a strategic opportunity
- Neutral: No significant direct impact on the company

Provide your response as a valid JSON object with the following structure:
{{
  "classification": "Threat" | "Opportunity" | "Neutral",
  "summary": "3-4 sentences briefly describing what this article is about, only summarize the article, don't include impact analysis",
  "explanation": "2-3 sentences explaining the specific impact on the company, referencing relevant aspects of the company context",
  "advice": "2-3 sentences with concrete, actionable recommendations for the company's management team on how to respond to this development"
}}

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting."""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }

