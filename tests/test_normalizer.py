from app.services.normalizers import DataNormalizerService as NormalizerService
from app.services.quality_reporter import DataQualityReporterService as DataQualityService


def test_string_and_url_normalization():
    """Validates raw extracted string and URL cleaning rules."""
    dirty_text = "   Quantitative Research  Intern \n\t  "
    clean_text = NormalizerService.normalize_string(dirty_text)
    assert clean_text == "Quantitative Research Intern"

    relative_url = "/apply/2026"
    absolute_url = NormalizerService.normalize_url(relative_url, base_url="https://example.com")
    assert absolute_url == "https://example.com/apply/2026"


def test_data_quality_scoring():
    """Evaluates quality report calculation on extracted records."""
    sample_records = [
        {"title": "Software Engineer Intern", "organisation": "TechCorp", "deadline": "2026-11-30"},
        {"title": "Data Analyst", "organisation": None, "deadline": "2026-12-01"}
    ]

    report = DataQualityService.evaluate_quality(sample_records, required_fields=["title", "organisation"])
    assert report["total_records"] == 2
    assert report["valid_records"] == 1
    assert report["completeness_score"] < 100.0