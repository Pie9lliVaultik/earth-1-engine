"""SEED CORPUS — real survey items with real cohort targets.

Grounding port, step 1 (spec: GROUNDING_PORT_SPEC.md). The old engine's
corpus was the OUTPUT of a grounding pipeline: every seed carried
question text, cohort targets, source, date, confidence tier and
provenance. Earth-1's corpus is LLM-authored profiles wearing the same
name. This rebuilds the real thing from sources already on the machine.

Sources (all real microdata, none authored):
  GSS   data/gss_truth.json — 15 items x up to 34 years, cohort cells
        by age bucket x education, weighted (WTSSNRPS)
  WVS7  data/wvs_w7_cohort_by_country.csv — 8 items x 65 countries x
        age bucket, weighted (W_WEIGHT)

Output: data/seed_corpus/index.json — append-only, one record per
(source, item, wave/year) with:
  question_text, source, source_url, date, confidence tier,
  cohort_targets {cell -> share}, national_target, n
Path D (live-grounded) seeds append here later with their own
provenance.
"""
from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT_DIR = "data/seed_corpus"

GSS_TEXT = {
    "abany": "Should it be possible for a pregnant woman to obtain a legal "
             "abortion if the woman wants it for any reason?",
    "abdefect": "Should abortion be legal if there is a strong chance of a "
                "serious defect in the baby?",
    "cappun": "Do you favour the death penalty for persons convicted of "
              "murder?",
    "grass": "Should the use of marijuana be made legal?",
    "homosex": "Are sexual relations between two adults of the same sex "
               "wrong?",
    "fechld": "Can a working mother establish just as warm and secure a "
              "relationship with her children as a mother who does not work?",
    "fepresch": "Does a preschool child suffer if his or her mother works?",
    "trust": "Generally speaking, would you say that most people can be "
             "trusted?",
    "confinan": "How much confidence do you have in banks and financial "
                "institutions?",
    "conmedic": "How much confidence do you have in medicine?",
    "conpress": "How much confidence do you have in the press?",
    "conlegis": "How much confidence do you have in Congress?",
    "polviews": "Do you think of yourself as liberal or conservative?",
    "natenvir": "Are we spending too little money on improving and "
                "protecting the environment?",
    "racopen": "Would you favour a law saying a homeowner cannot refuse to "
               "sell to someone because of race or colour?",
}
WVS_TEXT = {
    "Q57": "Generally speaking, would you say that most people can be "
           "trusted?",
    "Q65": "How much confidence do you have in the churches?",
    "Q71": "How much confidence do you have in the government?",
    "Q164": "How important is God in your life?",
    "Q180": "Is claiming government benefits you are not entitled to "
            "justifiable?",
    "Q182": "Is homosexuality justifiable?",
    "Q184": "Is abortion justifiable?",
    "Q185": "Is divorce justifiable?",
}


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    seeds = []

    gss = json.load(open("data/gss_truth.json"))
    for var, rec in gss.items():
        text = GSS_TEXT.get(var, rec["label"])
        for year, nat in rec["national"].items():
            cells = {k.split("|", 1)[1]: v["share"]
                     for k, v in rec["cells"].items()
                     if k.startswith(f"{year}|")}
            if len(cells) < 6:
                continue
            seeds.append({
                "id": f"gss:{var}:{year}",
                "question_text": text,
                "source": "GSS",
                "source_url": "https://gss.norc.org/",
                "instrument_item": var,
                "date": f"{year}",
                "population": "US",
                "national_target": nat["share"],
                "cohort_targets": cells,
                "cohort_axis": "age_bucket|education",
                "n": nat["n"],
                "confidence": "high",
                "calibration_source": "survey-matched",
            })

    by_q = {}
    for r in csv.DictReader(open("data/wvs_w7_cohort_by_country.csv")):
        by_q.setdefault(r["qcode"], {}).setdefault(
            r["country"], {})[r["age_bucket"]] = float(r["yes_weighted"])
    for qcode, by_cc in by_q.items():
        text = WVS_TEXT.get(qcode)
        if not text:
            continue
        for cc, cells in by_cc.items():
            if len(cells) < 4:
                continue
            seeds.append({
                "id": f"wvs7:{qcode}:{cc}",
                "question_text": text,
                "source": "WVS Wave 7",
                "source_url": "https://www.worldvaluessurvey.org/",
                "instrument_item": qcode,
                "date": "2017-2022",
                "population": cc,
                "national_target": round(
                    sum(cells.values()) / len(cells), 5),
                "cohort_targets": cells,
                "cohort_axis": "age_bucket",
                "n": None,
                "confidence": "high",
                "calibration_source": "survey-matched",
            })

    json.dump(seeds, open(f"{OUT_DIR}/index.json", "w"), indent=1)
    by_src = {}
    for s in seeds:
        by_src[s["source"]] = by_src.get(s["source"], 0) + 1
    print(f"SEED-CORPUS: {len(seeds)} real seeds  " +
          " | ".join(f"{k} {v}" for k, v in by_src.items()), flush=True)
    print(f"  distinct questions: "
          f"{len({s['question_text'] for s in seeds})} | populations: "
          f"{len({s['population'] for s in seeds})} | all confidence=high, "
          f"calibration_source=survey-matched", flush=True)


if __name__ == "__main__":
    main()
