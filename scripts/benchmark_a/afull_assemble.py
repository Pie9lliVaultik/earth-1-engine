"""A-FULL-1 table assembler.

Reads every artifact the A-FULL-1 chain (afull_run.sh) produced under
$EARTH1_AFULL_OUT (plus the task i/ii outputs that land in the repo's
data/cycles/) and writes $EARTH1_AFULL_OUT/AFULL_TABLE.json: one row per
(task x estate) over tasks {i,ii,iii,iv,v} x estates
{wvs_heldout, pew_frame_dev, goqa_dev}.

Row statuses: OK (scored), NOT_RUN (estate does not support the task —
one-line reason), PENDING (artifact expected but missing/unparseable —
never a crash).

Verdicts: level metrics (MAE in pp) get the campaign tier
WIN<=3.5 / GOOD<=5.0 / ACCEPT<=7.0 / MISS; non-level metrics get
WIN/LOSS vs the strongest baseline.

usage:
  afull_assemble.py             assemble from $EARTH1_AFULL_OUT
  afull_assemble.py --out DIR [--repo DIR]
  afull_assemble.py --selftest  synthetic-artifact self test
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TASKS = ("i", "ii", "iii", "iv", "v")
TASK_NAMES = {
    "i": "country means (four-arm LOO table)",
    "ii": "cohort cells (reliability-weighted frozen readout + A-v2 protocol ii)",
    "iii": "joints (energy distance vs independence, MRP-anchored marginals)",
    "iv": "held-out items / zero-shot transfer (cohort cells)",
    "v": "cross-wave deltas",
}
ESTATES = ("wvs_heldout", "pew_frame_dev", "goqa_dev")
ESTATE_FILES = {  # repo-relative source-of-truth file per estate, for sha256
    "wvs_heldout": "data/benchmark_a/confirm_targets_v2.json",
    "pew_frame_dev": "data/concordance/goqa_dev.json",
    "goqa_dev": "data/concordance/goqa_dev.json",
}
TIERS = {"WIN": 3.5, "GOOD": 5.0, "ACCEPT": 7.0}


def tier(mae_pp):
    if mae_pp is None:
        return None
    for name, cut in (("WIN", 3.5), ("GOOD", 5.0), ("ACCEPT", 7.0)):
        if mae_pp <= cut:
            return name
    return "MISS"


def sha256_of(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def find_artifact(out_dir, repo, name, also_cycles=True, globs=()):
    """First hit wins: $OUT/name, $OUT globs, repo data/cycles/name."""
    cands = [os.path.join(out_dir, name)]
    for g in globs:
        cands.extend(sorted(glob.glob(os.path.join(out_dir, g))))
    if also_cycles:
        cands.append(os.path.join(repo, "data", "cycles", name))
    for p in cands:
        if os.path.isfile(p):
            d = load_json(p)
            if d is not None:
                return d, p
    return None, None


def base_row(task, estate):
    return {"task": task, "task_name": TASK_NAMES[task], "estate": estate,
            "status": "PENDING", "reason": None, "metric": None,
            "earth1": None, "seed_sigma": None, "baselines": {},
            "verdict": None, "coverage": None, "source_artifact": None}


def pick(d, *keys):
    """First present key in a dict (tolerant reader for sibling artifacts)."""
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def harness_estate_block(art, estate):
    """Locate an estate section inside a sibling-harness artifact."""
    if not isinstance(art, dict):
        return None
    for holder in (art.get("estates"), art.get("results"), art):
        if isinstance(holder, dict) and isinstance(holder.get(estate), dict):
            return holder[estate]
    # score_sb1 naming: campaign pew_frame_dev is labelled goqa_dev in-code
    if estate == "pew_frame_dev":
        return harness_estate_block(art, "goqa_dev") \
            if art.get("goqa_dev") else None
    return None


# ------------------------------------------------------------------ task i
def rows_task_i(out_dir, repo):
    rows, extremes = [], {}
    src = {"wvs_heldout": "sb1_wvs_heldout.json",
           "pew_frame_dev": "sb1_goqa_dev.json"}
    for estate in ESTATES:
        r = base_row("i", estate)
        r["metric"] = "national_mae_pp (per-item leave-one-country-out)"
        if estate == "goqa_dev":
            r["status"] = "NOT_RUN"
            r["reason"] = ("no registered loader distinct from pew_frame_dev "
                           "(score_sb1 'goqa_dev' = data/concordance/"
                           "goqa_dev.json = pew_frame_dev; see that row)")
            rows.append(r)
            continue
        art, p = find_artifact(out_dir, repo, src[estate])
        if art is None:
            r["reason"] = f"missing artifact {src[estate]}"
            rows.append(r)
            continue
        try:
            r["status"] = "OK"
            r["source_artifact"] = p
            r["earth1"] = art["earth1"]["mae_pp"]
            r["seed_sigma"] = art["earth1"].get("seed_sigma")
            r["baselines"] = {m: art[m]["mae_pp"]
                             for m in ("mrsp", "naive", "region") if m in art}
            r["verdict"] = art.get("tier") or tier(r["earth1"])
            r["excess_vs_mrsp"] = art.get("excess_vs_mrsp")
            r["beats_naive"] = art.get("beats_naive")
            r["coverage"] = {"n_items_scored": art.get("n_items_scored")}
            if estate == "pew_frame_dev":
                r["note"] = ("score_sb1 labels this estate 'goqa_dev'; it is "
                             "the campaign's pew_frame_dev (469 items, "
                             "judge-free by construction)")
            extremes[estate] = {"worst5": art.get("worst5"),
                                "best5": art.get("best5"),
                                "top3_error_cells": art.get("top3_error_cells")}
        except (KeyError, TypeError) as e:
            r["status"] = "PENDING"
            r["reason"] = f"artifact parse error in {p}: {e!r}"
        rows.append(r)
    return rows, extremes


# ----------------------------------------------------------------- task ii
def rows_task_ii(out_dir, repo, av2_sb):
    rows = []
    for estate in ESTATES:
        r = base_row("ii", estate)
        r["metric"] = "cohort_cell_mae_pp"
        if estate != "wvs_heldout":
            r["status"] = "NOT_RUN"
            r["reason"] = ("cohort cells are WVS-only (campaign order; no "
                           "cohort ground truth exists for GOQA/Pew estates)")
            rows.append(r)
            continue
        frozen, fp = find_artifact(out_dir, repo, "frozen_afull1_c2plus.json")
        ii = (av2_sb or {}).get("tasks", {}).get("ii_cohorts")
        try:
            if ii:
                r["status"] = "OK"
                r["source_artifact"] = "av2/scoreboard_confirm_v2.json"
                r["metric"] = "cohort_cell_mae_pp (A-v2 protocol ii, 200k)"
                r["earth1"] = ii["mae_pp"]["e1"]
                r["baselines"] = {k: v for k, v in ii["mae_pp"].items()
                                 if k != "e1"}
                r["verdict"] = tier(r["earth1"])
                r["gate"] = ii.get("gate")
                r["gate_rule"] = ii.get("gate_rule")
                r["strongest_baseline"] = ii.get("strongest_baseline")
                r["relative_reduction"] = ii.get("relative_reduction")
                r["gradient_direction_pct"] = ii.get("gradient_direction_pct")
                r["beats_strongest_baseline"] = bool(
                    r["earth1"] < min(r["baselines"].values()))
                r["coverage"] = {"n_cells": ii.get("n_cells")}
            elif frozen:
                r["status"] = "OK"
                r["reason"] = ("A-v2 protocol-ii scoreboard missing; frozen-"
                               "cell readout used as primary")
            else:
                r["reason"] = ("neither av2/scoreboard_confirm_v2.json "
                               "(ii_cohorts) nor frozen_afull1_c2plus.json "
                               "found")
            if frozen:
                fr = {"label": frozen.get("label"),
                      "model_mae_pp": frozen.get("model_mae_pp"),
                      "invariant_floor_mae_pp":
                          frozen.get("invariant_floor_mae_pp"),
                      "level_mae_pp": frozen.get("level_mae_pp"),
                      "structure_dev_mae_pp":
                          frozen.get("structure_dev_mae_pp"),
                      "structure_zero_ref_pp":
                          frozen.get("structure_zero_ref_pp"),
                      "beats_invariant_floor": None,
                      "coverage": {
                          "n_frozen_cells_scored":
                              frozen.get("n_frozen_cells_scored"),
                          "world_thin_cell_fallbacks":
                              frozen.get("world_thin_cell_fallbacks")},
                      "flags": frozen.get("flags"),
                      "frozen_sha": frozen.get("frozen_sha"),
                      "source_artifact": fp}
                if (frozen.get("model_mae_pp") is not None
                        and frozen.get("invariant_floor_mae_pp") is not None):
                    fr["beats_invariant_floor"] = bool(
                        frozen["model_mae_pp"]
                        < frozen["invariant_floor_mae_pp"])
                r["frozen_cell_readout_reliability_weighted"] = fr
                if r["earth1"] is None:
                    r["metric"] = ("cohort_cell_mae_pp (frozen 18333-cell "
                                   "reliability-weighted readout, 20k)")
                    r["earth1"] = frozen.get("model_mae_pp")
                    r["baselines"] = {"invariant_floor":
                                      frozen.get("invariant_floor_mae_pp")}
                    r["verdict"] = tier(r["earth1"])
                    r["coverage"] = fr["coverage"]
        except (KeyError, TypeError) as e:
            r["status"] = "PENDING"
            r["reason"] = f"artifact parse error: {e!r}"
        rows.append(r)
    return rows


# ---------------------------------------------------------------- task iii
def rows_task_iii(out_dir, repo, av2_sb, confirm, joints_art, joints_path):
    rows, extremes = [], {}
    for estate in ESTATES:
        r = base_row("iii", estate)
        r["metric"] = "joint_energy_distance (median over countries)"
        if estate != "wvs_heldout":
            r["status"] = "NOT_RUN"
            r["reason"] = ("no respondent-level or crosstab data exists for "
                           "the GOQA/Pew estates (marginals only); joints "
                           "feasible on the WVS estate alone")
            rows.append(r)
            continue
        iii = (av2_sb or {}).get("tasks", {}).get("iii_joints")
        try:
            if iii:
                r["status"] = "OK"
                r["source_artifact"] = "av2/scoreboard_confirm_v2.json"
                med = iii.get("median_energy", {})
                r["earth1"] = med.get("e1_mrp_anchored")
                r["baselines"] = {"independent_mrp": med.get("independent_mrp")}
                r["verdict"] = ("WIN" if iii.get("gate")
                                else ("LOSS" if r["earth1"] is not None
                                      and med.get("independent_mrp") is not None
                                      and r["earth1"] >= med["independent_mrp"]
                                      else "LOSS"))
                r["gate"] = iii.get("gate")
                r["gate_rule"] = iii.get("gate_rule")
                r["independent_minus_e1_ci"] = iii.get("independent_minus_e1_ci")
                r["coverage"] = {"n_countries": iii.get("n_countries")}
                pc = iii.get("per_country") or []
                diffs = sorted(((e1 - ind, iso) for iso, ind, e1 in pc),
                               reverse=True)
                extremes["wvs_heldout"] = {
                    "worst5": [{"country": c, "e1_minus_independent": round(d, 6)}
                               for d, c in diffs[:5]],
                    "best5": [{"country": c, "e1_minus_independent": round(d, 6)}
                              for d, c in diffs[-5:]]}
            else:
                r["reason"] = ("av2/scoreboard_confirm_v2.json (iii_joints) "
                               "missing")
        except (KeyError, TypeError, ValueError) as e:
            r["status"] = "PENDING"
            r["reason"] = f"artifact parse error: {e!r}"
        # joints item/pair provenance
        ji = (confirm or {}).get("joint_items")
        r["joint_items"] = ji
        if joints_art is not None:
            r["pairs_harness"] = {"source_artifact": joints_path,
                                  "pairs": pick(joints_art, "pairs",
                                                "pair_list", "item_pairs"),
                                  "summary": pick(joints_art, "summary",
                                                  "metrics", "result")}
        rows.append(r)
    return rows, extremes


# ----------------------------------------------------------------- task iv
def rows_task_iv(out_dir, repo, av2_sb, confirm, held_art, held_path):
    rows = []
    for estate in ESTATES:
        r = base_row("iv", estate)
        r["metric"] = "zeroshot_cohort_cell_mae_pp (transfer)"
        blk = harness_estate_block(held_art, estate) if held_art else None
        try:
            if estate == "wvs_heldout":
                iv = (av2_sb or {}).get("tasks", {}).get("iv_zeroshot_cohorts")
                if iv:
                    r["status"] = "OK"
                    r["source_artifact"] = "av2/scoreboard_confirm_v2.json"
                    r["earth1"] = iv["mae_pp"].get("e1_transfer")
                    r["baselines"] = {k: v for k, v in iv["mae_pp"].items()
                                     if k != "e1_transfer"}
                    r["verdict"] = tier(r["earth1"])
                    r["gate"] = iv.get("gate")
                    r["gate_rule"] = iv.get("gate_rule")
                    r["strongest_baseline"] = iv.get("strongest_baseline")
                    r["beats_strongest_baseline"] = bool(
                        r["earth1"] is not None and r["baselines"]
                        and r["earth1"] < min(r["baselines"].values()))
                    r["coverage"] = {"n_cells": iv.get("n_cells")}
                else:
                    r["reason"] = ("av2/scoreboard_confirm_v2.json "
                                   "(iv_zeroshot_cohorts) missing")
            elif blk is not None:
                r["status"] = "OK"
                r["source_artifact"] = held_path
                r["earth1"] = pick(blk, "earth1_mae_pp", "e1_mae_pp",
                                   "mae_pp", "earth1")
                r["baselines"] = pick(blk, "baselines") or {}
                r["verdict"] = tier(r["earth1"]) if isinstance(
                    r["earth1"], (int, float)) else "SEE_ARTIFACT"
                r["coverage"] = pick(blk, "coverage", "n_items", "n_cells")
            else:
                r["reason"] = ("afull_heldout_items artifact missing or "
                               "lacks this estate")
            # split provenance
            if blk is not None:
                r["split"] = {"seed": pick(blk, "split_seed", "seed"),
                              "heldout_items": pick(blk, "heldout_items",
                                                    "test_items", "items"),
                              "train_items": pick(blk, "train_items")}
            elif estate == "wvs_heldout" and confirm:
                r["split"] = {"seed": 42,
                              "heldout_items": confirm.get("zeroshot_items"),
                              "note": ("v2 zeroshot items are a deterministic "
                                       "stride split of the 98 confirm items; "
                                       "neighbour ridge fit at seed 42")}
        except (KeyError, TypeError) as e:
            r["status"] = "PENDING"
            r["reason"] = f"artifact parse error: {e!r}"
        rows.append(r)
    return rows


# ------------------------------------------------------------------ task v
def rows_task_v(out_dir, repo, av2_sb, cw_art, cw_path):
    rows = []
    for estate in ESTATES:
        r = base_row("v", estate)
        r["metric"] = "cross_wave_delta_mae_pp"
        if estate != "wvs_heldout":
            r["status"] = "NOT_RUN"
            r["reason"] = ("second Pew wave not available (pew2019_judge is "
                           "HOLDOUT with path PENDING_FETCH; GOQA carries no "
                           "wave/year metadata)")
            rows.append(r)
            continue
        try:
            if cw_art is not None and str(pick(cw_art, "status") or "OK") \
                    .upper() in ("NOT_RUN", "BLOCKED", "BLOCKED-ON-DATA",
                                 "DATA-BLOCKED"):
                r["status"] = "NOT_RUN"
                r["reason"] = pick(cw_art, "reason", "note") or \
                    "crosswave harness declared NOT_RUN"
                r["source_artifact"] = cw_path
            elif cw_art is not None:
                r["status"] = "OK"
                r["source_artifact"] = cw_path
                r["earth1"] = pick(cw_art, "earth1_delta_mae_pp",
                                   "e1_delta_mae_pp", "delta_mae_pp",
                                   "earth1")
                r["baselines"] = pick(cw_art, "baselines") or {}
                if isinstance(r["earth1"], (int, float)) and r["baselines"]:
                    vals = [v for v in r["baselines"].values()
                            if isinstance(v, (int, float))]
                    r["verdict"] = ("WIN" if vals and r["earth1"] < min(vals)
                                    else "LOSS")
                else:
                    r["verdict"] = "SEE_ARTIFACT"
                r["coverage"] = pick(cw_art, "coverage", "n_questions",
                                     "n_items")
                r["provenance_caveat"] = pick(cw_art, "provenance_caveat") or \
                    ("W6->W7 paired aggregates in earth1/wvs_paired.py are "
                     "best-effort estimates; must be verified against the "
                     "official WVS database before external publication")
                r["per_question"] = pick(cw_art, "per_question", "questions")
            else:
                v = (av2_sb or {}).get("tasks", {}).get("v_cross_wave") or {}
                r["status"] = "NOT_RUN"
                r["reason"] = ("data-blocked: frozen harness reports "
                               f"status={v.get('status', 'BLOCKED-ON-DATA')}; "
                               "afull_crosswave artifact absent (only the "
                               "unverified 15-question W6->W7 paired "
                               "aggregates exist)")
        except (KeyError, TypeError) as e:
            r["status"] = "PENDING"
            r["reason"] = f"artifact parse error: {e!r}"
        rows.append(r)
    return rows


# ---------------------------------------------------------------- assemble
def assemble(out_dir, repo):
    av2_sb = load_json(os.path.join(out_dir, "av2",
                                    "scoreboard_confirm_v2.json"))
    confirm = load_json(os.path.join(out_dir, "av2",
                                     "confirm_targets_v2.json")) \
        or load_json(os.path.join(repo, "data", "benchmark_a",
                                  "confirm_targets_v2.json"))
    joints_art, joints_path = find_artifact(
        out_dir, repo, "afull_joints.json", also_cycles=False,
        globs=("afull_joints*.json",))
    held_art, held_path = find_artifact(
        out_dir, repo, "afull_heldout_items.json", also_cycles=False,
        globs=("afull_heldout*.json",))
    cw_art, cw_path = find_artifact(
        out_dir, repo, "afull_crosswave.json", also_cycles=False,
        globs=("afull_crosswave*.json",))
    flags_stamp = load_json(os.path.join(out_dir, "flags_stamp.json"))

    rows, extremes = [], {}
    r1, e1 = rows_task_i(out_dir, repo)
    rows += r1
    extremes["i"] = e1 or {"note": "no task-i artifacts found"}
    rows += rows_task_ii(out_dir, repo, av2_sb)
    extremes["ii"] = {"note": ("per-cell errors are not persisted by either "
                               "task-ii instrument (aggregates only)")}
    r3, e3 = rows_task_iii(out_dir, repo, av2_sb, confirm,
                           joints_art, joints_path)
    rows += r3
    extremes["iii"] = e3 or {"note": "no per-country joints rows found"}
    rows += rows_task_iv(out_dir, repo, av2_sb, confirm, held_art, held_path)
    extremes["iv"] = {"note": ("per-cell errors not persisted by the frozen "
                               "iv scorer (aggregates only)")}
    rows += rows_task_v(out_dir, repo, av2_sb, cw_art, cw_path)
    extremes["v"] = ({"per_question": pick(cw_art, "per_question",
                                           "questions")}
                     if cw_art else {"note": "crosswave artifact absent"})

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"],
                                capture_output=True, text=True,
                                cwd=repo).stdout.strip() or None
    except Exception:
        commit = None

    wvs_row_iv = next(r for r in rows
                      if r["task"] == "iv" and r["estate"] == "wvs_heldout")
    table = {
        "campaign": "A-FULL-1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": commit,
        "flag_stamp": flags_stamp or {
            "note": "flags_stamp.json absent; env at assemble time",
            "flags": {k: v for k, v in sorted(os.environ.items())
                      if k.startswith("EARTH1_")}},
        "estate_sha256": {e: sha256_of(os.path.join(repo, ESTATE_FILES[e]))
                          for e in ESTATES},
        "tier_rule": "level metrics: WIN<=3.5 / GOOD<=5.0 / ACCEPT<=7.0 pp; "
                     "else MISS. Non-level metrics: WIN/LOSS vs baseline.",
        "rows": rows,
        "per_task_extremes": extremes,
        "joints": {"joint_items": (confirm or {}).get("joint_items"),
                   "pairs": pick(joints_art, "pairs", "pair_list",
                                 "item_pairs")},
        "heldout_split": wvs_row_iv.get("split"),
        "row_counts": {s: sum(1 for r in rows if r["status"] == s)
                       for s in ("OK", "PENDING", "NOT_RUN")},
        "discrepancies": [
            "EARTH1_COHORT_READOUT has no consumer anywhere in the repo; "
            "reliability weighting is intrinsic to frozen_score.py",
            "campaign estate 'goqa_dev (GOQA dev split)' has no loader "
            "distinct from pew_frame_dev; its rows are NOT_RUN aliases",
            "score_sb1.py labels the pew_frame_dev estate 'goqa_dev' in its "
            "artifact filenames (sb1_goqa_dev.json)",
        ],
    }
    out_path = os.path.join(out_dir, "AFULL_TABLE.json")
    with open(out_path, "w") as f:
        json.dump(table, f, indent=1)
    return table, out_path


# ---------------------------------------------------------------- selftest
def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f)


def selftest():
    import tempfile
    base = tempfile.mkdtemp(prefix="afull_selftest_")
    repo = os.path.join(base, "repo")
    os.makedirs(os.path.join(repo, "data", "cycles"), exist_ok=True)

    def synth_dir(name):
        d = os.path.join(base, name)
        os.makedirs(d, exist_ok=True)
        return d

    # ---- pass 1: partial artifacts (no heldout/crosswave harness) --------
    out1 = synth_dir("out1")
    _write(os.path.join(out1, "sb1_wvs_heldout.json"), {
        "earth1": {"mae_pp": 11.775, "seed_sigma": 0.204},
        "mrsp": {"mae_pp": 11.18, "seed_sigma": 0.0},
        "naive": {"mae_pp": 12.802, "seed_sigma": 0.0},
        "region": {"mae_pp": 9.696, "seed_sigma": 0.0},
        "excess_vs_mrsp": 0.595, "tier": "MISS", "beats_naive": True,
        "n_items_scored": 98,
        "worst5": [{"err_pp": 84.7, "country": "TJ", "family": "other"}],
        "best5": [{"err_pp": 0.01, "country": "US", "family": "economy"}],
        "top3_error_cells": []})
    _write(os.path.join(out1, "sb1_goqa_dev.json"), {
        "earth1": {"mae_pp": 4.2, "seed_sigma": 0.09},
        "mrsp": {"mae_pp": 11.06, "seed_sigma": 0.0},
        "naive": {"mae_pp": 12.02, "seed_sigma": 0.0},
        "region": {"mae_pp": 10.31, "seed_sigma": 0.0},
        "excess_vs_mrsp": -6.86, "tier": "GOOD", "beats_naive": True,
        "n_items_scored": 468, "worst5": [], "best5": [],
        "top3_error_cells": []})
    _write(os.path.join(out1, "frozen_afull1_c2plus.json"), {
        "label": "afull1_c2plus",
        "flags": {"EARTH1_SUBSTRATE_FLAG": "c2plus_v1"},
        "model_mae_pp": 11.974, "invariant_floor_mae_pp": 13.025,
        "n_frozen_cells_scored": 18333, "world_thin_cell_fallbacks": 3786,
        "level_mae_pp": 11.265, "structure_dev_mae_pp": 3.974,
        "structure_zero_ref_pp": 2.571, "frozen_sha": "55777e15f46c4d11"})
    _write(os.path.join(out1, "av2", "scoreboard_confirm_v2.json"), {
        "stamp": {"commit": "deadbeef"},
        "tasks": {
            "i_sanity": {"gate": True},
            "ii_cohorts": {
                "mae_pp": {"national_copy": 10.08, "global_gradient": 9.92,
                           "cohort_mrp": 10.06, "e1": 10.58},
                "gradient_direction_pct": {"e1": 50.5},
                "strongest_baseline": "global_gradient",
                "relative_reduction": -0.066, "n_cells": 164997,
                "gate": False, "gate_rule": ">=10% AND >=75% gradient"},
            "iii_joints": {
                "n_countries": 3,
                "median_energy": {"independent_mrp": 0.1858,
                                  "e1_mrp_anchored": 0.1848},
                "independent_minus_e1_ci": [-0.002, -0.008, 0.003],
                "per_country": [["US", 0.20, 0.19], ["DE", 0.18, 0.20],
                                ["JP", 0.15, 0.15]],
                "gate": False, "gate_rule": "lower median, CI excl 0"},
            "iv_zeroshot_cohorts": {
                "mae_pp": {"national_copy": 21.09, "neighbour_offset": 21.21,
                           "e1_transfer": 21.28},
                "strongest_baseline": "national_copy", "n_cells": 4188,
                "gate": False, "gate_rule": "beat strongest, CI excl 0"},
            "v_cross_wave": {"status": "BLOCKED-ON-DATA", "gate": None}},
        "compression_trace_summary": {}})
    _write(os.path.join(out1, "av2", "confirm_targets_v2.json"), {
        "joint_items": ["Q7", "Q8", "Q9", "Q11", "Q12", "Q13", "Q14", "Q15"],
        "zeroshot_items": ["Q7", "Q20", "Q47", "Q63", "Q83", "Q135",
                           "Q166", "Q195"]})
    _write(os.path.join(out1, "afull_joints.json"), {
        "pairs": [["Q7", "Q8"], ["Q9", "Q11"]],
        "summary": {"n_pairs": 2}})
    _write(os.path.join(out1, "flags_stamp.json"), {
        "campaign": "A-FULL-1", "git_commit": "deadbeef",
        "flags": {"EARTH1_SUBSTRATE": "c2plus_v1"}})

    t1, p1 = assemble(out1, repo)
    assert os.path.isfile(p1) and load_json(p1), "table not written/valid"
    assert len(t1["rows"]) == 15, f"expected 15 rows, got {len(t1['rows'])}"
    by = {(r["task"], r["estate"]): r for r in t1["rows"]}
    assert by[("i", "wvs_heldout")]["status"] == "OK"
    assert by[("i", "wvs_heldout")]["verdict"] == "MISS"
    assert by[("i", "wvs_heldout")]["earth1"] == 11.775
    assert by[("i", "pew_frame_dev")]["verdict"] == "GOOD"
    assert by[("i", "goqa_dev")]["status"] == "NOT_RUN"
    assert by[("ii", "wvs_heldout")]["status"] == "OK"
    assert by[("ii", "wvs_heldout")]["verdict"] == "MISS"
    assert by[("ii", "wvs_heldout")][
        "frozen_cell_readout_reliability_weighted"]["model_mae_pp"] == 11.974
    assert by[("ii", "pew_frame_dev")]["status"] == "NOT_RUN"
    assert by[("ii", "goqa_dev")]["status"] == "NOT_RUN"
    assert by[("iii", "wvs_heldout")]["status"] == "OK"
    assert by[("iii", "wvs_heldout")]["verdict"] in ("WIN", "LOSS")
    assert by[("iii", "pew_frame_dev")]["status"] == "NOT_RUN"
    assert by[("iv", "wvs_heldout")]["status"] == "OK"
    assert by[("iv", "wvs_heldout")]["verdict"] == "MISS"
    assert by[("iv", "pew_frame_dev")]["status"] == "PENDING"
    assert by[("v", "wvs_heldout")]["status"] == "NOT_RUN"
    assert "data-blocked" in by[("v", "wvs_heldout")]["reason"]
    assert by[("v", "pew_frame_dev")]["status"] == "NOT_RUN"
    assert t1["joints"]["pairs"] == [["Q7", "Q8"], ["Q9", "Q11"]]
    assert t1["heldout_split"]["heldout_items"][0] == "Q7"
    assert t1["per_task_extremes"]["iii"]["wvs_heldout"]["worst5"][0][
        "country"] == "DE"
    assert t1["row_counts"] == {"OK": 4, "PENDING": 3, "NOT_RUN": 8}
    print("selftest pass 1 OK (partial artifacts):", t1["row_counts"])

    # ---- pass 2: add heldout + crosswave harness artifacts ---------------
    _write(os.path.join(out1, "afull_heldout_items.json"), {
        "estates": {
            "pew_frame_dev": {"earth1_mae_pp": 6.5, "split_seed": 777,
                              "heldout_items": ["qidA", "qidB"],
                              "train_items": ["qidC"],
                              "baselines": {"naive": 7.7},
                              "coverage": {"n_items": 2}},
            "goqa_dev": {"earth1_mae_pp": 3.1, "split_seed": 777,
                         "heldout_items": ["qidD"],
                         "baselines": {"naive": 3.0}}}})
    _write(os.path.join(out1, "afull_crosswave.json"), {
        "earth1_delta_mae_pp": 5.5,
        "baselines": {"zero_delta": 6.1, "persistence": 5.9},
        "coverage": {"n_questions": 15},
        "per_question": [{"q": "t_trust", "delta_err_pp": 4.0}]})
    t2, _ = assemble(out1, repo)
    by2 = {(r["task"], r["estate"]): r for r in t2["rows"]}
    assert by2[("iv", "pew_frame_dev")]["status"] == "OK"
    assert by2[("iv", "pew_frame_dev")]["verdict"] == "ACCEPT"
    assert by2[("iv", "pew_frame_dev")]["split"]["seed"] == 777
    assert by2[("iv", "goqa_dev")]["verdict"] == "WIN"
    assert by2[("v", "wvs_heldout")]["status"] == "OK"
    assert by2[("v", "wvs_heldout")]["verdict"] == "WIN"
    assert by2[("v", "wvs_heldout")]["earth1"] == 5.5
    print("selftest pass 2 OK (harness artifacts):", t2["row_counts"])

    # ---- pass 3: empty out dir -> no crash, all rows PENDING/NOT_RUN -----
    out3 = synth_dir("out3")
    t3, p3 = assemble(out3, repo)
    assert len(t3["rows"]) == 15
    assert t3["row_counts"]["OK"] == 0
    assert all(r["status"] in ("PENDING", "NOT_RUN") for r in t3["rows"])
    assert os.path.isfile(p3)
    print("selftest pass 3 OK (empty dir):", t3["row_counts"])

    print("SELFTEST PASS")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    out_dir = os.environ.get("EARTH1_AFULL_OUT",
                             "/opt/earth1-data/benchmark_a_full1")
    repo = ROOT
    if "--out" in argv:
        out_dir = argv[argv.index("--out") + 1]
    if "--repo" in argv:
        repo = argv[argv.index("--repo") + 1]
    os.makedirs(out_dir, exist_ok=True)
    table, path = assemble(out_dir, repo)
    print("AFULL_TABLE written:", path)
    print("row counts:", json.dumps(table["row_counts"]))
    for r in table["rows"]:
        print(f"  [{r['status']:>7}] task {r['task']:>3} x {r['estate']:<14}"
              f" earth1={r['earth1']} verdict={r['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
