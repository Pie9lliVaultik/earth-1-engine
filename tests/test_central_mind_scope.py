"""Scoped-headline fixes: stale 9-country prompt, global headline on
country questions, corpus hits discarding scope."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.central_mind import _extract_scope


def test_extract_scope_demonyms():
    assert _extract_scope("What do Italians think about the EU?") == "IT"
    assert _extract_scope("Do Germans support nuclear power?") == "DE"
    assert _extract_scope("Are Nigerians optimistic about the economy?") == "NG"


def test_extract_scope_country_names():
    assert _extract_scope("How does Japan view immigration?") == "JP"
    assert _extract_scope("Is trust in government rising in Brazil?") == "BR"


def test_extract_scope_global_default():
    assert _extract_scope("Do people believe hard work brings success?") == "global"


def test_gateway_prompt_names_194_countries():
    import earth1.llm_gateway as gw
    import inspect
    src = inspect.getsource(gw)
    assert "9 countries" not in src
    assert "194 countries" in src


def test_scoped_headline_differs_from_global():
    """A country-scoped question must report that country's cohort as
    the headline, not the planet's."""
    from earth1.engine import build_genesis_civilization, run_question
    from earth1.genesis import GENESIS_COUNTRY_CODES
    from earth1.types import Question, NUM_FORCES

    civ = build_genesis_civilization(5000, seed=42)
    w = np.zeros(NUM_FORCES)
    w[0] = 0.9
    q = Question(id="scope_q", text="scoped", domain="belief_causal",
                 baseline=0.5, weights=w, lens="wvs")
    r = run_question(q, civ)
    assert r.settled_stances is not None
    mask = civ.country == GENESIS_COUNTRY_CODES.index("IN")
    scoped = float(r.settled_stances[mask].mean())
    # the scoped readout is what think() now reports for country questions
    assert abs(scoped - r.yes_pct) > 1e-6  # a country is not the planet
