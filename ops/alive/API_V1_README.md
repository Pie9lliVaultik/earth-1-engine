# Earth-1 API v1 — the typed ship surface

One adapter, six endpoints, frozen 0.9 physics. Base URL: `/v1`. Auth: `Authorization: Bearer <key>` (per-key rate limits; every request lands in the hash-chained question log).

- `POST /ask` — any question. Body: `{text, class?, outcomes?, country?, fidelity: "20k"|"200k"}`. Routes to OPINION (present-world readout), FORECAST (real branch worlds, p_model), or CONDITIONAL (fork set). `fidelity: "200k"` returns `{job_id}`.
- `POST /consequences` — full ORDER 0–4 structured consequence report for a scenario. Cached by (scenario, ledger cutoff, fidelity).
- `GET /forecast/{id}` — a registered prospective forecast: p_model, market first-seen price (display only, never scored), status, resolution when known.
- `GET /world/state` — eight-force field by country with centroids and Conviction Index (the 3D layer's base render). adm1: registered limitation, pending.
- `GET /world/history` — live chronicle cascade episodes (date-range history pending the recorder store).
- `GET /health` — epoch, freeze tag, tree hash, question-log head, per-class calibration table.

Contract, enforced in code: every response carries epoch/freeze-tag/tree-hash/ledger-cutoff and per-line `calibration_tier ∈ {CALIBRATED, UNCALIBRATED, ABSTAIN, KNOWN-DEFECT}`; ABSTAIN lines never carry numbers; `p_model` is the only scored field and market prices are display-only; branch runs happen on copies — no request can touch a production epoch or any sealed (HOLDOUT/PROSPECTIVE-role) file.

**Product line:** Ask anything. Settled facts are answered with a source. Belief-driven outcomes are simulated and stamped with how well calibrated that class is. Exogenous events are answered from public evidence and paired with what the population would do if they happened.
