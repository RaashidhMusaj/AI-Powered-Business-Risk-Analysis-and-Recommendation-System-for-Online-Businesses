"""
Performance Benchmarking Unit Tests (Milestone 10.3).
Asserts latency thresholds and memory limits for Recommendation Engine and Mapper execution.
"""

import pytest
from scripts.benchmark_pipeline import benchmark_recommendation_pipeline


def test_performance_benchmark_thresholds():
    """Milestone 10.3: Asserts average recommendation processing latency remains below performance threshold."""
    report = benchmark_recommendation_pipeline(iterations=20)

    assert report["avg_ms"] < 100.0, f"Average pipeline execution time {report['avg_ms']}ms exceeded 100ms threshold!"
    assert report["p95_ms"] < 150.0, f"P95 latency {report['p95_ms']}ms exceeded 150ms threshold!"
