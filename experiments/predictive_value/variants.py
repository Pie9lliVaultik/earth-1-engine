"""Variant table for the predictive-value grid (EXPERIMENT_PLAN.md §6).

Each variant is a tick_kwargs dict — data, not code paths. B disables
every social/emergent mechanism; C is production defaults; C-m are
one-at-a-time ablations from C. No parameter values change between
variants except what disabling logically requires.
"""

VARIANTS = {
    "B_individual": {
        "enable_feedback": False, "enable_coupling": False,
        "enable_thresholds": False, "enable_rewire": False,
        "enable_event_generation": False, "diffusion_layers": 0,
    },
    "C_full": {},
    "C_no_diffusion": {"diffusion_layers": 0},
    "C_no_feedback": {"enable_feedback": False},
    "C_no_rewire": {"enable_rewire": False},
    "C_no_coupling": {"enable_coupling": False},
    "C_no_thresholds": {"enable_thresholds": False},
    "C_no_eventgen": {"enable_event_generation": False},
}
