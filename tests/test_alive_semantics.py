"""Phase 0.0a semantic invariants — time passes for everyone.

The founding defect (BIBLE v4.1 R17, triple-confirmed): `live_one_day`
never advanced `civ.age`, so max|Δage| = 0.0 over any horizon and every
age-dependent hazard ran on a frozen day-0 age structure — through the
365-day backtests, the 750-day archived world, and all 284 days of
Epoch 0.

Scope guard (founder Amendment B): `advance_age` maintains chronological
`age` and `age_bucket` ONLY. The tests below assert the invariant AND
the exclusions, so smuggling trait drift or an EXPERIENCE overwrite into
the clock fails CI as loudly as freezing the clock again would.
"""
import copy

import numpy as np
import pytest

from earth1.alive import live_one_day
from earth1.generational import _AGE_SPAN, advance_age
from earth1.types import Force

YEAR = 1.0 / _AGE_SPAN          # one year, in normalized age units


# ── the invariant: 365 days = one year, for every survivor ──────────

def test_one_year_ages_everyone_by_one_year(tiny_world, rng):
    """The 0.0a acceptance invariant, on the full live loop."""
    w = tiny_world
    before_alive = w.health.alive.copy()
    age0 = w.civ.age.copy()

    live_one_day(w, rng, dt_days=365.0)

    surv = before_alive & w.health.alive
    # exclude anyone clipped at the 90-year ceiling and slots recycled
    # by _be_born during the tick (age reset to 0)
    grew = surv & (age0 < 1.0 - YEAR) & (w.civ.age > age0)
    assert grew.sum() > 0.9 * surv.sum()
    np.testing.assert_allclose(w.civ.age[grew] - age0[grew], YEAR,
                               atol=1e-12)


def test_the_frozen_age_defect_is_detectable(tiny_world, rng):
    """The control that fires on the original bug: any nonzero advance.

    Before 0.0a this asserted-on quantity was measured at exactly 0.0
    over 30 days on the live path. If the wiring is ever lost again,
    this fails immediately.
    """
    w = tiny_world
    age0 = w.civ.age.copy()
    live_one_day(w, rng)
    assert float(np.abs(w.civ.age - age0).max()) > 0.0, \
        "age is frozen again — the R17 defect has returned"


def test_age_buckets_track_age(tiny_world):
    w = tiny_world
    advance_age(w.civ, dt_days=365.0 * 12)     # everyone +12 years
    years = 18.0 + w.civ.age * 72.0
    np.testing.assert_array_equal(
        w.civ.age_bucket, np.digitize(years, [30, 45, 60, 75]))


def test_age_clips_at_ceiling():
    """Nobody ages past the 90-year encoding ceiling."""
    from earth1.alive import birth_world
    w = birth_world(2_000, 7)
    w.civ.age[:] = 0.999
    advance_age(w.civ, dt_days=365.0 * 5)
    assert float(w.civ.age.max()) <= 1.0


def test_daily_increments_compose_to_a_year(tiny_world):
    """365 x 1-day == 1 x 365-day, to numerical precision."""
    a = copy.deepcopy(tiny_world.civ)
    b = copy.deepcopy(tiny_world.civ)
    for _ in range(365):
        advance_age(a, dt_days=1.0)
    advance_age(b, dt_days=365.0)
    np.testing.assert_allclose(a.age, b.age, atol=1e-9)


# ── the Amendment-B exclusions: the clock and ONLY the clock ────────

def test_advance_age_touches_nothing_but_the_clock(tiny_world):
    """Trait drift, EXPERIENCE overwrite, or any force change smuggled
    into the clock is a silent model change — exactly what the founder
    ruling forbids. Byte-compare everything else.
    """
    civ = tiny_world.civ
    # plant a sentinel: EXPERIENCE deliberately decoupled from age
    civ.forces[:, int(Force.EXPERIENCE)] = 0.31337
    frozen = {name: getattr(civ, name).copy()
              for name in ("forces", "alpha", "openness", "risk_appetite",
                           "desire_intensity", "conscientiousness",
                           "agreeableness", "extraversion", "neuroticism",
                           "doubt", "empathy", "means")}

    advance_age(civ, dt_days=365.0 * 40)       # forty years of clock

    for name, before in frozen.items():
        np.testing.assert_array_equal(
            getattr(civ, name), before,
            err_msg=f"advance_age modified civ.{name} — the clock must "
                    f"touch age and age_bucket only")


def test_experience_is_not_reasserted_by_the_live_loop(tiny_world, rng):
    """EXPERIENCE must remain a dynamical channel, not an age mirror.

    Six live modules legitimately move it, so it will not stay at the
    sentinel — the assertion is that it does not become EQUAL to age,
    which is what the forbidden generational identity-map would do.
    """
    w = tiny_world
    w.civ.forces[:, int(Force.EXPERIENCE)] = 0.777
    live_one_day(w, rng)
    exp = w.civ.forces[:, int(Force.EXPERIENCE)]
    assert not np.allclose(exp, w.civ.age, atol=1e-6), \
        "EXPERIENCE was overwritten from age — lived history erased"


# ── downstream visibility: the hazards read the new age ─────────────

def test_age_dependent_hazards_see_advancing_age(tiny_world):
    """The point of unfreezing: health's age input actually moves."""
    w = tiny_world
    years_before = 18.0 + w.civ.age * 72.0
    advance_age(w.civ, dt_days=365.0 * 10)
    years_after = 18.0 + w.civ.age * 72.0
    moved = years_after - years_before
    grew = w.civ.age < 1.0
    assert np.all(moved[grew] > 9.99), \
        "health/mobility/weather read 18 + age*72 — it must advance"
