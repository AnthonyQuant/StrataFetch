import asyncio
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.extraction_profile import FieldExtractionRule, DataTypeEnum, RuleTypeEnum
from app.services.benchmark import PerformanceBenchmarkService


async def main():
    print("⚡ StrataFetch Performance & Instrumentation Benchmark Engine")
    print("=" * 60)

    # Load offline HTML fixture
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "sample_opportunity.html")
    if not os.path.exists(fixture_path):
        print(f"❌ Error: Fixture not found at {fixture_path}")
        return

    with open(fixture_path, "r", encoding="utf-8") as f:
        html_content = f.read()

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

    print("Running 1,000 extraction iterations against offline DOM snapshot...")
    metrics = await PerformanceBenchmarkService.benchmark_extraction_engine(
        html_fixture=html_content,
        rules=rules,
        iterations=1000
    )

    print("\n📊 Benchmark Results:")
    print(f" • Total Time Elapsed : {metrics['total_elapsed_sec']} seconds")
    print(f" • Average Latency    : {metrics['avg_latency_ms']} ms / page")
    print(f" • Operations Rate    : {metrics['throughput_ops_sec']} ops / sec")
    print(f" • Peak RAM Footprint : {metrics['peak_memory_mb']} MB")
    print(f" • Schema Success     : {metrics['success_rate_pct']}%")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())