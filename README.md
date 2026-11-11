# ⚡ StrataFetch: Web Data Acquisition & Monitoring Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)

**StrataFetch** is an enterprise-grade, asynchronous web data acquisition, extraction, and historical DOM monitoring platform.

Designed with quantitative precision, the platform features multi-layered security guards (SSRF protection and ethical scraping rules), automated data quality scoring, visual DOM snapshot diffing, and webhook change alerting.

Built with **FastAPI**, **SQLAlchemy**, **Playwright**, and **LXML**, StrataFetch bridges static HTTP fetching with dynamic Single Page Application (SPA) rendering to convert unstructured web content into validated, clean structured datasets.

---

## 🎯 Key Capabilities

- 🚀 **Hybrid Dual-Engine Fetching:** High-throughput static page fetching via `httpx` alongside headless Chromium browser rendering via `Playwright` for dynamic JavaScript SPAs (infinite scroll, network idle state hydration).

- 🛡️ **Layered Security & Ethical Scraping:** Pre-flight IP validation blocking loopback and private subnets (SSRF defense), automated `robots.txt` compliance, domain concurrency caps, and exponential backoff on HTTP `429` rate limits.

- 🧩 **Declarative Extraction Profiles:** CSS Selector, XPath, and Meta Tag rule definition with strong data type coercion (URLs, ISO dates, currency amounts with ISO-4217 code standardization).

- 📂 **Historical Snapshot Diffing & Replay:** Offline DOM snapshot comparison, visual layout structural change detection, and extraction replay without re-querying target hosts.

- 📊 **Data Quality & Yield Telemetry:** Automated completeness and schema compliance scoring, missing field identification, MD5-based record deduplication, and execution log metrics.

- 🔔 **Automated Event Alerts:** Real-time webhook dispatches on newly discovered records or deadline change events.

- 🖥️ **Interactive UI Suite:** Built-in dark-themed monitoring dashboard, interactive visual DOM selector builder, and target tracking console.

---

## 🏗️ System Architecture & Data Flow

```text
                  ┌─────────────────────┐
                  │    API / Dashboard  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    Security Layer   │
                  │                     │
                  │ Protocol Verification
                  │ SSRF Block          │
                  │ Robots.txt Check    │
                  └──────────┬──────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  ▼                     ▼
        ┌─────────────────┐   ┌────────────────────┐
        │  Static Fetch   │   │   Dynamic Fetch   │
        │    (HTTPX)      │   │   (Playwright)    │
        └────────┬────────┘   └─────────┬──────────┘
                 │                      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Parsing &             │
                 │ Normalization         │
                 │                      │
                 │ LXML / CSS Extraction │
                 │ Type Coercion         │
                 │ MD5 Dedup             │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Quality Control &    │
                 │ Storage              │
                 │                      │
                 │ Quality Scoring       │
                 │ Snapshot ORM         │
                 │ Webhook Alerts       │
                 └──────────────────────┘
```

---

## 📈 Performance Instrumentation Benchmark

Evaluated over **1,008 extraction iterations** on standardized target DOM snapshots (`scripts/run_benchmark.py`).

| Metric | Measured Value | Target SLA | Status |
|---|---:|---:|---|
| **Mean Parse Latency** | 1.42 ms / page | < 10.0 ms | 🟢 Optimal |
| **Parsing Throughput** | 704.2 ops/sec | > 500 ops/sec | 🟢 Optimal |
| **Peak RAM Consumption** | 14.8 MB | < 50 MB | 🟢 Optimal |
| **Schema Yield Compliance** | 100.0% | > 98.0% | 🟢 Optimal |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites

- Python `3.10` or higher
- Node.js runtime (optional, for standalone Playwright dependencies)

### 2. Setup Environment

```bash
# Clone repository
git clone https://github.com/AnthonyQuant/StrataFetch.git

cd StrataFetch

# Create and activate virtual environment
python -m venv venv

source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright Chromium
playwright install chromium
```

### 3. Initialize & Run

```bash
# Start Uvicorn application server
uvicorn app.main:app --reload
```

Navigate to:

`http://127.0.0.1:8000`

to access the interactive platform dashboard.

---

## 🧪 Testing & Verification

StrataFetch includes an extensive offline test suite operating against saved HTML DOM fixtures to guarantee deterministic execution independent of external network stability.

```bash
# Run pytest suite
python -m pytest tests/ -v

# Run performance benchmark suite
python scripts/run_benchmark.py
```

---

## 🔌 API Reference Overview

The API is fully documented via OpenAPI (Swagger UI) at:

`http://127.0.0.1:8000/docs`

Key endpoint suites include:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/crawler/crawl` | Initiate asynchronous multi-page crawling job |
| POST | `/api/browser/render` | Hydrate dynamic SPA pages via headless Chromium |
| POST | `/api/opportunities/ingest` | Ingest and normalize domain opportunities |
| GET | `/api/opportunities` | Query tracked opportunities with filters |
| POST | `/api/exporter/export` | Stream dataset exports in CSV, JSON, or JSONL |
| GET | `/api/health` | System health check and runtime status |

---

## 📜 Ethical Scraping & Security Policy

StrataFetch is designed in strict adherence to web standards and responsible data scraping practices:

1. **Infrastructure Isolation:** Blocks outbound connections to private IP spaces to eliminate Server-Side Request Forgery risks.

2. **Politeness Compliance:** Honors domain `robots.txt` disallow paths and crawl delays.

3. **Data Privacy:** Cleans private credentials and personally identifiable information prior to persistent storage.