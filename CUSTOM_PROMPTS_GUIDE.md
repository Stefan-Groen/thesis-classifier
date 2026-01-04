# Custom Organization Prompts - Implementation Guide

## Overview

The system now supports **organization-specific prompts** stored as Python files. Each organization can have its own custom prompt configuration by specifying a prompt module name in the database.

## How It Works

### 1. Database Configuration

In the `organizations` table, set the `user_prompt_template` field to the name of your prompt module:

```sql
-- Example: Use the prompt_org1.py file for organization ID 1
UPDATE organizations
SET user_prompt_template = 'prompt_org1'
WHERE id = 1;

-- Example: Use the default prompt for organization ID 2
UPDATE organizations
SET user_prompt_template = NULL
WHERE id = 2;
```

**Important:** Store only the module name (e.g., `prompt_org1`), **NOT** `prompt_org1.py`

### 2. Creating Custom Prompt Files

Create a new file in the `prompts/` directory:

```bash
# Create a new prompt file for your organization
touch prompts/prompt_org2.py
```

Each prompt file must contain a `get_classification_prompt()` function:

```python
def get_classification_prompt(company_context: str, title: str, summary: str):
    """
    Returns the complete prompt body for article classification
    """
    return {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "Your custom system prompt here..."
            },
            {
                "role": "user",
                "content": f"""COMPANY CONTEXT:
{company_context}

NEWS ARTICLE:
Title: {title}
Summary: {summary}

Your custom instructions here...
"""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }
```

### 3. Available Prompt Templates

- **`prompt_default.py`** - Default cycling industry prompt (original)
- **`prompt_org1.py`** - Example technology-focused prompt
- Create your own: `prompt_org2.py`, `prompt_org3.py`, etc.

## Fallback Behavior

The system has robust fallback logic:

1. **If `user_prompt_template` is NULL or empty** → Uses default prompt from `prompt_config.py`
2. **If the specified file doesn't exist** → Warning printed, uses default prompt
3. **If the file exists but has errors** → Warning printed, uses default prompt

This ensures the system **never fails** due to missing or invalid custom prompts.

## Testing Your Custom Prompt

### Step 1: Create Your Prompt File

```bash
# Copy the default template
cp prompts/prompt_default.py prompts/prompt_myorg.py

# Edit it with your custom prompt
nano prompts/prompt_myorg.py
```

### Step 2: Update Database

```sql
UPDATE organizations
SET user_prompt_template = 'prompt_myorg'
WHERE name = 'Your Organization Name';
```

### Step 3: Run Classification

```bash
python LLM_multi.py
```

You should see output like:
```
================================================================================
Processing organization: Your Organization Name (ID: 1)
Created: 2024-01-01 12:00:00+00:00
Custom Prompt: prompt_myorg
================================================================================
```

## Example Custom Prompts

### Technology Company

```python
# prompts/prompt_tech.py
def get_classification_prompt(company_context: str, title: str, summary: str):
    return {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "You are a tech industry analyst..."
            },
            {
                "role": "user",
                "content": f"""Focus on: AI, cloud, SaaS, digital transformation

Article: {title}
{summary}

Company: {company_context}"""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }
```

### Healthcare Company

```python
# prompts/prompt_healthcare.py
def get_classification_prompt(company_context: str, title: str, summary: str):
    return {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "You are a healthcare business analyst..."
            },
            {
                "role": "user",
                "content": f"""Focus on: regulations, patient care, medical tech

Article: {title}
{summary}

Company: {company_context}"""
            }
        ],
        "stream": False,
        "max_tokens": 2048,
        "temperature": 0.0
    }
```

## File Structure

```
thesis-classifier/
├── LLM_multi.py              # Main classification script (updated)
├── prompt_config.py          # Prompt loader + default fallback (updated)
├── prompts/                  # Custom prompt modules directory (NEW)
│   ├── __init__.py          # Package marker
│   ├── prompt_default.py    # Default cycling industry prompt
│   ├── prompt_org1.py       # Example tech-focused prompt
│   ├── prompt_org2.py       # Your custom prompts...
│   └── prompt_org3.py
└── CUSTOM_PROMPTS_GUIDE.md  # This guide
```

## Key Code Changes

### 1. `LLM_multi.py`
- `get_all_organizations()` now fetches `user_prompt_template` field
- `classify_article()` accepts `prompt_module_name` parameter
- `process_organization()` passes custom prompt to classification

### 2. `prompt_config.py`
- New `load_prompt_module()` function for dynamic module loading
- Updated `get_classification_prompt()` with fallback logic
- Accepts optional `prompt_module_name` parameter

## Benefits

✅ **Flexible**: Each organization can have completely different prompts
✅ **Safe**: Automatic fallback to default if custom prompt fails
✅ **Scalable**: Just add new files, no code changes needed
✅ **Database-driven**: Control which org uses which prompt via SQL
✅ **Version-controlled**: All prompts are Python files in git

## Troubleshooting

### "Module not found" warning
- Check that the file exists in `prompts/` directory
- Verify the filename matches the database value exactly
- Ensure the file has a `.py` extension

### "Missing get_classification_prompt function" warning
- Your prompt file must define `get_classification_prompt(company_context, title, summary)`
- Check function signature matches exactly

### Falls back to default unexpectedly
- Check database: `SELECT user_prompt_template FROM organizations WHERE id = X;`
- Verify no typos in the module name
- Look for Python syntax errors in your custom prompt file

## Notes

- The `system_prompt`, `max_tokens`, and `temperature` fields in the database are currently **not used** (reserved for future enhancements)
- Currently, these settings are defined **inside each prompt file**
- To change model/temperature/max_tokens, edit your prompt file's return dictionary
