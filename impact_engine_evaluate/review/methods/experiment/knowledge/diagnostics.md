# OLS Output Interpretation

## Coefficient Estimates

The treatment coefficient is the estimated ATE. Its magnitude, sign, and
statistical significance are the primary quantities of interest. Control
variable coefficients should be interpreted cautiously — they adjust for
baseline differences but are not causal estimates themselves.

## Standard Errors

- Heteroskedasticity-robust (HC1/HC2/HC3) standard errors should be used
  by default to guard against non-constant variance.
- Cluster-robust standard errors are required when randomization or outcomes
  are correlated within groups (villages, classrooms, firms).
- Failure to cluster when appropriate inflates t-statistics and produces
  false positives.

## R-squared and Adjusted R-squared

R-squared measures in-sample fit. Low R-squared is common and acceptable in
experimental settings — the treatment explains a small share of total
variation by design. High R-squared from control variables signals good
precision but does not affect the causal interpretation of the treatment
effect.

## F-statistic

The overall F-test assesses joint significance of all regressors. More
relevant in experimental contexts is the F-test for covariate balance
(all covariates jointly insignificant in a regression of treatment on
covariates).

## Residual Diagnostics

- Residual plots can reveal heteroskedasticity, outliers, or non-linearity.
- Normally distributed residuals are not required for OLS consistency but
  affect finite-sample inference and confidence interval coverage.
