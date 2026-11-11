# StrataFetch Architecture & Technical Specification

StrataFetch is an enterprise-grade, asynchronous Web Data Acquisition, Extraction, and Monitoring Platform engineered in Python with FastAPI, SQLAlchemy, and Playwright.

---

## 1. System Context & Top-Level Architecture

```text
                       ┌─────────────────────────────────────┐
                       │         Client Interactions         │
                       │    (Web Dashboard UI / REST APIs)   │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              StrataFetch Core Engine                              │
│                                                                                   │
│  ┌───────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐  │
│  │   Security Gate   │────►│  Fetching Pipeline   │────►│  Extraction Engine   │  │
│  │  (SSRF / Robots)  │     │ (HTTPX / Playwright) │     │ (CSS / XPath / LXML) │  │
│  └───────────────────┘     └──────────────────────┘     └───────────┬──────────┘  │
│                                                                     │             │
│  ┌───────────────────┐     ┌──────────────────────┐                               │
│  │ Telemetry Logging │◄────│  Data Normalizer &   │◄────────────────┘             │
│  │  & Audit Tracker  │     │  Quality Assurance   │                               │
│  └───────────────────┘     └──────────────────────┘                               │
│                                                                                   │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
                       ┌────────────────────────────────────┐
                       │      Database & Export Engine      │
                       │   (SQLite/PostgreSQL & Webhooks)   │
                       └────────────────────────────────────┘
```

---

## 2. Security & Compliance Controls (Layered Defense)

StrataFetch enforces strict politeness protocols and infrastructure security prior to dispatching network requests:

1. **Layer A – Protocol & Scope Limits:** Restricts outbound targets strictly to `http` and `https` schemas.
2. **Layer B – Infrastructure & SSRF Protection:** Pre-resolves domain IP addresses against blocked subnets (Loopback `127.0.0.1`, RFC1918 Private ranges `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, Link-Local `169.254.0.0/16`, and AWS/GCP Metadata IPs).
3. **Layer C – Politeness & Rate-Limiting:** Reads and enforces `robots.txt` directives per domain, applies adaptive jitter backoff on HTTP `429 Too Many Requests`, and enforces concurrency caps.

---

## 3. End-to-End Ingestion Lifecycle

1. **Submission & Validation:** A target URL is submitted manually, scheduled via cron background workers, or queued in multi-page crawling mode.
2. **Fetching Layer Selection:** Static HTTP requests are processed asynchronously using `httpx`. Dynamic Single Page Applications (SPAs) are routed to headless Chromium via `Playwright` for client-side JavaScript execution.
3. **Extraction & Replay:** Raw HTML DOM is parsed using BeautifulSoup or LXML tree structures based on defined extraction profile rules (`css_selector`, `xpath`, `meta_tag`, `link_attribute`).
4. **Data Normalization & Cleaning:** Extracted strings are cleaned, relative URLs are resolved to absolute links, currencies are parsed into structured decimal amounts, and dates are converted to ISO-8601 strings.
5. **Quality Assurance & Deduplication:** Records undergo type validation and required-field checks, generating a quality score report while removing duplicates using MD5 field hashes.
6. **Persistence & Dispatch:** Standardized entities (e.g., Opportunities) are saved into the ORM database, telemetry execution logs are stored, and webhooks are triggered for newly discovered records.

---

## 4. Entity-Relationship Overview

* **`ScrapeSessionModel`**: Tracks job metadata, profile configuration, total yield, and execution timestamps.
* **`RecordSnapshotModel`**: Stores raw DOM string representations for visual historical diffing and offline extraction replay.
* **`ExecutionLogModel`**: Stores HTTP status codes, request latencies, SSRF security blocks, and error details.
* **`OpportunityModel`**: Domain entity storing standardized student and early-career opportunities (Title, Organisation, Location, Eligibility, Deadline, Application URL).