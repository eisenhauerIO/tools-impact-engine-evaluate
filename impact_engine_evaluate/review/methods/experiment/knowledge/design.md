# RCT Design Fundamentals

## Randomization

Random assignment of units to treatment and control ensures that, in
expectation, the two groups are balanced on all observed and unobserved
covariates. This makes the simple difference in means an unbiased estimator
of the average treatment effect (ATE).

Key checks:
- Balance tables comparing treatment and control on pre-treatment covariates.
- Joint F-test or chi-squared test for overall balance.
- Stratified or blocked randomization to improve precision.

## SUTVA

The Stable Unit Treatment Value Assumption requires:
1. No interference — one unit's treatment does not affect another unit's outcome.
2. No hidden versions of treatment — the treatment is well-defined.

Violations arise from spillover effects (geographic proximity, social networks)
or inconsistent treatment delivery.

## Exchangeability

Given random assignment, treatment and control groups are exchangeable:
potential outcomes are independent of treatment assignment. This is the
identifying assumption that supports a causal interpretation of the
estimated effect.

## Intent-to-Treat (ITT)

The ITT estimate compares outcomes by *assigned* treatment, ignoring
non-compliance. It is an unbiased estimate of the effect of being assigned
to treatment. It underestimates the effect of actually receiving treatment
when compliance is imperfect.

## Statistical Power

Power is the probability of detecting a true effect. It depends on:
- Sample size (larger is better).
- Effect size (larger effects are easier to detect).
- Significance level (typically 0.05).
- Outcome variance (lower variance improves power).

Minimum detectable effect (MDE) calculations should be reported to assess
whether the study was adequately powered.
