# DATA LICENCE AUDIT — Track C (THREE_TRACK_PREREG_v1 C3)
2026-08-26. Method: 6 sources × (terms research + independent adversarial
cross-check against LIVE official pages), ambiguity resolved restrictive.
Question audited: may Earthling Labs use the microdata as calibration/
training input to a commercially deployed model (data never
redistributed), and for internal commercial R&D?

## Verdicts
| source | commercial use | model training | redistribution | path to commercial use |
|---|---|---|---|---|
| **GSS** (NORC public-use) | PERMITTED (conditional) | NOT_ADDRESSED (no prohibition) | permission required | Already usable: no clickwrap, no commercial bar; obligations = Davern et al. citation + responsible use + never re-identify respondents. Download DIRECT from gss.norc.org (NOT via ICPSR/Roper, which add their own terms). Recommended: short confirmation email to gss@norc.org before commercial training. |
| **ANES** (public release) | PERMITTED_CONDITIONAL | NOT_ADDRESSED | permitted | Usable now for "research or statistical purposes" — model fitting qualifies as statistical use on the conservative reading. Download DIRECT from electionstudies.org (NOT via ICPSR). Never use Restricted-Use files commercially; model must never identify respondents. |
| **ESS** (ESS ERIC) | PERMISSION_REQUIRED | PERMISSION_REQUIRED | permission required | Data is CC BY-NC-SA 4.0 (NonCommercial). Defined path exists: case-by-case commercial licence under ESS ERIC Statutes Art. 23 — email ess@city.ac.uk, cc essdatasupport@sikt.no. |
| **WVS** (WVSA) | PROHIBITED under standard terms | PERMISSION_REQUIRED | prohibited | Click-through grants use "for non-profit purposes" ONLY; no commercial option exists on the registration form. Ad-hoc written permission from WVSA required: wvsa.secretariat@gmail.com + jdiezmed@jdsurvey.net (JD Systems, Madrid). Do not select "Academic research project" on the form for this project. |
| **EVS** (GESIS ZA7500/Trend) | PROHIBITED | PROHIBITED | prohibited | GESIS Terms (04.02.2026): commercial use prohibited (Sec. 4) AND "use of AI systems for processing the database" prohibited outside exclusively scientific purposes. Worst estate; no published commercial path. |
| **IPUMS-International** | PROHIBITED (strict) | PROHIBITED | prohibited | "Use in the pursuit of any commercial or income-generating venture" strictly prohibited; attaches to USE, not redistribution. Do NOT register. HOUSEHOLD/FINE_GEOGRAPHY joints stay BLOCKED_ON_DATA; the unblock is NOT IPUMS — it is public NSO tables or a negotiated/commercial census product. |

## Consequences for the programme
1. **Latent-z training estate**: commercially safe today = GSS + ANES —
   both US-only. The cross-country hierarchical-DIF design cannot
   legally train on WVS/EVS/ESS microdata for a commercial model until
   permissions land. Options: (a) founder secures WVS + ESS permissions
   (emails above; EVS has no path); (b) latent-z pilot proceeds as
   internal *scientific* validation only, with a registered firewall:
   no WVS/EVS/ESS-fitted parameter ships in a commercial artifact
   until its source is cleared; (c) US-only pilot on GSS+ANES first.
2. **Retroactive exposure (flag for counsel, not a conclusion)**: the
   deployed H layer (earth1/calibration.py) is fitted on WVS-7-derived
   aggregates. WVS terms distinguish the data files from published
   "results"; whether our aggregate inputs count as files-use or
   results-use needs counsel + the WVSA permission conversation.
3. **GSS reversal of fortune**: GSS is PARTIALLY_CONSUMED scientifically
   (R1: 79 vars) but is the MOST permissive licence in the estate. ESS
   is scientifically clean but NC-licensed. ANES is clean AND
   permissive — the single best untouched estate on both axes.
4. Registry licence fields updated (data/data_roles.json). Founder
   actions: two emails (WVSA, ESS ERIC), one optional confirmation
   (NORC), counsel review of item 2. Nothing here is sent by Claude.

Full per-source evidence with verbatim quoted clauses and cross-check
transcripts: workflow wf_47f3ea9d-cb1 journal (12 agents, 0 errors).
