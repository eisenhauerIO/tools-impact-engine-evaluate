# Quasi-Experimental Methods: Key Concepts

## Difference-in-Differences (DiD)

The parallel trends assumption requires that, absent treatment, the treated and
control groups would have evolved similarly over time. This assumption is
untestable in principle but can be supported by:

- Pre-treatment trend plots showing parallel movement
- Placebo tests using pre-treatment periods as pseudo-treatment dates
- Event-study specifications showing no pre-treatment divergence

Common threats: anticipation effects, differential composition changes,
Ashenfelter's dip, contamination of control group.

## Regression Discontinuity Design (RDD)

Identification relies on continuity of potential outcomes at the threshold.
Key diagnostics:

- McCrary density test for sorting/manipulation around the cutoff
- Covariate smoothness at the threshold
- Sensitivity to bandwidth choice (IK, CCT optimal bandwidths)
- Polynomial order robustness checks

Sharp RDD identifies a Local Average Treatment Effect (LATE) at the threshold;
fuzzy RDD requires an additional IV assumption.

## Instrumental Variables (IV)

Validity requires relevance (strong first stage, F-statistic > 10 as rule of
thumb) and the exclusion restriction (instrument affects outcome only through
treatment). LATE interpretation applies: effect identified only for compliers.

Key checks: first-stage F-statistic, overidentification tests (when applicable),
sensitivity to instrument definition.

## General Guidance

Quasi-experimental estimates are more credible when:
1. The identifying assumption is theoretically motivated, not merely asserted
2. Multiple robustness checks are reported and pass
3. Effect sizes are consistent with prior literature and mechanism
4. The local nature of the estimate (LATE, ATT at threshold) is acknowledged
