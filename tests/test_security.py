from app.services.security import SecurityService


def test_ssrf_blocks_loopback_and_internal_ips():
    """Validates Layer B SSRF security restrictions on internal networks."""
    # Loopback IP
    is_safe, reason = SecurityService.validate_url_safety("http://127.0.0.1/admin")
    assert not is_safe
    assert "SSRF" in reason or "Restricted" in reason

    # Localhost domain
    is_safe_host, _ = SecurityService.validate_url_safety("http://localhost:8000/metrics")
    assert not is_safe_host

    # Private RFC1918 Class A subnet
    is_safe_private, _ = SecurityService.validate_url_safety("http://10.0.0.1/internal-api")
    assert not is_safe_private


def test_ssrf_allows_public_urls():
    """Validates public web URLs pass Layer B validation."""
    is_safe, _ = SecurityService.validate_url_safety("https://example.com/opportunities")
    assert is_safe