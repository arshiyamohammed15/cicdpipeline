"""
SLI Calculator for ZeroUI Observability Layer.

Implements all 7 SLIs with explicit numerator/denominator formulas per PRD Section 5.1.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..contracts.event_types import EventType

logger = logging.getLogger(__name__)


@dataclass
class SLIResult:
    """Result of SLI computation."""

    sli_id: str
    sli_name: str
    value: float
    numerator: float
    denominator: float
    grouping: Dict[str, str]
    metadata: Dict[str, Any]


class SLICalculator:
    """
    SLI Calculator for ZeroUI Observability Layer.

    Computes all 7 SLIs deterministically from events and traces.
    """

    def __init__(self):
        """Initialize SLI calculator."""
        pass

    def compute_sli_a(
        self,
        traces: List[Dict[str, Any]],
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-A: End-to-End Decision Success Rate.

        Formula: successful_runs / total_runs
        Source: root spans in traces with attribute run_outcome=success vs all root spans
        Group by: component and channel

        Args:
            traces: List of trace dictionaries (root spans)
            component: Optional component filter
            channel: Optional channel filter

        Returns:
            List of SLIResult grouped by component and channel
        """
        # Group traces by component and channel
        grouped = defaultdict(lambda: {"successful": 0, "total": 0})

        for trace in traces:
            # Extract component and channel from trace attributes
            trace_component = trace.get("attributes", {}).get("component", "unknown")
            trace_channel = trace.get("attributes", {}).get("channel", "unknown")

            # Apply filters
            if component and trace_component != component:
                continue
            if channel and trace_channel != channel:
                continue

            # Check if root span
            parent_span_id = trace.get("parent_span_id")
            if parent_span_id:  # Not a root span
                continue

            # Count total runs
            grouped[(trace_component, trace_channel)]["total"] += 1

            # Check for success
            run_outcome = trace.get("attributes", {}).get("run_outcome")
            if run_outcome == "success":
                grouped[(trace_component, trace_channel)]["successful"] += 1

        # Compute SLI for each group
        results = []
        for (comp, chan), counts in grouped.items():
            if counts["total"] == 0:
                # Zero traffic - return 0.0 (no data)
                results.append(
                    SLIResult(
                        sli_id="SLI-A",
                        sli_name="End-to-End Decision Success Rate",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"component": comp, "channel": chan},
                        metadata={"zero_traffic": True},
                    )
                )
            else:
                value = counts["successful"] / counts["total"]
                results.append(
                    SLIResult(
                        sli_id="SLI-A",
                        sli_name="End-to-End Decision Success Rate",
                        value=value,
                        numerator=float(counts["successful"]),
                        denominator=float(counts["total"]),
                        grouping={"component": comp, "channel": chan},
                        metadata={},
                    )
                )

        return results

    def compute_sli_b(
        self,
        traces: List[Dict[str, Any]],
        perf_samples: List[Dict[str, Any]],
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-B: End-to-End Latency.

        Formula: p50/p95/p99 decision latency
        Source: root span duration OR perf.sample.v1 where operation=decision
        Group by: component and channel

        Args:
            traces: List of trace dictionaries (root spans)
            perf_samples: List of perf.sample.v1 events
            component: Optional component filter
            channel: Optional channel filter

        Returns:
            List of SLIResult with p50/p95/p99 values
        """
        # Collect latency values
        latencies_by_group: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        # From traces (root span duration)
        for trace in traces:
            trace_component = trace.get("attributes", {}).get("component", "unknown")
            trace_channel = trace.get("attributes", {}).get("channel", "unknown")

            if component and trace_component != component:
                continue
            if channel and trace_channel != channel:
                continue

            parent_span_id = trace.get("parent_span_id")
            if parent_span_id:  # Not a root span
                continue

            # Get span duration
            start_time = trace.get("start_time")
            end_time = trace.get("end_time")
            if start_time and end_time:
                duration_ms = (end_time - start_time) * 1000  # Convert to ms
                latencies_by_group[(trace_component, trace_channel)].append(duration_ms)

        # From perf.sample.v1 events (operation=decision)
        for sample in perf_samples:
            if sample.get("event_type") != EventType.PERF_SAMPLE.value:
                continue

            payload = sample.get("payload", {})
            if payload.get("operation") != "decision":
                continue

            sample_component = payload.get("component", "unknown")
            sample_channel = payload.get("channel", "unknown")

            if component and sample_component != component:
                continue
            if channel and sample_channel != channel:
                continue

            latency_ms = payload.get("latency_ms")
            if latency_ms is not None:
                latencies_by_group[(sample_component, sample_channel)].append(float(latency_ms))

        # Compute percentiles for each group
        results = []
        for (comp, chan), latencies in latencies_by_group.items():
            if not latencies:
                # Zero traffic
                results.append(
                    SLIResult(
                        sli_id="SLI-B",
                        sli_name="End-to-End Latency",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"component": comp, "channel": chan},
                        metadata={"zero_traffic": True, "p50": 0.0, "p95": 0.0, "p99": 0.0},
                    )
                )
            else:
                sorted_latencies = sorted(latencies)
                p50 = self._percentile(sorted_latencies, 50)
                p95 = self._percentile(sorted_latencies, 95)
                p99 = self._percentile(sorted_latencies, 99)

                results.append(
                    SLIResult(
                        sli_id="SLI-B",
                        sli_name="End-to-End Latency",
                        value=p95,  # Use p95 as primary value
                        numerator=float(len(sorted_latencies)),
                        denominator=float(len(sorted_latencies)),
                        grouping={"component": comp, "channel": chan},
                        metadata={"p50": p50, "p95": p95, "p99": p99, "count": len(sorted_latencies)},
                    )
                )

        return results

    def compute_sli_c(
        self,
        error_events: List[Dict[str, Any]],
        error_traces: List[Dict[str, Any]],
        component: Optional[str] = None,
        channel: Optional[str] = None,
        error_class: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-C: Error Capture Coverage.

        Formula: count(error.captured.v1 with required fields) / count(root spans with status=error)
        Source: error.captured.v1 + trace root spans
        Group by: error_class, component, channel

        Args:
            error_events: List of error.captured.v1 events
            error_traces: List of trace root spans with status=error
            component: Optional component filter
            channel: Optional channel filter
            error_class: Optional error_class filter

        Returns:
            List of SLIResult grouped by error_class, component, channel
        """
        # Count error.captured.v1 events with required fields
        captured_by_group = defaultdict(int)
        for event in error_events:
            if event.get("event_type") != EventType.ERROR_CAPTURED.value:
                continue

            payload = event.get("payload", {})
            event_component = payload.get("component", "unknown")
            event_channel = payload.get("channel", "unknown")
            event_error_class = payload.get("error_class", "unknown")

            # Apply filters
            if component and event_component != component:
                continue
            if channel and event_channel != channel:
                continue
            if error_class and event_error_class != error_class:
                continue

            # Check required fields are present
            required_fields = [
                "error_class",
                "error_code",
                "stage",
                "message_fingerprint",
                "input_fingerprint",
                "output_fingerprint",
                "internal_state_fingerprint",
            ]
            if all(field in payload for field in required_fields):
                key = (event_error_class, event_component, event_channel)
                captured_by_group[key] += 1

        # Count total errors from traces
        total_by_group = defaultdict(int)
        for trace in error_traces:
            trace_status = trace.get("status")
            if trace_status != "error":
                continue

            trace_component = trace.get("attributes", {}).get("component", "unknown")
            trace_channel = trace.get("attributes", {}).get("channel", "unknown")
            trace_error_class = trace.get("attributes", {}).get("error_class", "unknown")

            # Apply filters
            if component and trace_component != component:
                continue
            if channel and trace_channel != channel:
                continue
            if error_class and trace_error_class != error_class:
                continue

            parent_span_id = trace.get("parent_span_id")
            if parent_span_id:  # Not a root span
                continue

            key = (trace_error_class, trace_component, trace_channel)
            total_by_group[key] += 1

        # Compute coverage for each group
        results = []
        all_groups = set(captured_by_group.keys()) | set(total_by_group.keys())
        for (err_class, comp, chan) in all_groups:
            captured = captured_by_group.get((err_class, comp, chan), 0)
            total = total_by_group.get((err_class, comp, chan), 0)

            if total == 0:
                # Zero traffic
                results.append(
                    SLIResult(
                        sli_id="SLI-C",
                        sli_name="Error Capture Coverage",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"error_class": err_class, "component": comp, "channel": chan},
                        metadata={"zero_traffic": True},
                    )
                )
            else:
                value = captured / total
                results.append(
                    SLIResult(
                        sli_id="SLI-C",
                        sli_name="Error Capture Coverage",
                        value=value,
                        numerator=float(captured),
                        denominator=float(total),
                        grouping={"error_class": err_class, "component": comp, "channel": chan},
                        metadata={},
                    )
                )

        return results

    def compute_sli_d(
        self,
        prompt_validation_events: List[Dict[str, Any]],
        prompt_id: Optional[str] = None,
        prompt_version: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-D: Prompt Validation Pass Rate.

        Formula: count(prompt.validation.result.v1 status=pass) / count(prompt.validation.result.v1)
        Source: prompt.validation.result.v1
        Group by: prompt_id and prompt_version

        Args:
            prompt_validation_events: List of prompt.validation.result.v1 events
            prompt_id: Optional prompt_id filter
            prompt_version: Optional prompt_version filter

        Returns:
            List of SLIResult grouped by prompt_id and prompt_version
        """
        grouped = defaultdict(lambda: {"pass": 0, "total": 0})

        for event in prompt_validation_events:
            if event.get("event_type") != EventType.PROMPT_VALIDATION_RESULT.value:
                continue

            payload = event.get("payload", {})
            event_prompt_id = payload.get("prompt_id", "unknown")
            event_prompt_version = payload.get("prompt_version", "unknown")

            # Apply filters
            if prompt_id and event_prompt_id != prompt_id:
                continue
            if prompt_version and event_prompt_version != prompt_version:
                continue

            key = (event_prompt_id, event_prompt_version)
            grouped[key]["total"] += 1

            if payload.get("status") == "pass":
                grouped[key]["pass"] += 1

        # Compute SLI for each group
        results = []
        for (pid, pver), counts in grouped.items():
            if counts["total"] == 0:
                results.append(
                    SLIResult(
                        sli_id="SLI-D",
                        sli_name="Prompt Validation Pass Rate",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"prompt_id": pid, "prompt_version": pver},
                        metadata={"zero_traffic": True},
                    )
                )
            else:
                value = counts["pass"] / counts["total"]
                results.append(
                    SLIResult(
                        sli_id="SLI-D",
                        sli_name="Prompt Validation Pass Rate",
                        value=value,
                        numerator=float(counts["pass"]),
                        denominator=float(counts["total"]),
                        grouping={"prompt_id": pid, "prompt_version": pver},
                        metadata={},
                    )
                )

        return results

    def compute_sli_e(
        self,
        retrieval_events: List[Dict[str, Any]],
        corpus_id: Optional[str] = None,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-E: Retrieval Compliance.

        Formula: count(retrieval.eval.v1 where relevance_compliant=true AND timeliness_compliant=true) / count(retrieval.eval.v1)
        Source: retrieval.eval.v1
        Group by: corpus_id, component, channel

        Args:
            retrieval_events: List of retrieval.eval.v1 events
            corpus_id: Optional corpus_id filter
            component: Optional component filter
            channel: Optional channel filter

        Returns:
            List of SLIResult grouped by corpus_id, component, channel
        """
        grouped = defaultdict(lambda: {"compliant": 0, "total": 0})

        for event in retrieval_events:
            if event.get("event_type") != EventType.RETRIEVAL_EVAL.value:
                continue

            payload = event.get("payload", {})
            event_corpus_id = payload.get("corpus_id", "unknown")
            event_component = payload.get("component", "unknown")
            event_channel = payload.get("channel", "unknown")

            # Apply filters
            if corpus_id and event_corpus_id != corpus_id:
                continue
            if component and event_component != component:
                continue
            if channel and event_channel != channel:
                continue

            key = (event_corpus_id, event_component, event_channel)
            grouped[key]["total"] += 1

            # Check compliance
            relevance_compliant = payload.get("relevance_compliant", False)
            timeliness_compliant = payload.get("timeliness_compliant", False)
            if relevance_compliant and timeliness_compliant:
                grouped[key]["compliant"] += 1

        # Compute SLI for each group
        results = []
        for (corp_id, comp, chan), counts in grouped.items():
            if counts["total"] == 0:
                results.append(
                    SLIResult(
                        sli_id="SLI-E",
                        sli_name="Retrieval Compliance",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"corpus_id": corp_id, "component": comp, "channel": chan},
                        metadata={"zero_traffic": True},
                    )
                )
            else:
                value = counts["compliant"] / counts["total"]
                results.append(
                    SLIResult(
                        sli_id="SLI-E",
                        sli_name="Retrieval Compliance",
                        value=value,
                        numerator=float(counts["compliant"]),
                        denominator=float(counts["total"]),
                        grouping={"corpus_id": corp_id, "component": comp, "channel": chan},
                        metadata={},
                    )
                )

        return results

    def compute_sli_f(
        self,
        evaluation_events: List[Dict[str, Any]],
        user_flag_events: List[Dict[str, Any]],
        component: Optional[str] = None,
        channel: Optional[str] = None,
        eval_suite_id: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-F: Evaluation Quality Signal.

        Formula: user_flags + score_distribution
        Source: evaluation.result.v1 (metrics) and user.flag.v1
        Group by: channel, component, eval_suite_id

        Args:
            evaluation_events: List of evaluation.result.v1 events
            user_flag_events: List of user.flag.v1 events
            component: Optional component filter
            channel: Optional channel filter
            eval_suite_id: Optional eval_suite_id filter

        Returns:
            List of SLIResult with score distribution and user flag rate
        """
        # Collect scores and flags by group
        scores_by_group: Dict[Tuple[str, str, str], List[float]] = defaultdict(list)
        flags_by_group: Dict[Tuple[str, str, str], int] = defaultdict(int)

        # From evaluation.result.v1
        for event in evaluation_events:
            if event.get("event_type") != EventType.EVALUATION_RESULT.value:
                continue

            payload = event.get("payload", {})
            event_component = payload.get("component", "unknown")
            event_channel = payload.get("channel", "unknown")
            event_suite_id = payload.get("eval_suite_id", "unknown")

            # Apply filters
            if component and event_component != component:
                continue
            if channel and event_channel != channel:
                continue
            if eval_suite_id and event_suite_id != eval_suite_id:
                continue

            # Extract scores from metrics
            metrics = payload.get("metrics", [])
            for metric in metrics:
                if metric.get("metric_name") in ["score", "accuracy", "quality"]:
                    score = metric.get("metric_value")
                    if score is not None:
                        key = (event_component, event_channel, event_suite_id)
                        scores_by_group[key].append(float(score))

        # From user.flag.v1
        for event in user_flag_events:
            if event.get("event_type") != EventType.USER_FLAG.value:
                continue

            payload = event.get("payload", {})
            event_component = payload.get("component", "unknown")
            event_channel = payload.get("channel", "unknown")
            event_suite_id = "unknown"  # user.flag.v1 doesn't have eval_suite_id

            # Apply filters
            if component and event_component != component:
                continue
            if channel and event_channel != channel:
                continue

            key = (event_component, event_channel, event_suite_id)
            flags_by_group[key] += 1

        # Compute SLI for each group
        results = []
        all_groups = set(scores_by_group.keys()) | set(flags_by_group.keys())
        for (comp, chan, suite_id) in all_groups:
            scores = scores_by_group.get((comp, chan, suite_id), [])
            flags = flags_by_group.get((comp, chan, suite_id), 0)

            if not scores and flags == 0:
                # Zero traffic
                results.append(
                    SLIResult(
                        sli_id="SLI-F",
                        sli_name="Evaluation Quality Signal",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"component": comp, "channel": chan, "eval_suite_id": suite_id},
                        metadata={"zero_traffic": True, "user_flag_rate": 0.0, "score_distribution": {}},
                    )
                )
            else:
                # Compute score distribution
                if scores:
                    sorted_scores = sorted(scores)
                    score_p50 = self._percentile(sorted_scores, 50)
                    score_p95 = self._percentile(sorted_scores, 95)
                    score_mean = sum(sorted_scores) / len(sorted_scores)
                else:
                    score_p50 = score_p95 = score_mean = 0.0

                # User flag rate (flags per evaluation)
                flag_rate = flags / len(scores) if scores else 0.0

                # Primary value: mean score (can be adjusted)
                value = score_mean

                results.append(
                    SLIResult(
                        sli_id="SLI-F",
                        sli_name="Evaluation Quality Signal",
                        value=value,
                        numerator=float(len(scores)),
                        denominator=float(len(scores)),
                        grouping={"component": comp, "channel": chan, "eval_suite_id": suite_id},
                        metadata={
                            "user_flag_rate": flag_rate,
                            "user_flags": flags,
                            "score_distribution": {
                                "p50": score_p50,
                                "p95": score_p95,
                                "mean": score_mean,
                                "count": len(scores),
                            },
                        },
                    )
                )

        return results

    def compute_sli_g(
        self,
        alert_noise_control_events: List[Dict[str, Any]],
        detector_type: Optional[str] = None,
    ) -> List[SLIResult]:
        """
        Compute SLI-G: False Positive Rate (FPR).

        Formula: false_positive / (false_positive + true_positive)
        Source: alert.noise_control.v1 enriched by human validation outcomes
        Group by: detector type and alert_fingerprint

        Args:
            alert_noise_control_events: List of alert.noise_control.v1 events
            detector_type: Optional detector_type filter

        Returns:
            List of SLIResult grouped by detector type and alert_fingerprint
        """
        # Group by detector type and alert_fingerprint
        grouped = defaultdict(lambda: {"false_positive": 0, "true_positive": 0})

        for event in alert_noise_control_events:
            if event.get("event_type") != EventType.ALERT_NOISE_CONTROL.value:
                continue

            payload = event.get("payload", {})
            alert_fingerprint = payload.get("alert_fingerprint", "unknown")

            # Extract detector type from component or metadata
            event_component = payload.get("component", "unknown")
            # Assume detector type is in component or can be extracted
            event_detector_type = event_component  # Simplified - can be enhanced

            # Apply filters
            if detector_type and event_detector_type != detector_type:
                continue

            # Check validation outcome (from metadata or enrichment)
            # For Phase 1, assume we can extract from event metadata
            validation_outcome = event.get("metadata", {}).get("validation_outcome", "unknown")
            key = (event_detector_type, alert_fingerprint)

            if validation_outcome == "false_positive":
                grouped[key]["false_positive"] += 1
            elif validation_outcome == "true_positive":
                grouped[key]["true_positive"] += 1

        # Compute FPR for each group
        results = []
        for (det_type, alert_fp), counts in grouped.items():
            total_positive = counts["false_positive"] + counts["true_positive"]
            if total_positive == 0:
                # Zero traffic
                results.append(
                    SLIResult(
                        sli_id="SLI-G",
                        sli_name="False Positive Rate (FPR)",
                        value=0.0,
                        numerator=0.0,
                        denominator=0.0,
                        grouping={"detector_type": det_type, "alert_fingerprint": alert_fp},
                        metadata={"zero_traffic": True},
                    )
                )
            else:
                fpr = counts["false_positive"] / total_positive
                results.append(
                    SLIResult(
                        sli_id="SLI-G",
                        sli_name="False Positive Rate (FPR)",
                        value=fpr,
                        numerator=float(counts["false_positive"]),
                        denominator=float(total_positive),
                        grouping={"detector_type": det_type, "alert_fingerprint": alert_fp},
                        metadata={},
                    )
                )

        return results

    def _percentile(self, data: List[float], percentile: int) -> float:
        """
        Calculate percentile.

        Args:
            data: Sorted list of values
            percentile: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0
        index = int(len(data) * percentile / 100)
        if index >= len(data):
            index = len(data) - 1
        return data[index]


# Convenience functions
def compute_sli_a(traces: List[Dict[str, Any]], **kwargs) -> List[SLIResult]:
    """Compute SLI-A: End-to-End Decision Success Rate."""
    calculator = SLICalculator()
    return calculator.compute_sli_a(traces, **kwargs)


def compute_sli_b(traces: List[Dict[str, Any]], perf_samples: List[Dict[str, Any]], **kwargs) -> List[SLIResult]:
    """Compute SLI-B: End-to-End Latency."""
    calculator = SLICalculator()
    return calculator.compute_sli_b(traces, perf_samples, **kwargs)


def compute_sli_c(error_events: List[Dict[str, Any]], error_traces: List[Dict[str, Any]], **kwargs) -> List[SLIResult]:
    """Compute SLI-C: Error Capture Coverage."""
    calculator = SLICalculator()
    return calculator.compute_sli_c(error_events, error_traces, **kwargs)
