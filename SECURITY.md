# StrataFetch Security & Vulnerability Disclosure Policy

## 🛡️ Security Architecture & Defense Layers

StrataFetch implements a three-tier security model to protect infrastructure and prevent malicious use during data acquisition jobs.

### Layer A: Protocol & Scheme Validation
* **Allowed Protocols:** Outbound network requests are strictly confined to `http://` and `https://` schemes.
* **Blocked Protocols:** Execution of file system URLs (`file://`), loopback aliases (`gopher://`), shell commands (`ftp://`, `ssh://`), or arbitrary socket connections is blocked prior to request dispatch.

### Layer B: Server-Side Request Forgery (SSRF) Protection
Before initializing any static HTTP fetch (`httpx`) or dynamic browser context (`Playwright`), target hostnames are resolved to IP addresses and evaluated against restricted IP space tables:

* **Loopback Interfaces:** `127.0.0.0/8`, `::1/128`
* **Private Subnets (RFC 1918):** `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
* **Link-Local & Multicast:** `169.254.0.0/16`, `224.0.0.0/4`
* **Cloud Provider Metadata Endpoints:** `169.254.169.254` (AWS/GCP/Azure IMDS)

Redirect chains are re-validated at each step to prevent HTTP 30x redirect bypass attacks.

### Layer C: Request Sanitization & Credential Isolation
* **User-Agent Management:** Standardized browser user-agent headers are attached to identify traffic responsibly.
* **Secret Scrubbing:** Authorization headers, tokens, and basic auth credentials are scrubbed from execution log persistent stores.

---

## 🔒 Reporting a Vulnerability

If you discover a security vulnerability within StrataFetch, please report it responsibly:

1. **Email Contact:** Open a private issue or email `anthonyomokpo6489@gmail.com`.
2. **Details to Include:** Provide a description of the issue, step-by-step proof-of-concept (PoC), and potential impact.
3. **Response Timeline:** Acknowledge receipt within 48 hours and provide patches within 14 days.