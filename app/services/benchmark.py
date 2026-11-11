import asyncio
import time
import tracemalloc
from typing import Any, Dict, List
from app.models.extraction_profile import FieldExtractionRule, DataTypeEnum, RuleTypeEnum
from app.services.parser_rules import ParserRuleService


class PerformanceBenchmarkService:
    """Measures crawl throughput, execution latency, memory consumption, and yield rates."""

    @classmethod
    async def benchmark_extraction_engine(
        cls,
        html_fixture: str,
        rules: List[FieldExtractionRule],
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """Runs stress-testing iterations of DOM parsing to calculate throughput and latency."""
        tracemalloc.start()
        start_time = time.perf_counter()

        successful_parse_count = 0
        for _ in range(iterations):
            extracted = ParserRuleService.apply_profile_rules(html_fixture, rules)
            if extracted:
                successful_parse_count += 1

        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        total_elapsed_sec = end_time - start_time
        avg_latency_ms = (total_elapsed_sec / iterations) * 1000.0
        throughput_ops_sec = iterations / total_elapsed_sec if total_elapsed_sec > 0 else 0.0

        return {
            "iterations": iterations,
            "total_elapsed_sec": round(total_elapsed_sec, 4),
            "avg_latency_ms": round(avg_latency_ms, 3),
            "throughput_ops_sec": round(throughput_ops_sec, 2),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 2),
            "success_rate_pct": round((successful_parse_count / iterations) * 100.0, 2)
        }