# Impact Engine — Evaluate

[![CI](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/ci.yaml/badge.svg)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/ci.yaml)
[![Docs](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/docs.yaml/badge.svg?branch=main)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/docs.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Slack](https://img.shields.io/badge/Slack-Join%20Us-4A154B?logo=slack)](https://join.slack.com/t/eisenhauerioworkspace/shared_invite/zt-3lxtc370j-XLdokfTkno54wfhHVxvEfA)

*Confidence scoring and agentic review for causal impact estimates*

How much you trust a causal estimate depends on the method that produced it. A randomized experiment with thousands of observations produces stronger evidence than a time series model on sparse data — but most pipelines treat all estimates equally.

**Impact Engine — Evaluate** scores each estimate for reliability based on its measurement design. A deterministic scorer assigns confidence from methodology-specific ranges. An agentic reviewer sends the actual measurement artifacts to an LLM for structured, per-dimension evaluation. The resulting confidence score directly penalizes return estimates downstream, making the allocator conservative where evidence is weak and aggressive where evidence is strong.

Visit our [documentation](https://eisenhauerio.github.io/tools-impact-engine-evaluate/) for details.
