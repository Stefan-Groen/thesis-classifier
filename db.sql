-- ARTICLES
CREATE TABLE "articles" (
    "id" serial PRIMARY KEY,
    "title" text NOT NULL,
    "link" text NOT NULL CONSTRAINT "articles_link_key" UNIQUE,
    "summary" text,
    "date_published" timestamp with time zone,
    "source" text,
    "date_added" timestamp with time zone DEFAULT now()
);

-- ORGANIZATIONS
CREATE TABLE "organizations" (
    "id" serial PRIMARY KEY,
    "name" varchar(255) NOT NULL CONSTRAINT "organizations_name_key" UNIQUE,
    "company_context" text NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    "is_active" boolean DEFAULT true,
    "system_prompt" text DEFAULT 'You are a business analyst specializing in supply chain management, operations management and strategic analysis for the cycling industry. Your task is to analyze news articles and assess their potential impact on a company in this sector.',
    "user_prompt_template" text,
    "max_tokens" integer DEFAULT 2048,
    "temperature" numeric(3, 2) DEFAULT '0.0'
);

-- ARTICLE CLASSIFICATIONS
CREATE TABLE "article_classifications" (
    "id" serial PRIMARY KEY,
    "article_id" integer NOT NULL,
    "organization_id" integer NOT NULL,
    "classification" varchar(50),
    "explanation" text,
    "advice" text,
    "reasoning" text,
    "status" varchar(50) DEFAULT 'PENDING',
    "starred" boolean DEFAULT false,
    "classification_date" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "unique_article_org" UNIQUE("article_id","organization_id")
);

-- SUMMARIES
CREATE TABLE "summaries" (
    "id" serial PRIMARY KEY,
    "summary_date" date NOT NULL,
    "content" text NOT NULL,
    "created_at" timestamp DEFAULT now(),
    "updated_at" timestamp DEFAULT now(),
    "version" integer DEFAULT 1,
    "organization_id" integer,
    CONSTRAINT "summaries_date_version_org_unique" UNIQUE("summary_date","version","organization_id")
);

-- USERS
CREATE TABLE "users" (
    "id" serial PRIMARY KEY,
    "username" varchar(50) NOT NULL CONSTRAINT "users_username_key" UNIQUE,
    "password_hash" varchar(255) NOT NULL,
    "email" varchar(100),
    "full_name" varchar(100),
    "created_at" timestamp DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamp DEFAULT CURRENT_TIMESTAMP,
    "last_login" timestamp,
    "is_active" boolean DEFAULT true,
    "last_dashboard_visit" timestamp with time zone,
    "organization_legacy" varchar(255),
    "organization_id" integer
);

-- FOREIGN KEYS
ALTER TABLE "article_classifications"
    ADD CONSTRAINT "article_classifications_article_id_fkey"
    FOREIGN KEY ("article_id") REFERENCES "articles"("id") ON DELETE CASCADE;

ALTER TABLE "article_classifications"
    ADD CONSTRAINT "article_classifications_organization_id_fkey"
    FOREIGN KEY ("organization_id") REFERENCES "organizations"("id") ON DELETE CASCADE;

ALTER TABLE "summaries"
    ADD CONSTRAINT "fk_summaries_organization"
    FOREIGN KEY ("organization_id") REFERENCES "organizations"("id") ON DELETE CASCADE;

ALTER TABLE "users"
    ADD CONSTRAINT "users_organization_id_fkey"
    FOREIGN KEY ("organization_id") REFERENCES "organizations"("id") ON DELETE SET NULL;

-- INDEXES (only the extra ones, no duplicates of PK/UNIQUE constraints)

CREATE INDEX "idx_article_classifications_article_id" ON "article_classifications" ("article_id");
CREATE INDEX "idx_article_classifications_classification" ON "article_classifications" ("classification");
CREATE INDEX "idx_article_classifications_date" ON "article_classifications" ("classification_date");
CREATE INDEX "idx_article_classifications_organization_id" ON "article_classifications" ("organization_id");
CREATE INDEX "idx_article_classifications_starred" ON "article_classifications" ("starred");
CREATE INDEX "idx_article_classifications_status" ON "article_classifications" ("status");

CREATE INDEX "idx_articles_date" ON "articles" ("date_published");
CREATE INDEX "idx_articles_date_published" ON "articles" ("date_published");

CREATE INDEX "idx_organizations_active" ON "organizations" ("is_active");
CREATE INDEX "idx_organizations_custom_prompts" ON "organizations" ("id");
CREATE INDEX "idx_organizations_name" ON "organizations" ("name");

CREATE INDEX "idx_summaries_date" ON "summaries" ("summary_date");
CREATE INDEX "idx_summaries_date_version" ON "summaries" ("summary_date","version");
CREATE INDEX "idx_summaries_org_date" ON "summaries" ("organization_id","summary_date","version");

CREATE INDEX "idx_users_email" ON "users" ("email");
CREATE INDEX "idx_users_organization_id" ON "users" ("organization_id");
CREATE INDEX "idx_users_username" ON "users" ("username");
