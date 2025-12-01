"""
Criticality Score Assessment Script

This script evaluates the quality of article classifications by sending them to a second LLM
(Minimax M2) for critical assessment. The criticality score (0-100) measures the reliability
and quality of the original classification, explanation, advice, and reasoning.

Process:
1. Fetch article_classifications with criti_status = 'WAITING' or 'FAILED'
2. For each classification, send article + classification data to Minimax M2
3. Parse the criticality score and explanation from the response
4. Update the database with the results (criti_score, criti_explanation, criti_status, criti_date)

This provides a quality assurance layer to catch poor or unreliable classifications.
"""

import os
import psycopg
from dotenv import load_dotenv
import aiohttp
import asyncio
from criti_prompt import get_api_config, get_criticality_prompt, calculate_criticality_score


def get_classifications_needing_assessment(limit: int | None = None):
    """
    Get article classifications that need criticality assessment.

    Returns classifications where:
    1. criti_status = 'WAITING' (never assessed)
    2. criti_status = 'FAILED' (assessment failed, retry)

    Only returns classifications that have been successfully classified (status = 'CLASSIFIED')
    to ensure we have data to assess.

    Returns list of tuples: (id, article_id, title, summary, classification,
                             explanation, advice, reasoning, organization_id, company_context)
    """

    load_dotenv()
    CONN_STRING = os.getenv('DATABASE_URL')
    if not CONN_STRING:
        raise RuntimeError("DATABASE_URL not found in environment variables.")

    sql = """
        SELECT
            ac.id,
            ac.article_id,
            a.title,
            a.summary,
            ac.classification,
            ac.explanation,
            ac.advice,
            ac.reasoning,
            ac.organization_id,
            o.company_context
        FROM article_classifications ac
        JOIN articles a ON ac.article_id = a.id
        JOIN organizations o ON ac.organization_id = o.id
        WHERE
            ac.status = 'CLASSIFIED'  -- Only assess successfully classified articles
            AND (ac.criti_status = 'WAITING' OR ac.criti_status = 'FAILED')
        ORDER BY ac.classification_date ASC  -- Oldest first
    """

    if limit is not None:
        sql += ' LIMIT %s'

    with psycopg.connect(CONN_STRING) as conn:
        with conn.cursor() as cursor:
            if limit is not None:
                cursor.execute(sql, (limit,))
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()

    return rows


async def assess_classification(session, title: str, summary: str, classification: str,
                                explanation: str, advice: str, reasoning: str,
                                company_context: str, api_key: str, max_retries: int = 3):
    """
    Send classification to Minimax M2 for criticality assessment.

    Args:
        session: aiohttp ClientSession
        title: Article title
        summary: Article summary
        classification: Original classification (Threat/Opportunity/Neutral)
        explanation: Original explanation
        advice: Original advice
        reasoning: Original reasoning
        company_context: Company-specific context for the organization
        api_key: Chutes API key
        max_retries: Maximum retry attempts

    Returns tuple: (response_content, finish_reason)
    Returns (None, None) on failure
    """
    api_config = get_api_config(api_key)
    url = api_config['url']
    headers = api_config['headers']
    body = get_criticality_prompt(title, summary, classification, explanation, advice, reasoning, company_context)

    for attempt in range(max_retries):
        try:
            async with session.post(url, headers=headers, json=body) as response:
                if response.status == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 2))
                    wait_time = retry_after if attempt == 0 else retry_after * (2 ** attempt)
                    print(f"  ⚠️  Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = await response.json()
                content = data['choices'][0]['message']['content'] #output ?
                finish_reason = data['choices'][0].get('finish_reason')
                return content, finish_reason

        except aiohttp.ClientResponseError as e:
            if e.status == 429 and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"  ⚠️  Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"  ✗ API Request failed: {e}")
                return None, None
        except aiohttp.ClientError as e:
            print(f"  ✗ API Request failed: {e}")
            return None, None
        except Exception as e:
            print(f"  ✗ Unexpected error during assessment: {e}")
            return None, None

    print(f"  ✗ Max retries ({max_retries}) exceeded")
    return None, None


def parse_criticality_response(response: str):
    """
    Parse the Minimax M2 response to extract individual criterion scores and explanation.

    Expected JSON format:
    {
      "scores": {
        "correctness_factual_soundness": <number 0-100>,
        "relevance_alignment": <number 0-100>,
        "reasoning_transparency": <number 0-100>,
        "practical_usefulness_actionability": <number 0-100>,
        "clarity_communication_quality": <number 0-100>,
        "safety_bias_appropriateness": <number 0-100>
      },
      "explanations": {
        "correctness_factual_soundness": "<2-3 sentence explanation>",
        "relevance_alignment": "<2-3 sentence explanation>",
        "reasoning_transparency": "<2-3 sentence explanation>",
        "practical_usefulness_actionability": "<2-3 sentence explanation>",
        "clarity_communication_quality": "<2-3 sentence explanation>",
        "safety_bias_appropriateness": "<2-3 sentence explanation>"
      },
      "overall_summary": "<overall 3-5 sentence summary>"
    }

    Returns tuple: (final_score, overall_summary, scores_dict, explanations_dict)
    The final_score is calculated by calling calculate_criticality_score() with the individual scores.
    The scores_dict contains all 6 individual criterion scores for database storage.
    The explanations_dict contains per-criterion explanations (2-3 sentences each).
    """
    import json
    import re

    if not response:
        return None, None, None, None

    try:
        # Clean the response
        response_clean = response.strip()

        # Remove markdown code blocks if present
        if response_clean.startswith('```'):
            response_clean = re.sub(r'^```(?:json)?\s*\n', '', response_clean)
            response_clean = re.sub(r'\n```\s*$', '', response_clean)

        data = json.loads(response_clean)

        # Extract the scores dictionary, explanations dictionary, and overall summary
        scores = data.get('scores')
        explanations = data.get('explanations')
        overall_summary = data.get('overall_summary', '').strip()

        # Validate scores
        if not scores or not isinstance(scores, dict):
            print(f"  ⚠️  'scores' object missing or invalid in response")
            return None, None, None, None

        # Validate explanations
        if not explanations or not isinstance(explanations, dict):
            print(f"  ⚠️  'explanations' object missing or invalid in response")
            # We'll continue but with empty explanations
            explanations = {}

        # Check that all required criterion scores are present
        required_criteria = [
            'correctness_factual_soundness',
            'relevance_alignment',
            'reasoning_transparency',
            'practical_usefulness_actionability',
            'clarity_communication_quality',
            'safety_bias_appropriateness'
        ]

        missing_criteria = [c for c in required_criteria if c not in scores]
        if missing_criteria:
            print(f"  ⚠️  Missing criterion scores: {missing_criteria}")
            # We'll proceed anyway, calculate_criticality_score defaults missing to 0

        # Calculate the final weighted score
        final_score = calculate_criticality_score(scores)

        if not overall_summary:
            overall_summary = "No overall summary provided"

        # Return final_score, overall_summary, scores dict, and explanations dict
        return final_score, overall_summary, scores, explanations

    except (json.JSONDecodeError, ValueError, AttributeError, KeyError) as e:
        print(f"  ⚠️  JSON parsing failed: {e}")
        print(f"  Raw response (first 300 chars):")
        print(f"  {response[:300]}")
        if len(response) > 300:
            print(f"  ... (total length: {len(response)} chars)")

        # Try fallback parsing - look for scores and explanations objects
        try:
            # Try to extract scores object with regex
            scores_match = re.search(r'"scores"\s*:\s*\{([^}]+)\}', response, re.DOTALL)
            overall_summary_match = re.search(r'"overall_summary"\s*:\s*"([^"]+)"', response)

            if scores_match:
                # Try to parse individual scores from the matched text
                scores_text = scores_match.group(1)
                scores = {}

                # Extract each criterion score
                for criterion in ['correctness_factual_soundness', 'relevance_alignment',
                                  'reasoning_transparency', 'practical_usefulness_actionability',
                                  'clarity_communication_quality', 'safety_bias_appropriateness']:
                    score_match = re.search(rf'"{criterion}"\s*:\s*(\d+)', scores_text)
                    if score_match:
                        scores[criterion] = int(score_match.group(1))

                # Try to extract explanations (this is harder with regex, but attempt it)
                explanations = {}
                for criterion in ['correctness_factual_soundness', 'relevance_alignment',
                                  'reasoning_transparency', 'practical_usefulness_actionability',
                                  'clarity_communication_quality', 'safety_bias_appropriateness']:
                    expl_match = re.search(rf'"{criterion}"\s*:\s*"([^"]+)"', response)
                    if expl_match:
                        explanations[criterion] = expl_match.group(1)

                if scores:
                    final_score = calculate_criticality_score(scores)
                    overall_summary = overall_summary_match.group(1) if overall_summary_match else response[:200]
                    return final_score, overall_summary, scores, explanations
        except Exception as fallback_e:
            print(f"  ⚠️  Fallback parsing also failed: {fallback_e}")

        return None, None, None, None


def update_criticality_score(
    classification_id: int,
    criti_score: int,
    criti_explanation: str,
    criti_status: str = 'GIVEN',
    scores_dict: dict = None,
    explanations_dict: dict = None
):
    """
    Update the criticality score in the database.

    Args:
        classification_id: ID of the article_classification record
        criti_score: Final weighted criticality score (0-100)
        criti_explanation: Overall summary explanation from the assessment
        criti_status: Status ('GIVEN' for success, 'FAILED' for failure)
        scores_dict: Dictionary containing individual criterion scores (optional)
        explanations_dict: Dictionary containing per-criterion explanations (optional)
    """
    load_dotenv()
    CONN_STRING = os.getenv('DATABASE_URL')
    if not CONN_STRING:
        raise RuntimeError("DATABASE_URL not found in environment variables.")

    # SQL to update article_classifications
    update_sql = """
        UPDATE article_classifications
        SET
            criti_score = %s,
            criti_explanation = %s,
            criti_status = %s,
            criti_date = NOW(),
            updated_at = NOW()
        WHERE id = %s
    """

    # SQL to insert detailed scores and explanations (using UPSERT in case of retries)
    detail_sql = """
        INSERT INTO criticality_scores_detail (
            article_classification_id,
            correctness_factual_soundness,
            relevance_alignment,
            reasoning_transparency,
            practical_usefulness_actionability,
            clarity_communication_quality,
            safety_bias_appropriateness,
            correctness_factual_soundness_explanation,
            relevance_alignment_explanation,
            reasoning_transparency_explanation,
            practical_usefulness_actionability_explanation,
            clarity_communication_quality_explanation,
            safety_bias_appropriateness_explanation
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (article_classification_id)
        DO UPDATE SET
            correctness_factual_soundness = EXCLUDED.correctness_factual_soundness,
            relevance_alignment = EXCLUDED.relevance_alignment,
            reasoning_transparency = EXCLUDED.reasoning_transparency,
            practical_usefulness_actionability = EXCLUDED.practical_usefulness_actionability,
            clarity_communication_quality = EXCLUDED.clarity_communication_quality,
            safety_bias_appropriateness = EXCLUDED.safety_bias_appropriateness,
            correctness_factual_soundness_explanation = EXCLUDED.correctness_factual_soundness_explanation,
            relevance_alignment_explanation = EXCLUDED.relevance_alignment_explanation,
            reasoning_transparency_explanation = EXCLUDED.reasoning_transparency_explanation,
            practical_usefulness_actionability_explanation = EXCLUDED.practical_usefulness_actionability_explanation,
            clarity_communication_quality_explanation = EXCLUDED.clarity_communication_quality_explanation,
            safety_bias_appropriateness_explanation = EXCLUDED.safety_bias_appropriateness_explanation,
            created_at = NOW()
    """

    try:
        with psycopg.connect(CONN_STRING) as conn:
            with conn.cursor() as cursor:
                # Update main classification table
                cursor.execute(update_sql, (criti_score, criti_explanation, criti_status, classification_id))

                # Insert detailed scores and explanations if provided and status is GIVEN
                if scores_dict and criti_status == 'GIVEN':
                    # Get explanations, default to empty string if not provided
                    if not explanations_dict:
                        explanations_dict = {}

                    cursor.execute(detail_sql, (
                        classification_id,
                        # Scores
                        scores_dict.get('correctness_factual_soundness', 0),
                        scores_dict.get('relevance_alignment', 0),
                        scores_dict.get('reasoning_transparency', 0),
                        scores_dict.get('practical_usefulness_actionability', 0),
                        scores_dict.get('clarity_communication_quality', 0),
                        scores_dict.get('safety_bias_appropriateness', 0),
                        # Explanations
                        explanations_dict.get('correctness_factual_soundness', ''),
                        explanations_dict.get('relevance_alignment', ''),
                        explanations_dict.get('reasoning_transparency', ''),
                        explanations_dict.get('practical_usefulness_actionability', ''),
                        explanations_dict.get('clarity_communication_quality', ''),
                        explanations_dict.get('safety_bias_appropriateness', '')
                    ))
        return True
    except Exception as e:
        print(f"  ✗ Failed to update criticality score for classification {classification_id}: {e}")
        return False


async def process_classifications(session, classifications, api_key):
    """
    Process all classifications needing assessment.
    """
    if not classifications:
        print("No classifications need assessment.")
        return 0, 0

    print(f"Found {len(classifications)} classifications to assess\n")

    successful = 0
    failed = 0

    # unpack tuple and assign each value to a variable
    for idx, classification in enumerate(classifications, 1):
        (
            classification_id,
            article_id,
            title,
            summary,
            class_label,
            explanation,
            advice,
            reasoning,
            organization_id,
            company_context
        ) = classification

        print(f"Processing classification {idx}/{len(classifications)} (ID: {classification_id}, Org: {organization_id})")
        print(f"  Article: {title[:60]}...")
        print(f"  Original Classification: {class_label}")

        # Assess the classification
        result = await assess_classification(
            session,
            title,
            summary or "",  # Handle None summary
            class_label,
            explanation,
            advice,
            reasoning or "",  # Handle None reasoning
            company_context,  # Company-specific context
            api_key
        )

        # Add small delay between requests
        await asyncio.sleep(0.5)

        if result and result[0] is not None:
            response_content, finish_reason = result

            if finish_reason == 'length':
                print(f"  ⚠️  Warning: Response was cut off due to token limit")

            score, criti_explanation, scores_dict, explanations_dict = parse_criticality_response(response_content)

            if score is not None:
                success = update_criticality_score(
                    classification_id,
                    score,
                    criti_explanation,
                    'GIVEN',
                    scores_dict,  # Pass the detailed scores dictionary
                    explanations_dict  # Pass the per-criterion explanations
                )

                if success:
                    print(f"  ✓ Criticality Score: {score}/100")
                    print(f"    Explanation: {criti_explanation[:80]}...\n")
                    successful += 1
                else:
                    print(f"  ✗ Failed to save criticality score\n")
                    failed += 1
            else:
                print(f"  ✗ Failed to parse assessment response\n")
                # Mark as failed in database
                update_criticality_score(
                    classification_id,
                    None,
                    "Failed to parse criticality assessment response",
                    'FAILED'
                )
                failed += 1
        else:
            print(f"  ✗ Failed to get assessment from API\n")
            # Mark as failed in database
            update_criticality_score(
                classification_id,
                None,
                "Failed to get response from criticality assessment API",
                'FAILED'
            )
            failed += 1

    return successful, failed


async def main():
    """
    Main function - assess criticality scores for all waiting/failed classifications
    """

    # Load API key
    load_dotenv()
    CHUTES_API_KEY = os.getenv('CHUTES_API_KEY')
    if not CHUTES_API_KEY:
        raise RuntimeError("CHUTES_API_KEY not found in environment variables.")

    print(f"\n{'='*80}")
    print(f"CRITICALITY SCORE ASSESSMENT")
    print(f"{'='*80}\n")

    # Get classifications needing assessment
    # You can add a limit here for testing, e.g., get_classifications_needing_assessment(limit=10)
    classifications = get_classifications_needing_assessment()

    if not classifications:
        print("✓ No classifications need criticality assessment.")
        print(f"{'='*80}\n")
        return

    # Returns list of tuples: (id, article_id, title, summary, classification,
    #                          explanation, advice, reasoning, organization_id, company_context)


    # Process classifications
    async with aiohttp.ClientSession() as session:
        successful, failed = await process_classifications(session, classifications, CHUTES_API_KEY)

    # Final summary
    print(f"\n{'='*80}")
    print(f"ASSESSMENT COMPLETE")
    print(f"{'='*80}")
    print(f"Total classifications processed: {len(classifications)}")
    print(f"Successful assessments: {successful}")
    print(f"Failed assessments: {failed}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
