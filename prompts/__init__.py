"""
Organization-Specific Prompt Modules

This package contains custom prompt configurations for different organizations.
Each organization can have its own prompt file (e.g., prompt_org1.py, prompt_org2.py)
that defines a get_classification_prompt() function.

The user_prompt_template field in the organizations table should contain the module name
(without .py extension) to use for that organization.

Example:
    - Organization has user_prompt_template = "prompt_org1"
    - System loads prompts/prompt_org1.py
    - Calls prompt_org1.get_classification_prompt(company_context, title, summary)
"""
