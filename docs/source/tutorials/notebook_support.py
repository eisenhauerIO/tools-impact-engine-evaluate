"""Shared utilities for tutorial notebooks."""

import json


def print_json(data, indent=2):
    """Pretty-print a dict as formatted JSON."""
    print(json.dumps(data, indent=indent))


def print_result_summary(result):
    """Print a compact summary of an EvaluateResult dict."""
    lo, hi = result["confidence_range"]
    print(f"Initiative:  {result['initiative_id']}")
    print(f"Strategy:    {result['strategy']}")
    print(f"Confidence:  {result['confidence']:.4f}  (range {lo:.2f}–{hi:.2f})")
    report = result["report"]
    if isinstance(report, str):
        print(f"Report:      {report}")
    else:
        print(
            f"Report:      {report.get('overall_score', 'N/A')} overall"
            f" ({len(report.get('dimensions', []))} dimensions)"
        )
