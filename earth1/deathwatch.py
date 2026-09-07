"""DEATHWATCH — the one correct way to observe deaths in a live world.

This exists because the naive method is wrong and keeps being rewritten.

THE DEFECT (measured, 2026-08-27, ops ledger): a dead agent's slot is
REBORN in the same tick, so the obvious mask

    died = prev_alive & ~world.health.alive        # WRONG

sees an alive slot on both sides and misses the death. Measured capture
was ~30 of ~780 real deaths at 200k — about 4%. Every age-at-death
figure taken that way carried +/-3.5yr of noise while claiming +/-1,
and a 100M run on 2026-09-02 reported mean age at death = 0 from zero
scored deaths.

THE FIX: detect on person_id TURNOVER as well as the alive flag, and
read ages from the PRE-tick snapshot (the post-tick age belongs to the
newborn occupying the slot). cause_of_death read post-tick is still the
dead occupant's — rebirth does not rewrite it before the next death.

Usage:
    watch = DeathWatch(w)
    for _ in range(days):
        live_one_day(w, rng)
        watch.observe(w)
    watch.mean_age_at_death, watch.ages, watch.by_cause
"""
import numpy as np


class DeathWatch:
    """Observe-only. Holds pre-tick snapshots; never mutates the world."""

    def __init__(self, world):
        self.ages = []
        self.by_cause = {}
        self._snap(world)

    def _snap(self, w):
        self._alive = w.health.alive.copy()
        self._pid = w.civ.person_id.copy()
        self._age = w.civ.age.copy()

    def observe(self, w) -> int:
        """Call once immediately after each live_one_day. Returns the
        number of deaths captured this tick."""
        died = self._alive & (~w.health.alive
                              | (w.civ.person_id != self._pid))
        n = int(died.sum())
        if n:
            ages = 18.0 + self._age[died] * 72.0
            self.ages.extend(ages.tolist())
            cod = getattr(w.health, "cause_of_death", None)
            if cod is not None:
                for a_, c_ in zip(ages.tolist(), cod[died].tolist()):
                    self.by_cause.setdefault(int(c_), []).append(a_)
        self._snap(w)
        return n

    @property
    def n(self) -> int:
        return len(self.ages)

    @property
    def mean_age_at_death(self):
        return float(np.mean(self.ages)) if self.ages else None

    def summary(self) -> dict:
        return {"n_deaths_captured": self.n,
                "mean_age_at_death": (round(self.mean_age_at_death, 2)
                                      if self.ages else None),
                "method": "person_id turnover + pre-tick ages "
                          "(earth1.deathwatch — the naive alive-mask "
                          "captures ~4% of deaths)"}
