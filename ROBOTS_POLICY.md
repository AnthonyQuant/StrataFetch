# StrataFetch Ethical Scraping & Politeness Policy

StrataFetch is engineered to adhere to ethical web data acquisition standards and preserve target server stability.

---

## 📜 Politeness Implementation

### 1. Robots.txt Compliance Engine
* Prior to scraping any domain, StrataFetch fetches and parses the host's `/robots.txt` file.
* If a path is flagged under `Disallow:` for the default user-agent, execution for that URL is halted with a `SECURITY_ROBOTS_DISALLOWED` status log.

### 2. Crawl-Delay & Concurrency Caps
* **Default Domain Concurrency:** Capped at `5` concurrent HTTP requests per host domain.
* **Crawl-Delay Support:** If `Crawl-delay` is specified in `robots.txt`, execution rates are throttled accordingly.
* **Adaptive Jitter Backoff:** When an HTTP `429 Too Many Requests` status code is received, StrataFetch applies exponential backoff with random jitter before retrying.

### 3. Data Privacy & Copyright Respect
* StrataFetch is configured to acquire publicly visible opportunities, research grants, and public listings.
* Capturing authentication-gated data or bypassing paywalls/CAPTCHAs is intentionally unsupported by core extraction profiles.

---

## ⚙️ Configuration Reference

Politeness rules can be adjusted via environment variables (`.env`):

```env
ENABLE_SSRF_PROTECTION=true
MAX_CONCURRENT_REQUESTS=5
DEFAULT_REQUEST_TIMEOUT_SECONDS=30
ALLOWED_SCHEMES="http,https"