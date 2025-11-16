# Classification Optimization - Historical Articles

## The Problem You Identified

**Great catch!** You noticed that when adding a new organization, the classifier would try to classify ALL existing articles in the database (potentially 1,000+).

### Why This Would Be Bad:

```
Database has 1,000 articles from January - November 2025
New Company joins on November 16, 2025

WITHOUT optimization:
❌ Classifier tries to classify all 1,000 articles
❌ 1,000 LLM API calls × $0.01 = $10+ just for one org!
❌ Takes hours to complete
❌ Most articles are irrelevant/outdated for new client
```

---

## The Solution Implemented

**Only classify articles published AFTER the organization joined.**

### How It Works:

The classifier now checks the organization's `created_at` timestamp and ONLY classifies articles with `date_published >= created_at`:

```python
def get_pending_articles_for_organization(organization_id, organization_created_at, limit=None):
    sql = """
        SELECT ...
        FROM articles a
        LEFT JOIN article_classifications ac
            ON a.id = ac.article_id AND ac.organization_id = %s
        WHERE
            (ac.id IS NULL OR ac.status = 'PENDING')
            AND a.date_published >= %s  -- 🔑 KEY FILTER!
        ORDER BY a.date_published ASC
    """
```

### Example:

```
Database has 1,000 articles:
- 950 articles from Jan 1 - Nov 15
- 50 articles from Nov 16 - Nov 30

New Company "Acme Corp" joins on Nov 16:

WITH optimization:
✅ Classifier only processes 50 articles (published after Nov 16)
✅ 50 LLM API calls × $0.01 = $0.50 (95% cost savings!)
✅ Takes minutes instead of hours
✅ Only classifies relevant, current news
```

---

## Benefits

### 1. **Cost Savings**
- 95%+ reduction in LLM API costs for new organizations
- Scales efficiently as you add more organizations

### 2. **Speed**
- New organizations get onboarded in minutes, not hours
- Users can start using the dashboard immediately

### 3. **Relevance**
- Old news from before they joined isn't relevant anyway
- Focus on current and future articles

### 4. **Scalability**
- Can add 100 organizations without performance issues
- Each only classifies articles from their join date forward

---

## Special Cases

### What if an organization WANTS historical data?

You can manually adjust their `created_at` date:

```sql
-- Example: Give them access to last 30 days of articles
UPDATE organizations
SET created_at = CURRENT_DATE - INTERVAL '30 days'
WHERE name = 'Special Client';
```

Then run the classifier, and it will classify articles from 30 days ago forward.

---

## Technical Implementation

### Files Modified:

**thesis-classifier/LLM_multitenant.py:**

1. **get_all_organizations()** - Now fetches `created_at`:
   ```python
   SELECT id, name, company_context, created_at  -- Added created_at
   FROM organizations
   ```

2. **get_pending_articles_for_organization()** - Filters by date:
   ```python
   WHERE a.date_published >= organization_created_at
   ```

3. **process_organization()** - Passes created_at:
   ```python
   org_id, org_name, company_context, org_created_at = organization
   pending = get_pending_articles_for_organization(org_id, org_created_at, limit)
   ```

---

## Example Output

When you run the classifier now:

```
================================================================================
MULTI-TENANT ARTICLE CLASSIFICATION
================================================================================
Found 2 active organization(s):
  - Biclou Prestige (ID: 1)
  - Acme Corp (ID: 2)

================================================================================
Processing organization: Biclou Prestige (ID: 1)
Created: 2025-01-01 10:00:00
================================================================================
Found 1000 articles to classify for Biclou Prestige
(Only articles published after 2025-01-01)

================================================================================
Processing organization: Acme Corp (ID: 2)
Created: 2025-11-16 14:30:00
================================================================================
Found 50 articles to classify for Acme Corp
(Only articles published after 2025-11-16)
✓ Classified as: Threat
  Advice: Monitor supply chain developments...
...
```

---

## Cost Comparison

### Scenario: 5 Organizations Over Time

**WITHOUT optimization:**
```
Month 1: Org A joins → 100 articles × 1 org = 100 classifications
Month 2: Org B joins → 200 articles × 2 orgs = 400 classifications
Month 3: Org C joins → 300 articles × 3 orgs = 900 classifications
Month 4: Org D joins → 400 articles × 4 orgs = 1,600 classifications
Month 5: Org E joins → 500 articles × 5 orgs = 2,500 classifications

Total: 5,500 classifications
Cost: $55 (at $0.01 per classification)
```

**WITH optimization:**
```
Month 1: Org A joins → 100 new articles = 100 classifications
Month 2: Org B joins → 100 new articles = 200 classifications (100 × 2 orgs)
Month 3: Org C joins → 100 new articles = 300 classifications (100 × 3 orgs)
Month 4: Org D joins → 100 new articles = 400 classifications (100 × 4 orgs)
Month 5: Org E joins → 100 new articles = 500 classifications (100 × 5 orgs)

Total: 1,500 classifications
Cost: $15 (at $0.01 per classification)

SAVINGS: 73% reduction in cost! ($40 saved)
```

---

## Key Takeaway

This optimization makes your multi-tenant system truly scalable and cost-effective. New organizations only pay for classifying articles that are actually relevant to them!

**You identified a critical optimization opportunity!** 🎯
