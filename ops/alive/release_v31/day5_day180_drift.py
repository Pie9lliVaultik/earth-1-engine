#!/usr/bin/env python3
"""Audit v31, items 4+13: equilibration-transient deltas, freeze-0.9 physics.

Inputs are transcribed VERBATIM from the committed record:
  ops/alive/SCALE_INVARIANCE_100M.md lines 131-141 (4M x 180d table,
  freeze-0.9, configstamp-verified) and line 140 (200k board @180d row).
No engine code is imported; this is arithmetic on published board numbers.
"""

# day: (median $/day, poverty $8.30 share, poverty $3.00 share, CDR/yr, mean age at death)
FREEZE09_4M = {
    5:   (8.61, 0.4874, 0.1864, 0.00772, 68.40),
    180: (9.52, 0.4529, 0.1630, 0.00738, 68.29),
}
BOARD_200K_180D = (9.605, 0.4588, 0.1680, 0.00727, 68.99)

# Legacy-physics day-5 census (same file, lines 46-59; config-correction banner lines 3-23)
LEGACY_DAY5 = {"median": 3.23, "pov830": 0.946}

d5, d180 = FREEZE09_4M[5], FREEZE09_4M[180]
print("freeze-0.9 4M equilibration transient (day 5 -> day 180):")
print(f"  median  : {d5[0]:.2f} -> {d180[0]:.2f}  (delta +${d180[0]-d5[0]:.2f}, {100*(d180[0]-d5[0])/d5[0]:+.1f}%)")
print(f"  pov$8.30: {100*d5[1]:.2f}% -> {100*d180[1]:.2f}%  (delta {100*(d180[1]-d5[1]):+.2f}pp)")
print(f"  pov$3.00: {100*d5[2]:.2f}% -> {100*d180[2]:.2f}%  (delta {100*(d180[2]-d5[2]):+.2f}pp)")
print(f"  CDR/yr  : {d5[3]:.5f} -> {d180[3]:.5f}  (delta {100*(d180[3]-d5[3])/d5[3]:+.1f}%)")
print(f"  ageAtDeath: {d5[4]:.2f} -> {d180[4]:.2f}  (delta {d180[4]-d5[4]:+.2f} yr)")

print("\nlegacy-physics day-5 census vs freeze-0.9 day-5 (same world-day, different flags):")
print(f"  median  : {LEGACY_DAY5['median']:.2f} vs {d5[0]:.2f}")
print(f"  pov$8.30: {100*LEGACY_DAY5['pov830']:.1f}% vs {100*d5[1]:.2f}%")

print("\nday-180 4M vs 200k board @180d:")
print(f"  median gap  : {100*(d180[0]-BOARD_200K_180D[0])/BOARD_200K_180D[0]:+.1f}%")
print(f"  pov$8.30 gap: {100*(d180[1]-BOARD_200K_180D[1]):+.2f}pp")
