"""
Multi-Tenant Article Classification Script

This script classifies articles for ALL organizations in the database.
Each article is classified separately for each organization using their specific company context.

Key Changes from Original:
- Fetches ALL active organizations from database
- Classifies each pending article for each organization
- Stores results in article_classifications table (not articles table)
- Uses organization-specific company context for each classification
"""

import os
import psycopg
from dotenv import load_dotenv
import aiohttp
import asyncio
from prompt_config import get_api_config, get_classification_prompt


def get_all_organizations():
    """
    Fetch all active organizations from the database
    Returns list of tuples: (id, name, company_context, created_at)
    """
    load_dotenv()
    CONN_STRING = os.getenv('DATABASE_URL')
    if not CONN_STRING:
        raise RuntimeError("DATABASE_URL not found in environment variables.")

    sql = """
        SELECT id, name, company_context, created_at
        FROM organizations
        WHERE is_active = TRUE
        ORDER BY id
    """

    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

    return rows


def get_pending_articles_for_organization(organization_id: int, organization_created_at, limit: int | None = None):
    """
    Get articles that need classification for a specific organization

    IMPORTANT: Only returns articles published AFTER the organization was created.
    This prevents classifying thousands of old articles for new organizations.

    Returns articles that either:
    1. Have no classification record for this organization yet
    2. Have a PENDING status for this organization
    AND were published after the organization was created
    """
    load_dotenv()
    CONN_STRING = os.getenv('DATABASE_URL')
    if not CONN_STRING:
        raise RuntimeError("DATABASE_URL not found in environment variables.")

    sql = """
        SELECT
            a.id,
            a.title,
            a.summary,
            a.date_published,
            a.source
        FROM articles a
        LEFT JOIN article_classifications ac
            ON a.id = ac.article_id
            AND ac.organization_id = %s
        WHERE
            (ac.id IS NULL OR ac.status = 'PENDING')  -- No classification or pending
            AND a.date_published >= %s  -- Only articles published after org was created
        ORDER BY a.date_published ASC
    """

    if limit is not None:
        sql += ' LIMIT %s'

    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cursor:
            if limit is not None:
                cursor.execute(sql, (organization_id, organization_created_at, limit))
            else:
                cursor.execute(sql, (organization_id, organization_created_at))
            rows = cursor.fetchall()

    return rows


async def classify_article(session, title: str, summary: str, api_key: str, company_context: str):
    """
    Sends a single article to LLM for classification
    Returns the classification result and explanation
    """
    api_config = get_api_config(api_key)
    url = api_config['url']
    headers = api_config['headers']
    body = get_classification_prompt(company_context, title, summary)

    try:
        async with session.post(url, headers=headers, json=body) as response:
            response.raise_for_status()
            data = await response.json()
            content = data['choices'][0]['message']['content']
            reasoning = data['choices'][0]['message'].get("reasoning_content")
            finish_reason = data['choices'][0].get('finish_reason')
            return content, reasoning, finish_reason
    except aiohttp.ClientError as e:
        print(f"API Request failed: {e}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error during classification: {e}")
        return None, None, None


def parse_llm_response(response: str):
    """
    Parse the LLM response to extract classification, explanation, and advice
    Returns tuple: (classification, explanation, advice)
    """
    if not response:
        return None, None, None

    lines = response.strip().split('\n')
    classification = None
    explanation = None
    advice = None

    for line in lines:
        if line.startswith("Classification:"):
            classification = line.replace("Classification:", "").strip()
        elif line.startswith("Explanation:"):
            explanation = line.replace("Explanation:", "").strip()
        elif line.startswith("Advice:"):
            advice = line.replace("Advice:", "").strip()

    # Validate Classification
    valid_classifications = {'Threat', 'Opportunity', 'Neutral'}
    if classification not in valid_classifications:
        classification = "Error: Unknown"

    if not explanation:
        explanation = response

    if not advice:
        advice = "No specific advice provided"

    return classification, explanation, advice


def upsert_classification(
    article_id: int,
    organization_id: int,
    classification: str,
    explanation: str,
    advice: str,
    reasoning: str,
    status: str = 'CLASSIFIED'
):
    """
    Insert or update article classification in the database
    Uses UPSERT (INSERT ... ON CONFLICT UPDATE) to handle existing records
    """
    load_dotenv()
    CONN_STRING = os.getenv('DATABASE_URL')
    if not CONN_STRING:
        raise RuntimeError("DATABASE_URL not found in environment variables.")

    sql = """
        INSERT INTO article_classifications (
            article_id,
            organization_id,
            classification,
            explanation,
            advice,
            reasoning,
            status,
            classification_date,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (article_id, organization_id)
        DO UPDATE SET
            classification = EXCLUDED.classification,
            explanation = EXCLUDED.explanation,
            advice = EXCLUDED.advice,
            reasoning = EXCLUDED.reasoning,
            status = EXCLUDED.status,
            classification_date = NOW(),
            updated_at = NOW()
    """

    try:
        with psycopg.connect(CONN_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    article_id,
                    organization_id,
                    classification,
                    explanation,
                    advice,
                    reasoning,
                    status
                ))
        return True
    except Exception as e:
        print(f"Failed to upsert classification for article {article_id}, org {organization_id}: {e}")
        return False


async def process_organization(session, organization, api_key, limit=None):
    """
    Process all pending articles for a single organization
    """
    org_id, org_name, company_context, org_created_at = organization

    print(f"\n{'='*80}")
    print(f"Processing organization: {org_name} (ID: {org_id})")
    print(f"Created: {org_created_at}")
    print(f"{'='*80}")

    # Get articles that need classification for this organization
    # Only articles published AFTER the organization was created
    pending_articles = get_pending_articles_for_organization(org_id, org_created_at, limit)

    if not pending_articles:
        print(f"✓ No pending articles for {org_name} (only checking articles after {org_created_at.date()})")
        return 0, 0

    print(f"Found {len(pending_articles)} articles to classify for {org_name}")
    print(f"(Only articles published after {org_created_at.date()})\n")

    successful = 0
    failed = 0

    for idx, article in enumerate(pending_articles, 1):
        article_id = article[0]
        title = article[1]
        summary = article[2]

        print(f"[{org_name}] Processing article {idx}/{len(pending_articles)} (ID: {article_id})")
        print(f"  Title: {title[:60]}...")

        # Classify the article using this organization's context
        result = await classify_article(session, title, summary, api_key, company_context)

        if result:
            llm_response_content, llm_response_reasoning, finish_reason = result

            if finish_reason == 'length':
                print(f"  ⚠️  Warning: Response was cut off due to token limit")

            classification, explanation, advice = parse_llm_response(llm_response_content)

            if classification and explanation:
                success = upsert_classification(
                    article_id,
                    org_id,
                    classification,
                    explanation,
                    advice,
                    llm_response_reasoning or ""
                )

                if success:
                    print(f"  ✓ Classified as: {classification}")
                    print(f"    Advice: {advice[:60]}...\n")
                    successful += 1
                else:
                    print(f"  ✗ Failed to save classification\n")
                    failed += 1
            else:
                print(f"  ✗ Failed to parse LLM response\n")
                upsert_classification(
                    article_id,
                    org_id,
                    None,
                    None,
                    None,
                    None,
                    status='FAILED (to parse response)'
                )
                failed += 1
        else:
            print(f"  ✗ Failed to get LLM response\n")
            upsert_classification(
                article_id,
                org_id,
                None,
                None,
                None,
                None,
                status='FAILED (no response)'
            )
            failed += 1

    return successful, failed


async def main():
    """
    Main function - classifies articles for ALL organizations
    """
    # Load API key
    load_dotenv()
    CHUTES_API_KEY = os.getenv('CHUTES_API_KEY')
    if not CHUTES_API_KEY:
        raise RuntimeError("CHUTES_API_KEY not found in environment variables.")

    # Get all active organizations
    organizations = get_all_organizations()

    if not organizations:
        print("No active organizations found in database.")
        return

    print(f"\n{'='*80}")
    print(f"MULTI-TENANT ARTICLE CLASSIFICATION")
    print(f"{'='*80}")
    print(f"Found {len(organizations)} active organization(s):")
    for org in organizations:
        print(f"  - {org[1]} (ID: {org[0]})")
    print()

    # Process each organization
    total_successful = 0
    total_failed = 0

    async with aiohttp.ClientSession() as session:
        for organization in organizations:
            successful, failed = await process_organization(session, organization, CHUTES_API_KEY)
            total_successful += successful
            total_failed += failed

    # Final summary
    print(f"\n{'='*80}")
    print(f"CLASSIFICATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total organizations processed: {len(organizations)}")
    print(f"Total successful classifications: {total_successful}")
    print(f"Total failed classifications: {total_failed}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
