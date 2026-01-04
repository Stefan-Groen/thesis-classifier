import importlib
import os
import sys


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


def load_prompt_module(prompt_module_name: str):
    """
    Dynamically load a prompt module from the prompts/ directory.

    Args:
        prompt_module_name: Name of the module (e.g., "prompt_org1" or "prompt_default")
                           without .py extension

    Returns:
        The loaded module object, or None if loading fails

    Example:
        module = load_prompt_module("prompt_org1")
        if module:
            prompt = module.get_classification_prompt(context, title, summary)
    """
    if not prompt_module_name:
        return None

    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(script_dir, "prompts")

        # Add prompts directory to Python path if not already there
        if prompts_dir not in sys.path:
            sys.path.insert(0, prompts_dir)

        # Import the module dynamically
        module = importlib.import_module(prompt_module_name)

        # Verify the module has the required function
        if not hasattr(module, 'get_classification_prompt'):
            print(f"  ⚠️  Warning: Module '{prompt_module_name}' does not have 'get_classification_prompt' function")
            return None

        return module

    except ModuleNotFoundError:
        print(f"  ⚠️  Warning: Prompt module '{prompt_module_name}' not found in prompts/ directory")
        return None
    except Exception as e:
        print(f"  ⚠️  Warning: Failed to load prompt module '{prompt_module_name}': {e}")
        return None


def get_classification_prompt(company_context: str, title: str, summary: str,
                             prompt_module_name: str = None):
    """
    Returns the complete prompt body for article classification.

    Args:
        company_context: Company-specific context for the organization
        title: Article title
        summary: Article summary
        prompt_module_name: Optional name of custom prompt module (e.g., "prompt_org1")
                          If None or not found, uses default prompt below

    Returns:
        Dictionary containing the API request body with model, messages, etc.
    """

    # Try to load organization-specific prompt module if specified
    if prompt_module_name:
        custom_module = load_prompt_module(prompt_module_name)
        if custom_module:
            try:
                return custom_module.get_classification_prompt(company_context, title, summary)
            except Exception as e:
                print(f"  ⚠️  Warning: Error calling custom prompt function: {e}")
                print(f"  ⚠️  Falling back to default prompt")

    # Default prompt (fallback when no custom prompt is specified or loading fails)
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

