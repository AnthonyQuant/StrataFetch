from app.models.extraction_profile import FieldExtractionRule, DataTypeEnum, RuleTypeEnum
from app.services.html_extractor import HTMLExtractorService
from app.services.parser_rules import ParserRuleService


def test_offline_html_field_extraction(sample_html_fixture):
    """Executes rule extractions against an offline HTML snapshot fixture."""
    rules = [
        FieldExtractionRule(
            field_name="title",
            rule_type=RuleTypeEnum.CSS_SELECTOR,
            expression="h2.opp-title",
            data_type=DataTypeEnum.STRING,
            required=True
        ),
        FieldExtractionRule(
            field_name="organisation",
            rule_type=RuleTypeEnum.CSS_SELECTOR,
            expression="span.opp-org",
            data_type=DataTypeEnum.STRING,
            required=True
        ),
        FieldExtractionRule(
            field_name="application_url",
            rule_type=RuleTypeEnum.CSS_SELECTOR,
            expression="a.apply-link",
            attribute="href",
            data_type=DataTypeEnum.URL,
            required=True
        )
    ]

    extracted = ParserRuleService.apply_profile_rules(sample_html_fixture, rules)

    assert extracted["title"] == "Quantitative Research Intern"
    assert extracted["organisation"] == "Strata Capital Ltd"
    assert extracted["application_url"] == "https://example.com/apply/quant-2026"


def test_container_based_record_extraction(sample_html_fixture):
    """Tests container card wrapper record extractions."""
    rules = [
        FieldExtractionRule(
            field_name="title",
            rule_type=RuleTypeEnum.CSS_SELECTOR,
            expression="h2.opp-title",
            data_type=DataTypeEnum.STRING
        )
    ]

    records = HTMLExtractorService.extract(
        html_content=sample_html_fixture,
        container_selector="div.opportunity-card",
        rules=rules
    )

    assert len(records) == 1
    assert records[0]["title"] == "Quantitative Research Intern"