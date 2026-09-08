# Release staging — v3.1 assessability package (audit move 2)

Contents, staged for PUBLIC release on founder approval (nothing here is
released yet; staging is not release):

- baselines_agreement.py / .json — recomputes Earth-1's 83.5% / 14.2%
  headline from data/cycles/distance2026/cells.csv and the LOO baseline
  agreement rows (naive 81.2/12.6; region-copy 84.3/15.6).
- provenance_split.py / .json — the 63-measured vs tier-fallback split.
- protest_confound.py / .json — income-stratified re-scoring of the
  protest-onset register (partial rho 0.339, exact p 0.176).
- accumulation_null.py / .json — the shock-free accumulation null family
  for the wealth-concentration claim (family ceiling 17.63 / 0.141;
  surplus variant 26.15 / 0.162; measured 29.48 / 0.194).
- learning_scorer_check.py / .json — 15/15 consistency checks of
  data/cycles/v02_report.json against the published Experience Loop
  gates; the scorer-extension commits are ac6d35d + 25b956b.

To complete the release: add data/cycles/distance2026/cells.csv (per-cell
predictions, judge values, abstention flags — survey values are public)
and the per-event frozen outputs under ops/alive/historical/. Withheld
regardless of release: engine physics, constants, readout construction,
injector templates, registered vocabulary. Note: the frozen-forecast
JSONs contain full-precision branch distances alongside p_model; strip
the distances before public release (they reconstruct the readout
mapping — see the v3 leak check).
