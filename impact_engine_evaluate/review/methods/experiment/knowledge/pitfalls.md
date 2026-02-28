# Common Threats to RCT Validity

## Attrition

Differential dropout between treatment and control groups can bias the
treatment effect estimate. Check:
- Overall attrition rate (above 20% is concerning).
- Differential attrition (compare rates across arms).
- Lee bounds or trimming estimators to bound the effect under worst-case
  attrition.

## Non-compliance

When assigned treatment differs from received treatment:
- ITT analysis remains valid but may underestimate the effect.
- IV/2SLS with assignment as instrument estimates the local average
  treatment effect (LATE) for compliers.
- Per-protocol analysis is biased and should be avoided as a primary
  estimate.

## Spillover Effects

Treatment effects can leak to control units through:
- Geographic proximity (neighboring villages).
- Social networks (information diffusion).
- Market-level effects (general equilibrium).

Detection: compare control outcomes near vs. far from treated units.
Prevention: cluster randomization with sufficient buffer zones.

## Multiple Testing

Running many hypothesis tests inflates the family-wise error rate:
- Bonferroni correction (conservative).
- Benjamini-Hochberg FDR control (less conservative).
- Pre-registered primary outcomes reduce the testing burden.
- Exploratory subgroup analyses should be flagged as such.

## Hawthorne and John Henry Effects

- Hawthorne: subjects change behavior because they know they are observed.
- John Henry: control group increases effort to compensate for not
  receiving treatment.
- Both bias the estimated treatment effect in opposite directions.
- Blinding (single or double) mitigates these threats when feasible.
