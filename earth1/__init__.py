"""Earth-1 — the living civilization engine.

THE CANONICAL WORLD IS `earth1.alive.World`, advanced by
`earth1.alive.live_one_day`. That is the only Earth.

Until 0.5a this file imported the retired opinion engine at package
level — so every `import earth1` executed `engine.py` and its family
(forces, diffusion, population, llm_gateway), privileging the dead
substrate as the package default even though ZERO code consumed the
re-exports. Importing the package now imports nothing: subsystems are
reached explicitly (`from earth1.alive import ...`), and the legacy
family is quarantined — it may explain history, it may not define
present Earth (see earth1/legacy_gate.py and the release gate's
one-production-earth invariant).
"""
