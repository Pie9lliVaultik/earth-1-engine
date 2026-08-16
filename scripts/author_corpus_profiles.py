#!/usr/bin/env python3
"""Author temporal response profiles for every corpus entry (ONE LAW).

Blind: question text only, temperature 0, one call per entry. Resumable
— NaN rows are the un-authored ones; the script fills them and saves
every 25 entries. ~1,564 Haiku calls, a few dollars, one night.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.corpus import QuestionCorpus
from earth1.news_perception import perceive_question_response

CORPUS = ROOT / "data" / "corpus" / "goqa_seed"


def main():
    c = QuestionCorpus.load(CORPUS)
    todo = [i for i in range(len(c.ids)) if np.isnan(c.profiles[i]).any()]
    print(f"{len(c.ids)} entries, {len(todo)} un-authored")

    done = 0
    for i in todo:
        prof = perceive_question_response(c.texts[i])
        if prof is None:
            print(f"  {c.ids[i]}: authoring failed, stays inert")
            continue
        c.profiles[i] = prof
        done += 1
        if done % 25 == 0:
            c.save(CORPUS)
            print(f"  {done}/{len(todo)} authored (saved)")
    c.save(CORPUS)
    n_left = sum(1 for i in range(len(c.ids)) if np.isnan(c.profiles[i]).any())
    print(f"Done: {done} authored this run, {n_left} still inert")


if __name__ == "__main__":
    main()
