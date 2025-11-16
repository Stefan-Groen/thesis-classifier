# Multi-Tenant Classification Scripts

This directory now contains both the **original single-tenant scripts** and the **new multi-tenant scripts**.

## What Changed?

### Original Architecture (Single-Tenant)
```
1. Fetch articles → Store in articles table with classification columns
2. Classify articles → Update articles table with classifications
```

**Problem:** Each organization needed separate database + deployment

---

### New Architecture (Multi-Tenant)
```
1. Fetch articles → Store in articles table (no classification columns)
2. For EACH organization:
   - Get their company_context from database
   - Classify articles using their context
   - Store in article_classifications table with organization_id
```

**Benefit:** One database + deployment serves multiple organizations!

---

## File Overview

### Original Files (Keep for reference)
- `fetch-data-and-write-to-db.py` - Original single-tenant fetch script
- `LLM.py` - Original single-tenant classification script
- `company_case.txt` - Original company context (now stored in database)

### New Multi-Tenant Files
- `fetch-data-and-write-to-db_multitenant.py` - ✅ Updated fetch script
- `LLM_multitenant.py` - ✅ Updated classification script (classifies for ALL orgs)

### Unchanged Files
- `prompt_config.py` - No changes needed
- `requirements.txt` - No changes needed
- `create-db.sql` - Replaced by dashboard migrations

---

## How to Use Multi-Tenant Scripts

### Step 1: Fetch Articles (Run Once)
```bash
python3 fetch-data-and-write-to-db_multitenant.py
```

**What it does:**
- Fetches articles from RSS feeds
- Stores them in `articles` table
- Articles are shared across ALL organizations

**Output example:**
```
--> Stored 5 new articles out of 10 from https://feeds.nos.nl/nosnieuwsalgemeen
--> Stored 3 new articles out of 8 from https://feeds.nos.nl/nosnieuwsbinnenland
...
=== Run complete. Total new articles stored: 42 ===
```

---

### Step 2: Classify Articles (Run for ALL Organizations)
```bash
python3 LLM_multitenant.py
```

**What it does:**
- Fetches ALL active organizations from database
- For each organization:
  - Gets their company_context
  - Finds articles not yet classified for that org
  - Classifies using their specific context
  - Stores in `article_classifications` table

**Output example:**
```
================================================================================
MULTI-TENANT ARTICLE CLASSIFICATION
================================================================================
Found 2 active organization(s):
  - Biclou Prestige (ID: 1)
  - Company B (ID: 2)

================================================================================
Processing organization: Biclou Prestige (ID: 1)
================================================================================
Found 42 articles to classify for Biclou Prestige

[Biclou Prestige] Processing article 1/42 (ID: 123)
  Title: Shimano factory catches fire in Japan
  ✓ Classified as: Threat
    Advice: Monitor component supply chain and contact alternative suppliers...

[Biclou Prestige] Processing article 2/42 (ID: 124)
  Title: New cycling tax proposed in Netherlands
  ✓ Classified as: Neutral
    Advice: No immediate action required, monitor legislative developments...

...

================================================================================
Processing organization: Company B (ID: 2)
================================================================================
Found 42 articles to classify for Company B

[Company B] Processing article 1/42 (ID: 123)
  Title: Shimano factory catches fire in Japan
  ✓ Classified as: Neutral
    Advice: Limited impact as Company B uses different suppliers...

...

================================================================================
CLASSIFICATION COMPLETE
================================================================================
Total organizations processed: 2
Total successful classifications: 84
Total failed classifications: 0
================================================================================
```

---

## Key Differences Explained

### 1. Articles Table
**Before (Single-Tenant):**
```sql
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title TEXT,
  link TEXT UNIQUE,
  summary TEXT,
  classification VARCHAR(50),      -- ❌ Removed
  explanation TEXT,                -- ❌ Removed
  advice TEXT,                     -- ❌ Removed
  reasoning TEXT,                  -- ❌ Removed
  status VARCHAR(50),              -- ❌ Removed
  starred BOOLEAN                  -- ❌ Removed
);
```

**After (Multi-Tenant):**
```sql
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title TEXT,
  link TEXT UNIQUE,
  summary TEXT,
  -- Classification fields removed! They're now in article_classifications
);
```

### 2. New Article Classifications Table
```sql
CREATE TABLE article_classifications (
  id SERIAL PRIMARY KEY,
  article_id INTEGER REFERENCES articles(id),
  organization_id INTEGER REFERENCES organizations(id),
  classification VARCHAR(50),
  explanation TEXT,
  advice TEXT,
  reasoning TEXT,
  status VARCHAR(50),
  starred BOOLEAN,
  UNIQUE(article_id, organization_id)  -- One classification per org per article
);
```

### 3. Classification Logic

**Before:**
```python
# Get pending articles
pending = get_pending_entries()

# Classify each article
for article in pending:
    classification = classify_article(article, COMPANY_CONTEXT)
    # Update articles table
    update_database(article_id, classification)
```

**After:**
```python
# Get ALL organizations
organizations = get_all_organizations()

# For each organization
for org in organizations:
    # Get pending articles for THIS organization
    # IMPORTANT: Only articles published AFTER the org was created!
    pending = get_pending_articles_for_organization(org.id, org.created_at)

    # Classify using THIS organization's context
    for article in pending:
        classification = classify_article(article, org.company_context)
        # Insert into article_classifications with org_id
        upsert_classification(article_id, org.id, classification)
```

**Key Optimization:** When you add a new organization, only articles published **after** their `created_at` date are classified. This prevents classifying thousands of old articles that aren't relevant to them!

---

## Automation / Scheduling

You can schedule these scripts to run automatically:

### Option 1: Cron Job (Linux/Mac)
```bash
# Add to crontab: crontab -e

# Fetch new articles every hour
0 * * * * cd /path/to/thesis-classifier && python3 fetch-data-and-write-to-db_multitenant.py

# Classify articles every 30 minutes
*/30 * * * * cd /path/to/thesis-classifier && python3 LLM_multitenant.py
```

### Option 2: GitHub Actions (Recommended)
See `.github/workflows/` for automated scheduling examples

---

## Adding a New Organization

To add a new company to the system:

1. **Insert into database:**
   ```sql
   INSERT INTO organizations (name, company_context, is_active)
   VALUES (
     'New Company Name',
     'Paste their company context here...',
     true
   );
   ```

2. **Create users for that organization:**
   ```sql
   INSERT INTO users (username, password_hash, organization_id, ...)
   VALUES ('newuser', 'hash...', (SELECT id FROM organizations WHERE name = 'New Company Name'), ...);
   ```

3. **Run classifier:**
   ```bash
   python3 LLM_multitenant.py
   ```

### Important: Historical Articles

**The classifier ONLY classifies articles published AFTER the organization was created.**

**Example:**
- Database has 1,000 articles from 2024-01-01 to 2025-11-16
- You add "Company B" on 2025-11-16
- Classifier will ONLY classify articles from 2025-11-16 onwards
- The 1,000 old articles are NOT classified for Company B

**Why?**
- ✅ **Cost-effective:** Avoids thousands of unnecessary LLM API calls
- ✅ **Faster:** New organizations get started quickly
- ✅ **Relevant:** Old news isn't useful for new clients anyway

**If you WANT to classify historical articles:**
You can manually set an earlier `created_at` date:
```sql
UPDATE organizations
SET created_at = '2024-01-01'  -- Start from this date
WHERE name = 'Company B';
```
Then run `LLM_multitenant.py` to classify from that date forward.

---

## Testing

You can test with a limit to avoid processing all articles:

```python
# In LLM_multitenant.py, modify this line in main():
successful, failed = await process_organization(session, organization, CHUTES_API_KEY, limit=5)
```

This will only classify 5 articles per organization.

---

## Questions?

- **Q: Do I need to run both scripts?**
  - A: Yes! First fetch articles, then classify them.

- **Q: What if I add a new organization?**
  - A: Just run `LLM_multitenant.py` - it will automatically classify all articles for the new org.

- **Q: Can I still use the old scripts?**
  - A: The old scripts won't work with the new database structure. Use the `_multitenant` versions.

- **Q: How do I migrate from old to new?**
  - A: You already did! The SQL migration moved your existing classifications to the new structure.
