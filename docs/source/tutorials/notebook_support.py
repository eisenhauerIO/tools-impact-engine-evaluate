"""Shared utilities for tutorial notebooks."""

import json


def print_json(data, indent=2):
    """Pretty-print a dict as formatted JSON."""
    print(json.dumps(data, indent=indent))


def print_result_summary(result):
    """Print a compact summary of an EvaluateResult dict."""
    print(f"Initiative:  {result['initiative_id']}")
    print(f"Model type:  {result['model_type']}")
    print(f"Confidence:  {result['confidence']:.4f}")
    print(f"Cost:        {result['cost']:.2f}")
    print(f"Return best: {result['return_best']:.2f}")
    print(f"Return med:  {result['return_median']:.2f}")
    print(f"Return worst:{result['return_worst']:.2f}")
    print(f"Sample size: {result['sample_size']}")
