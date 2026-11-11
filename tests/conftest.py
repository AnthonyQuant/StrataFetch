import os
import pytest


@pytest.fixture(scope="session")
def sample_html_fixture():
    """Loads the static HTML fixture for offline extraction testing."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_opportunity.html")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()