"""
Performance Benchmarking Tool (Milestone 10.3).
Measures execution time and memory usage across every stage of the Business Risk & Recommendation Engine.
"""

import time
import tracemalloc
import statistics
from typing import Dict, Any

from core.business_risk.models.business_risk_result import BusinessRiskResult
from core.business_risk.models.aspect_risk import AspectRisk
from core.business_risk.models.risk_level import RiskLevel

from core.recommendation.service import RecommendationService
from core.recommendation.engine import RecommendationEngine
from app.mappers.analysis_mapper import AnalysisMapper


def benchmark_recommendation_pipeline(iterations: int = 50) -> Dict[str, Any]:
    """
    Benchmarks Recommendation Engine and Mapper latency and memory allocation over N iterations.
    """
    service = RecommendationService()

    high_risk_br = BusinessRiskResult(
        quality=AspectRisk(aspect="quality", score=85.0, level="HIGH"),
        delivery=AspectRisk(aspect="delivery", score=22.0, level="LOW"),
        trust=AspectRisk(aspect="trust", score=60.0, level="MEDIUM"),
        business_risk_index=76.0,
        business_risk_level=RiskLevel.HIGH,
    )

    times_ms = []

    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    for _ in range(iterations):
        t0 = time.perf_counter()
        rec_result = service.generate_recommendation(high_risk_br)

        mock_output = {
            "product": {"title": "Benchmark Product", "url": "https://daraz.com.np/p/bench"},
            "business": high_risk_br,
            "quality": high_risk_br.quality,
            "delivery": high_risk_br.delivery,
            "trust": high_risk_br.trust,
            "recommendation": rec_result,
        }
        _ = AnalysisMapper.to_api_result(mock_output)
        t1 = time.perf_counter()

        times_ms.append((t1 - t0) * 1000.0)

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    memory_allocated_kb = sum(stat.size for stat in snapshot_after.compare_to(snapshot_before, 'filename')) / 1024.0

    avg_time = statistics.mean(times_ms)
    min_time = min(times_ms)
    max_time = max(times_ms)
    p95_time = sorted(times_ms)[int(iterations * 0.95)]

    report = {
        "iterations": iterations,
        "avg_ms": round(avg_time, 3),
        "min_ms": round(min_time, 3),
        "max_ms": round(max_time, 3),
        "p95_ms": round(p95_time, 3),
        "memory_delta_kb": round(memory_allocated_kb, 2),
    }

    return report


def main():
    print("=" * 60)
    print("      BUSINESS RISK & RECOMMENDATION PIPELINE BENCHMARK")
    print("=" * 60)

    report = benchmark_recommendation_pipeline(iterations=50)

    print(f"Iterations Evaluated    : {report['iterations']}")
    print(f"Average Response Time   : {report['avg_ms']} ms")
    print(f"Minimum Response Time   : {report['min_ms']} ms")
    print(f"Maximum Response Time   : {report['max_ms']} ms")
    print(f"95th Percentile Latency : {report['p95_ms']} ms")
    print(f"Memory Delta Allocated  : {report['memory_delta_kb']} KB")
    print("=" * 60)
    print("BENCHMARK COMPLETED SUCCESSFULLY.")
    print("=" * 60)


if __name__ == "__main__":
    main()
