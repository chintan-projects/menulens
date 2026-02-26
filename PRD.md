# MenuLens — Product Requirements Document

**Competitive Menu Pricing Intelligence via Semantic Extraction**

Author: Chintan Sanghvi
Date: February 2026
Status: Pre-build / Exploration

---

## 1. Problem Statement

Restaurant owners make pricing decisions with half the picture. Tools like Toast, Square, and xtraCHEF solve the **internal** cost side — ingredient costs, food cost percentage, COGS tracking. But the **external** side — what are my direct competitors actually charging for comparable dishes? — remains manual, anecdotal, or invisible.

Today, a restaurant owner who wants competitive pricing data either:

- Drives around and checks competitor menus by hand
- Browses websites one by one (many are outdated PDFs or images)
- Checks DoorDash/UberEats (inflated 15-30%, not real dine-in prices)
- Hires a consultant
- Guesses

None of these scale. None update automatically. None give a structured, comparable view.

Meanwhile, the data **exists** — scattered across restaurant websites, PDF menus, delivery platforms, social media, and Google Maps listings. The problem isn't data availability; it's data heterogeneity. Every source structures menu information differently, and traditional scraping requires per-source extraction rules that break constantly.

### Why This Matters Financially

Toast's own research: a restaurant serving 350 customers/day that misprices by $0.75 per item loses ~$100K/year. Competitive pricing intelligence isn't a nice-to-have — it's a direct revenue lever.

---

## 2. Product Vision

**MenuLens** is a competitive menu pricing intelligence tool for restaurant operators. It discovers competitor menus in a target region, extracts dish names and prices across heterogeneous sources (HTML, PDF, delivery platforms, images), normalizes dish categories, and delivers a structured competitive pricing view.

### The Underlying Technology Bet

The core enabling technology is a **semantic extraction layer** — an LLM-based pipeline that replaces per-source scraping rules with a single model-driven extraction step. The model understands what a "dish name" and "price" mean semantically, regardless of how the source structures its markup.

This extraction layer is the **reusable, transferable asset**. If the restaurant pricing product doesn't find market fit, the same extraction SDK applies to any domain with heterogeneous unstructured sources and a target schema (real estate listings, job postings, event pricing, product catalogs).

### What MenuLens Is NOT

- Not a generic price comparison website (Yelp, Google already aggregate loosely)
- Not a delivery platform (not competing with DoorDash/UberEats)
- Not an internal food costing tool (not competing with Toast/xtraCHEF)
- Not a web scraping service (not competing with Zyte, Apify, FoodSpark)

MenuLens is **intelligence from extraction** — the value is in the structured, normalized, comparable output, not in the raw data access.

---

## 3. Target Users

### Primary: Independent Restaurant Owners & Operators

- Own 1-5 locations
- Set their own menu prices (no corporate mandate)
- Operate in competitive local markets (urban/suburban, not rural)
- Currently price by gut feel + occasional manual competitor checks
- Price-sensitive on software ($50-150/month range)

### Secondary: Restaurant Groups & Multi-Unit Operators

- 5-50+ locations across regions
- Need regional pricing strategy (same dish, different price by market)
- Have ops/analytics staff who would use the tool regularly
- Higher willingness to pay ($200-500/month)

### Tertiary (Validation Only — Don't Build For These Yet)

- Food consultants advising restaurants on pricing
- Commercial real estate firms evaluating restaurant viability
- Food delivery platforms wanting pricing benchmarks

---

## 4. Core User Stories

### P0 — Must Have for MVP

1. **As a restaurant owner**, I can enter my location and cuisine type and see a list of competing restaurants in my area with their menu items and prices, so I can understand my competitive landscape.

2. **As a restaurant owner**, I can search for a specific dish (e.g., "chicken tikka masala") and see what every competitor in my area charges for it, so I can price my own version competitively.

3. **As a restaurant owner**, I can see my dishes benchmarked against local competitors — am I priced above, below, or at the median — so I can identify mispriced items.

4. **As a restaurant owner**, I can define my geographic radius (1mi, 3mi, 5mi, 10mi) to control which competitors are included in my comparison set.

### P1 — Important for Retention

5. **As a restaurant owner**, I get notified when a competitor changes their prices, so I can respond quickly.

6. **As a restaurant owner**, I can see price trends over time (are competitors raising prices? by how much?) so I can plan my own price changes.

7. **As a restaurant owner**, I can filter by cuisine type, price tier, or restaurant style (fast casual vs. fine dining) to compare against relevant competitors only.

8. **As a restaurant owner**, I can export my competitive pricing data as a spreadsheet for offline analysis or to share with partners.

### P2 — Differentiators

9. **As a restaurant owner**, the system discovers new competitors automatically when they open in my area.

10. **As a restaurant owner**, I can see estimated food cost percentages for competitor dishes (based on ingredient price databases) alongside their menu prices, giving me margin intelligence not just price intelligence.

---

## 5. System Architecture

### High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        MenuLens Pipeline                        │
│                                                                 │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────┐│
│  │ Discovery  │──▶│  Fetching  │──▶│ Extraction │──▶│ Normal-││
│  │            │   │            │   │            │   │ ization ││
│  │ - Google   │   │ - HTML     │   │ - LLM-based│   │         ││
│  │   Maps API │   │ - PDF      │   │ - Schema-  │   │ - Dish  ││
│  │ - Yelp     │   │ - Delivery │   │   enforced │   │   match ││
│  │ - Manual   │   │   platform │   │ - Multi-   │   │ - Dedup ││
│  │   add      │   │   scrape   │   │   format   │   │ - Categ.││
│  └────────────┘   └────────────┘   └────────────┘   └────────┘│
│                                                         │       │
│                                                         ▼       │
│  ┌────────────┐   ┌────────────┐   ┌──────────────────────────┐│
│  │ Monitoring │◀──│  Storage   │◀──│  Pricing Intelligence    ││
│  │            │   │            │   │                          ││
│  │ - Change   │   │ - Postgres │   │ - Competitor benchmarks  ││
│  │   detect   │   │ - PostGIS  │   │ - Percentile rankings    ││
│  │ - Alerts   │   │ - Time-    │   │ - Trend analysis         ││
│  │ - Re-fetch │   │   series   │   │ - Price change alerts    ││
│  └────────────┘   └────────────┘   └──────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 5.1 Discovery Service

**Purpose:** Find restaurants in a target area with their menu source URLs.

**Data Sources:**
- Google Maps / Places API (primary — gives name, location, website, cuisine tags)
- Yelp Fusion API (supplementary — menus, photos, categories)
- DoorDash/UberEats/Grubhub public listings (delivery platform menus)
- User-submitted URLs (manual override for sources the system misses)

**Output:** Restaurant record with metadata + list of candidate menu source URLs.

#### 5.2 Fetching Service

**Purpose:** Retrieve raw menu content from discovered source URLs.

**Challenges (don't underestimate these):**
- PDF menus (common — many restaurants just upload a PDF)
- Image-only menus (photographed paper menus on social media / Google)
- JavaScript-rendered pages (SPAs that need headless browser execution)
- Anti-bot protections on delivery platforms
- Authentication walls (some ordering systems require interaction)

**Approach:**
- HTML pages: `httpx` + `BeautifulSoup` for static, `Playwright` for JS-rendered
- PDFs: Download + extract text via `pymupdf` or vision model for scanned PDFs
- Images: Vision model (see Model Recommendations below)
- Delivery platforms: Structured data extraction from public listing pages where available; avoid heavy scraping that violates ToS

#### 5.3 Extraction Service (Core — The Semantic Layer)

**Purpose:** Convert raw menu content (any format) into structured JSON conforming to the MenuLens schema.

**Target Schema:**

```json
{
  "restaurant_name": "string",
  "source_url": "string",
  "extraction_timestamp": "ISO-8601",
  "menu_sections": [
    {
      "section_name": "string (e.g., 'Appetizers', 'Main Course')",
      "items": [
        {
          "dish_name": "string",
          "description": "string | null",
          "price": "float",
          "price_variants": [
            {"label": "small", "price": 8.99},
            {"label": "large", "price": 12.99}
          ],
          "currency": "string (default: USD)",
          "dietary_tags": ["vegetarian", "gluten-free"],
          "spice_level": "string | null"
        }
      ]
    }
  ],
  "extraction_confidence": "float (0-1)",
  "raw_source_type": "html | pdf | image | delivery_platform"
}
```

**How it works:**
1. Raw content is cleaned/preprocessed (strip nav, footers, ads for HTML; OCR for images)
2. Content is passed to the extraction model with the target schema
3. Output is validated against schema (Pydantic)
4. Low-confidence extractions are flagged for review or retry with a stronger model

#### 5.4 Normalization Service

**Purpose:** Make dishes comparable across restaurants.

**This is the hardest technical problem in the system.** "Chicken Tikka Masala" vs "Tikka Masala (Chicken)" vs "Chicken Tikka" vs "CTM" need to map to the same canonical dish for comparison to work.

**Approach:**
- Embedding-based similarity (sentence-transformers) to cluster dish names
- Cuisine-specific taxonomy (maintained per cuisine type — Indian, Italian, Mexican, etc.)
- LLM-assisted categorization for ambiguous cases
- Human-in-the-loop for initial taxonomy building; automated once patterns stabilize

**Canonical Dish Schema:**

```json
{
  "canonical_id": "uuid",
  "canonical_name": "Chicken Tikka Masala",
  "cuisine": "Indian",
  "category": "Main Course / Curry",
  "aliases": ["Tikka Masala Chicken", "CTM", "Chicken Tikka"],
  "typical_price_range": {"low": 14.0, "high": 22.0, "median": 17.5}
}
```

#### 5.5 Storage & Intelligence Layer

**Purpose:** Store extracted data with geospatial and temporal dimensions; compute pricing intelligence.

**Key Queries the System Must Support:**
- "What do restaurants within 5 miles charge for [dish]?" (geospatial + dish lookup)
- "Where does my price for [dish] rank among local competitors?" (percentile)
- "How have prices for [dish] in [area] changed over the past 6 months?" (time-series)
- "Which of my dishes are priced >20% above/below local median?" (anomaly detection)

---

## 6. Tech Stack Recommendation

### Backend

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| **Language** | Python 3.12 | ML/LLM ecosystem is Python-native. FastAPI for API layer. No need to optimize for language-level performance — the bottleneck is model inference, not framework overhead. |
| **API Framework** | FastAPI | Async-native, Pydantic integration for schema validation, OpenAPI docs for free. You already know it from project-alpha. |
| **Database** | PostgreSQL 16 + PostGIS | Geospatial queries are first-class (find restaurants within X miles). TimescaleDB extension for time-series price tracking. Battle-tested, free. |
| **Task Queue** | Celery + Redis | Menu fetching and extraction are async batch jobs, not real-time requests. Celery handles scheduling (re-fetch menus weekly), retries, and failure tracking. |
| **Caching** | Redis | Cache extracted menu data, geocoding results, frequently-queried comparisons. |
| **Search / Similarity** | pgvector (PostgreSQL extension) | Dish name embeddings stored alongside relational data. No need for a separate vector DB at this scale. |
| **Object Storage** | S3-compatible (MinIO locally, S3 in prod) | Store raw fetched content (HTML snapshots, PDFs, images) for audit trail and re-extraction. |
| **Frontend** | React + TypeScript + Vite | Simple dashboard. Not the hard part. Can start with a CLI tool and add frontend later. |

### Why Not [Alternative]?

- **Django instead of FastAPI?** Heavier than needed. You're building an API + worker pipeline, not a content management system. FastAPI's async and Pydantic integration are better fits.
- **MongoDB instead of PostgreSQL?** You need geospatial queries (PostGIS), time-series (TimescaleDB), and relational joins (restaurant → menu → items → comparisons). Postgres does all three. Mongo would require bolting on geo and time-series separately.
- **Separate vector DB (Pinecone, Weaviate)?** Overkill at this scale. pgvector handles dish name similarity search in Postgres directly. You'd need maybe 100K dish embeddings — pgvector handles that trivially.

---

## 7. Model Recommendations

This is the critical decision. Here's a tiered strategy — use the right model for each job rather than one model for everything.

### Tier 1: Menu Extraction (Core — Runs on Every Menu)

**Candidate A: LFM2-8B-A1B (Liquid AI, open weights, MoE architecture)**

- Architecture: 8.3B total parameters, but only **1.5B active per token** (Mixture-of-Experts with 32 experts, top-4 routing). This means you get 8B-class knowledge with 1.5B-class inference speed and cost.
- 32K context length — sufficient for even the longest menus.
- Liquid AI **explicitly recommends this model for data extraction** and agentic tasks. Menu extraction is squarely in its design target.
- On-device capable: Runs quantized (Q4_0 ~4.7GB) via `llama.cpp` (build b6709+), `ExecuTorch`, or `vLLM`. Can run on a laptop with no GPU for development.
- Multilingual support (English, Spanish, French, Chinese, Arabic, Japanese, Korean) — useful for menus in multilingual areas.
- Training mix is 60% English / 25% multilingual / 15% code — the code training helps with structured JSON output.
- IFEval score of 77.6 (instruction following) and strong performance on structured benchmarks suggest it will follow JSON schema instructions reliably.
- Structured output: Use with `Instructor` library (Pydantic schema enforcement) or `Outlines` for constrained decoding.
- License: LFM Open License v1.0 (commercial use permitted).

**Candidate B: Llama 3.2-3B-Instruct (Meta, open source, dense)**

- Why evaluate alongside LFM2: Similar effective compute class (LFM2's 1.5B active path vs. Llama's 3B dense), giving a fair speed comparison while testing whether the MoE architecture's broader knowledge base helps extraction accuracy.
- 128K context length.
- Larger community ecosystem, more tooling support, and more inference hosting options.
- Well-tested with Instructor and Outlines for structured output.
- Hosting: Locally via `ollama` or `vLLM`. Cloud via Together AI, Fireworks, Groq.

**Evaluation Plan (Week 1 of MVP):**

Run both models on the same 20 restaurant menus (diverse formats) and compare:
- Extraction accuracy (dish name + price correctness, manually verified)
- Schema compliance (does the output parse cleanly into Pydantic?)
- Inference speed (tokens/second on target hardware)
- Failure modes (what does each model get wrong?)

Pick the winner based on accuracy first, speed second. The losing model becomes the backup.

**Fallback: Claude Sonnet (via API)**

- For menus where the primary model's extraction confidence is below threshold (<0.8)
- Frontier model catches edge cases: unusual layouts, ambiguous pricing, multi-language menus
- More expensive per call, but only used for ~5-15% of extractions

**Future Exploration: LFM2-2.6B (Liquid AI, dense)**

- If LFM2-8B-A1B proves accurate, explore whether the smaller 2.6B dense variant can handle the task after LoRA fine-tuning on menu extraction specifically.
- Advantage: ~240 tok/s on CPU, <1GB memory — could enable edge deployment or extremely cheap cloud inference.
- Risk: May need 5,000+ labeled training examples to match the larger model's zero-shot performance. Worth exploring in Phase 2 once you have labeled data from Phase 1.

### Tier 2: Image/PDF Menu OCR + Extraction (Multimodal)

**Primary: Qwen2.5-VL-7B-Instruct or LLaVA-v1.6 (open source, vision-language)**

- Why: Handles scanned PDF menus and photographed menu boards directly — no separate OCR step needed. Send the image, get structured JSON back.
- This is a meaningful percentage of restaurant menus (many are just a photo or scanned PDF).
- Note: LFM2-8B-A1B is text-only — it cannot process images directly. For image menus, you need a dedicated vision model.
- Alternative: Claude Sonnet (strong vision capabilities) for image tasks if open source quality isn't sufficient.

### Tier 3: Dish Normalization (Embedding + Classification)

**Primary: all-MiniLM-L6-v2 or BGE-small (sentence-transformers, open source)**

- Generate embeddings for dish names
- Cluster similar dishes using cosine similarity
- Tiny models (~80MB), run locally instantly, no API cost

**Supplementary: LFM2-8B-A1B or Claude API (whichever is primary extraction model)**

- For ambiguous cases: "Is 'Paneer Butter Masala' the same dish as 'Butter Paneer'?"
- LLM-as-judge for dish equivalence decisions during taxonomy building
- Used in batch during normalization pipeline, not in real-time

### Tier 4: Integration Slug Generation (Async, One-Time Per Source)

**Recommendation: Claude API (Sonnet or Opus)**

- When the system encounters a new source type that needs a custom fetcher (unusual auth, pagination, JavaScript rendering), use Claude to generate the connector code.
- This is async and one-time per source — cost is irrelevant (pennies).
- Claude Code API can generate, test, and iterate on the connector code autonomously.
- This is your "integration factory" concept from the original POV doc — use it as a Phase 2 differentiator.

### Model Strategy Summary

| Task | Model | Active Params | Where | Cost |
|------|-------|--------------|-------|------|
| Menu extraction (candidate A) | LFM2-8B-A1B | 1.5B active (8.3B total) | Local (llama.cpp/vLLM) | Free (compute only) |
| Menu extraction (candidate B) | Llama 3.2-3B-Instruct | 3B | Local or cloud API | Free local / ~$0.10/1M tokens cloud |
| Menu extraction (fallback) | Claude Sonnet | — | API | ~$3/1M tokens |
| Menu extraction (image/PDF) | Qwen2.5-VL-7B or LLaVA | 7B | Cloud API or local | ~$0.15/1M tokens |
| Dish normalization (embed) | all-MiniLM-L6-v2 | 22M | Local | Free |
| Dish normalization (judge) | Primary extraction model or Claude | — | Local or API | Minimal |
| Integration slug generation | Claude Sonnet/Opus | — | API | ~$0.10/slug |
| Fine-tuning exploration (Phase 2) | LFM2-2.6B | 2.6B | Local | Free (compute only) |
| Fine-tuning exploration | LFM2-2.6B | 2.6B | Local | Free (compute only) |

---

## 8. Data Model (PostgreSQL)

```sql
-- Core entities
CREATE TABLE restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    address TEXT,
    cuisine_types TEXT[],              -- ['indian', 'pakistani']
    google_place_id TEXT UNIQUE,
    website_url TEXT,
    menu_source_urls TEXT[],           -- discovered menu URLs
    price_tier TEXT,                   -- 'budget', 'mid', 'upscale', 'fine_dining'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE menu_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id),
    fetched_at TIMESTAMPTZ NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL,         -- 'html', 'pdf', 'image', 'delivery_platform'
    raw_content_path TEXT,             -- S3 path to raw fetched content
    extraction_model TEXT,             -- 'qwen2.5-7b', 'claude-sonnet', etc.
    extraction_confidence FLOAT,
    extracted_data JSONB NOT NULL,     -- full structured extraction
    is_latest BOOLEAN DEFAULT TRUE     -- flag for current snapshot
);

CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id UUID REFERENCES menu_snapshots(id),
    restaurant_id UUID REFERENCES restaurants(id),
    dish_name TEXT NOT NULL,
    canonical_dish_id UUID REFERENCES canonical_dishes(id),
    section_name TEXT,
    price NUMERIC(8,2) NOT NULL,
    price_variants JSONB,             -- [{"label": "small", "price": 8.99}]
    description TEXT,
    dietary_tags TEXT[],
    currency TEXT DEFAULT 'USD',
    is_current BOOLEAN DEFAULT TRUE
);

CREATE TABLE canonical_dishes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT NOT NULL,
    cuisine TEXT NOT NULL,
    category TEXT,                     -- 'appetizer', 'main', 'dessert', etc.
    aliases TEXT[],
    embedding VECTOR(384),            -- for similarity search via pgvector
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Geospatial index for "restaurants within X miles"
CREATE INDEX idx_restaurants_location ON restaurants USING GIST(location);

-- Time-series index for price trend queries
CREATE INDEX idx_menu_items_restaurant_dish ON menu_items(restaurant_id, canonical_dish_id, is_current);

-- Composite for "current prices for dish in area"
CREATE INDEX idx_menu_items_canonical ON menu_items(canonical_dish_id) WHERE is_current = TRUE;
```

---

## 9. MVP Scope (Phase 1 — 4-6 Weekends)

### Constraint: One Cuisine, One City

Pick a single cuisine type (Indian food recommended — rich menu variety, standardized-ish dish names, personal familiarity) in one metro area.

### What to Build

1. **Discovery script** — Use Google Maps Places API to find all Indian restaurants within a radius. Store names, locations, website URLs. (~1 weekend)

2. **Fetching pipeline** — Fetch menu content from discovered URLs. Handle HTML and PDF. Skip image-only menus for MVP. (~1 weekend)

3. **Extraction pipeline** — Pass fetched content through Qwen2.5-7B with Instructor/Pydantic schema enforcement. Store structured output. (~1 weekend)

4. **Normalization (basic)** — Embedding-based clustering of dish names. Manual review of clusters to build initial canonical dish taxonomy for Indian food. (~1 weekend)

5. **Comparison API + simple UI** — FastAPI endpoints: `GET /compare?dish=chicken-tikka-masala&lat=...&lng=...&radius=5mi`. Simple React dashboard showing price distribution. (~1-2 weekends)

6. **Validation** — Show the working prototype to 5 restaurant owners. Record reactions. (~1 weekend)

### What NOT to Build in Phase 1

- Price change monitoring / alerts
- Automatic re-fetching
- Multi-cuisine normalization
- Image menu extraction
- Integration slug auto-generation
- User accounts / authentication
- Payment / subscription

### Phase 1 Success Criteria

- Extract menus from 50+ restaurants in target area
- Extraction accuracy ≥90% on dish name + price (manually verified on 20 restaurants)
- Dish normalization correctly groups ≥85% of common dishes
- At least 3 of 5 restaurant owners shown the demo say "I would use this"
- Total cloud/API cost for the full pipeline run < $20

---

## 10. Phase 2 — If Phase 1 Validates (Months 2-4)

- Multi-cuisine support (expand normalization taxonomy)
- Scheduled re-fetching (weekly) with change detection
- Price trend tracking (time-series queries)
- Image/PDF menu support via vision model
- Email/SMS alerts on competitor price changes
- User accounts + saved restaurant profiles
- Stripe integration for subscription billing

## Phase 3 — Growth & SDK (Months 4-8)

- Extract the semantic extraction layer into a standalone SDK
- Integration slug generation via Claude Code API
- Support non-restaurant verticals (validate extraction layer generalization)
- Public API for third-party integrations
- Toast/Square/Clover integration exploration

---

## 11. Key Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Extraction accuracy insufficient on diverse menus** | High | Start with one cuisine to constrain variance. Use fallback to larger model for low-confidence extractions. Fine-tune if needed. |
| **Menu source access (anti-bot, JS rendering, ToS)** | High | Prioritize HTML and PDF menus. Use delivery platform structured data where available. Don't scrape aggressively — this is a low-frequency batch job (weekly), not real-time. |
| **Dish normalization errors** | Medium | Start with human-in-the-loop taxonomy. Use embeddings + LLM judge. Accept that normalization will be imperfect at launch and improve iteratively. |
| **Restaurant owners won't pay** | Medium | Validate willingness-to-pay before building billing. Consider freemium (free for basic, paid for alerts + trends). If owners won't pay, pivot to selling to restaurant groups or consultants. |
| **Toast/DoorDash builds this natively** | Medium | Move fast. They have data advantages but are slow to ship niche features. Your advantage is focus. Also: they only see their own customers' data; you see the whole market. |
| **Data freshness** | Medium | Display "last updated" prominently. Re-fetch on a schedule. Flag stale data (>30 days) visually. |

---

## 12. Open Questions (Decide Before Building)

1. **Which metro area for MVP?** Pick a city you know, with enough Indian restaurants to be meaningful (50+). Good candidates: Bay Area, NYC, Chicago, Houston, DFW.

2. **Delivery platform data: use or avoid?** DoorDash/UberEats have structured menu data but inflated prices and ToS restrictions. Decision: use for discovery (which dishes exist), but prefer restaurant's own website for pricing.

3. **Hosting for MVP:** Local development with ollama (free) vs. cloud API for extraction (cheap but not free). Recommendation: start local, move to cloud when you need to run batch extraction on 50+ restaurants.

4. **Open source from day one?** If the extraction SDK is the long-term play, open-sourcing MenuLens could build credibility and community. But it also lets competitors see your approach. Decision: open source the SDK layer, keep the pricing intelligence product proprietary.

---

## 13. Project Structure

```
menulens/
├── PRD.md                          # This document
├── src/
│   ├── discovery/                  # Restaurant discovery (Google Maps, Yelp)
│   │   ├── google_maps.py
│   │   └── models.py
│   ├── fetching/                   # Raw content retrieval
│   │   ├── html_fetcher.py
│   │   ├── pdf_fetcher.py
│   │   └── models.py
│   ├── extraction/                 # LLM-based semantic extraction
│   │   ├── extractor.py            # Core extraction logic
│   │   ├── schemas.py              # Pydantic models for menu schema
│   │   ├── prompts.py              # Extraction prompts per source type
│   │   └── models.py               # Model client abstraction
│   ├── normalization/              # Dish name normalization
│   │   ├── embeddings.py
│   │   ├── taxonomy.py
│   │   └── matcher.py
│   ├── intelligence/               # Pricing intelligence computations
│   │   ├── comparison.py
│   │   ├── trends.py
│   │   └── alerts.py
│   ├── api/                        # FastAPI application
│   │   ├── main.py
│   │   ├── routes/
│   │   └── dependencies.py
│   └── config/
│       └── settings.py
├── tests/
├── scripts/                        # One-off scripts for data collection
├── data/                           # Local data (gitignored)
│   ├── raw/                        # Fetched HTML/PDF snapshots
│   └── extracted/                  # Extraction outputs
├── pyproject.toml
├── docker-compose.yml              # Postgres + Redis + app
└── .env.example
```

---

## 14. References & Resources

### Models

- [LFM2-8B-A1B on HuggingFace](https://huggingface.co/LiquidAI/LFM2-8B-A1B) — Primary extraction candidate
- [LFM2-8B-A1B Blog Post](https://www.liquid.ai/blog/lfm2-8b-a1b-an-efficient-on-device-mixture-of-experts) — Architecture details & benchmarks
- [LFM2-2.6B on HuggingFace](https://huggingface.co/LiquidAI/LFM2-2.6B-Exp) — Phase 2 fine-tuning candidate
- [Llama 3.2-3B on HuggingFace](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) — Alternative extraction candidate
- [Qwen2.5-VL-7B on HuggingFace](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) — Vision model for image menus

### Libraries

- [Instructor](https://github.com/jxnl/instructor) — Structured output from LLMs via Pydantic
- [Outlines](https://github.com/outlines-dev/outlines) — Constrained LLM generation
- [vLLM](https://github.com/vllm-project/vllm) — Fast LLM serving
- [sentence-transformers](https://www.sbert.net/) — Dish name embeddings

### Benchmarks

- [LLMStructBench (Feb 2026)](https://arxiv.org/html/2602.14743v1) — Structured extraction benchmark
- [StructEval (Dec 2025)](https://arxiv.org/html/2505.20139v1) — Structural output benchmark

### Market Context

- [Toast Menu Price Monitor](https://pos.toasttab.com/blog/data/menu-price-monitor)
- [Toast Food Cost Guide](https://pos.toasttab.com/blog/on-the-line/how-to-calculate-food-cost-percentage)
- [Liquid AI LFM2 Technical Report](https://arxiv.org/abs/2511.23404)
- [Liquid AI Cookbook](https://github.com/Liquid4All/cookbook)

### Existing Players (Competitive Awareness)

- [FoodSpark](https://www.foodspark.io/) — Food data scraping API
- [Zyte](https://www.zyte.com/data-types/restaurant-data-scraping/) — Restaurant data extraction
- [Diffbot](https://www.diffbot.com/) — ML-based web extraction (general purpose)
