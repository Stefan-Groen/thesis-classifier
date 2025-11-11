

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
Based on the detailed company context above, classify this news article and explain its potential impact on Biclou Prestige.

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
- Threat: Could negatively impact Biclou's business, supply chain, reputation, or operations
- Opportunity: Could benefit Biclou or presents a strategic opportunity
- Neutral: No significant direct impact on Biclou

Provide your response in the following format:
Classification: [Threat/Opportunity/Neutral]
Explanation: [2-3 sentences explaining the specific impact on Biclou, referencing relevant aspects of the company context]"""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.5
    }

