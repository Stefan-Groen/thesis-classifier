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
Only Return the word WORKING as response

Provide your response as a valid JSON object with the following structure:
{{
  "classification": "WORKING"",
  "summary": "WORKING",
  "explanation": "WORKING",
  "advice": "WORKING"
}}

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting."""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }
