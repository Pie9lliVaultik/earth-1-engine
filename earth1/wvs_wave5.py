"""WVS Wave 5 (2005-2009) aggregates + fieldwork-year alignment (A6).

TRAINING ERA for the A6 secular leg: betas are fit on W5->W6 observed
deltas ONLY, then frozen before any W6->W7 scoring. This module was
authored AFTER the predictive-value spec freeze (frozen/spec.json
records the pre-W5 state of wvs_paired.py) so the experiment design
cannot have been shaped by these numbers.

PROVENANCE AND HONESTY: values are compiled from published WVS Wave 5
aggregate findings (Inglehart et al.; WVS online analysis tool),
matching the per-question codings declared in wvs_paired.py. Same
caveat as the W6/W7 data in wvs_paired.py, stated more strongly:
these are best-effort ESTIMATES of the published aggregates and MUST
be verified against the official database at worldvaluessurvey.org
before any result built on them is published externally. Countries
listed are those actually fielded in W5 that overlap the W6->W7 set
(26 of 37); W5 never fielded PK NG ZW LB TN MA KZ KG PH SG EC.

Fieldwork years: per-country survey years for rate normalization
(A6.1: drift = beta_q . D_rate with D_rate = D / years_i * 7.0).
Approximate where the wave spanned multiple years; verify with the
official documentation alongside the aggregates.
"""
from __future__ import annotations

W5_YEARS = {
    "US": 2006, "DE": 2006, "AU": 2005, "JP": 2005, "KR": 2005,
    "BR": 2006, "MX": 2005, "AR": 2006, "CL": 2006, "CO": 2005,
    "PE": 2006, "IN": 2006, "EG": 2008, "JO": 2007, "IQ": 2006,
    "TR": 2007, "RU": 2006, "UA": 2006, "RO": 2005, "TH": 2007,
    "MY": 2006, "CY": 2006, "NZ": 2004, "NL": 2006, "GH": 2007,
    "HK": 2005,
}

W6_YEARS = {
    "US": 2011, "DE": 2013, "AU": 2012, "JP": 2010, "KR": 2010,
    "BR": 2014, "MX": 2012, "AR": 2013, "CL": 2012, "CO": 2012,
    "PE": 2012, "IN": 2012, "PK": 2012, "NG": 2012, "GH": 2012,
    "ZW": 2012, "EG": 2013, "JO": 2014, "IQ": 2013, "LB": 2013,
    "TN": 2013, "MA": 2011, "TR": 2012, "RU": 2011, "UA": 2011,
    "RO": 2012, "KZ": 2011, "KG": 2011, "PH": 2012, "TH": 2013,
    "MY": 2012, "SG": 2012, "NZ": 2011, "NL": 2012, "CY": 2011,
    "EC": 2013, "HK": 2013,
}

W7_YEARS = {
    "US": 2017, "DE": 2017, "AU": 2018, "JP": 2019, "KR": 2018,
    "BR": 2018, "MX": 2018, "AR": 2017, "CL": 2018, "CO": 2018,
    "PE": 2018, "IN": 2022, "PK": 2018, "NG": 2017, "GH": 2021,
    "ZW": 2020, "EG": 2018, "JO": 2018, "IQ": 2018, "LB": 2018,
    "TN": 2019, "MA": 2021, "TR": 2018, "RU": 2017, "UA": 2020,
    "RO": 2018, "KZ": 2018, "KG": 2020, "PH": 2019, "TH": 2018,
    "MY": 2018, "SG": 2020, "NZ": 2019, "NL": 2022, "CY": 2019,
    "EC": 2018, "HK": 2018,
}

# question_id -> {country: proportion} on the SAME coding as wvs_paired
WAVE5 = {
    "t_homosexuality": {  # V202, 6+/10 justifiable
        "US": 0.42, "DE": 0.58, "AU": 0.55, "JP": 0.38, "KR": 0.18,
        "BR": 0.30, "MX": 0.32, "AR": 0.44, "CL": 0.34, "CO": 0.20,
        "PE": 0.14, "IN": 0.10, "EG": 0.02, "JO": 0.03, "IQ": 0.03,
        "TR": 0.06, "RU": 0.08, "UA": 0.07, "RO": 0.08, "TH": 0.28,
        "MY": 0.05, "CY": 0.14, "NZ": 0.56, "NL": 0.72, "GH": 0.03,
        "HK": 0.30,
    },
    "t_abortion": {  # V203-ish, 6+/10 justifiable
        "US": 0.34, "DE": 0.38, "AU": 0.40, "JP": 0.34, "KR": 0.28,
        "BR": 0.14, "MX": 0.18, "AR": 0.26, "CL": 0.22, "CO": 0.13,
        "PE": 0.10, "IN": 0.16, "EG": 0.06, "JO": 0.10, "TR": 0.18,
        "RU": 0.36, "UA": 0.32, "RO": 0.24, "TH": 0.32, "NZ": 0.44,
        "NL": 0.48, "GH": 0.06, "HK": 0.28,
    },
    "t_divorce": {  # 6+/10 justifiable
        "US": 0.46, "DE": 0.54, "AU": 0.52, "JP": 0.42, "KR": 0.30,
        "BR": 0.34, "MX": 0.34, "AR": 0.46, "CL": 0.38, "CO": 0.28,
        "PE": 0.22, "IN": 0.18, "EG": 0.12, "JO": 0.16, "IQ": 0.14,
        "TR": 0.20, "RU": 0.40, "UA": 0.38, "RO": 0.30, "TH": 0.36,
        "MY": 0.14, "CY": 0.30, "NZ": 0.54, "NL": 0.62, "GH": 0.10,
        "HK": 0.38,
    },
    "t_religion": {  # very/rather important
        "US": 0.70, "DE": 0.38, "AU": 0.44, "JP": 0.22, "KR": 0.48,
        "BR": 0.88, "MX": 0.82, "AR": 0.66, "CL": 0.70, "CO": 0.86,
        "PE": 0.84, "IN": 0.90, "EG": 0.98, "JO": 0.98, "IQ": 0.98,
        "TR": 0.92, "RU": 0.48, "UA": 0.56, "RO": 0.84, "TH": 0.90,
        "MY": 0.96, "CY": 0.78, "NZ": 0.40, "NL": 0.34, "GH": 0.98,
        "HK": 0.38,
    },
    "t_trust": {  # most people can be trusted
        "US": 0.39, "DE": 0.34, "AU": 0.46, "JP": 0.39, "KR": 0.28,
        "BR": 0.09, "MX": 0.16, "AR": 0.17, "CL": 0.13, "CO": 0.14,
        "PE": 0.06, "IN": 0.23, "EG": 0.19, "JO": 0.31, "IQ": 0.41,
        "TR": 0.05, "RU": 0.27, "UA": 0.28, "RO": 0.20, "TH": 0.41,
        "MY": 0.09, "CY": 0.10, "NZ": 0.51, "NL": 0.45, "GH": 0.09,
        "HK": 0.41,
    },
    "t_democracy": {  # very/fairly good
        "US": 0.86, "DE": 0.95, "AU": 0.90, "JP": 0.88, "KR": 0.84,
        "BR": 0.82, "MX": 0.78, "AR": 0.90, "CL": 0.86, "CO": 0.84,
        "PE": 0.80, "IN": 0.92, "EG": 0.98, "JO": 0.90, "IQ": 0.88,
        "TR": 0.90, "RU": 0.68, "UA": 0.80, "RO": 0.84, "TH": 0.92,
        "MY": 0.90, "CY": 0.94, "NZ": 0.92, "NL": 0.94, "GH": 0.94,
        "HK": 0.84,
    },
    "t_army_rule": {  # very/fairly good
        "US": 0.08, "DE": 0.04, "AU": 0.08, "JP": 0.04, "KR": 0.10,
        "BR": 0.32, "MX": 0.28, "AR": 0.12, "CL": 0.16, "CO": 0.26,
        "PE": 0.24, "IN": 0.28, "EG": 0.20, "JO": 0.28, "IQ": 0.30,
        "TR": 0.22, "RU": 0.18, "UA": 0.16, "RO": 0.22, "TH": 0.28,
        "MY": 0.28, "CY": 0.10, "NZ": 0.06, "NL": 0.04, "GH": 0.18,
        "HK": 0.14,
    },
    "t_life_sat": {  # 7+/10 satisfied
        "US": 0.66, "DE": 0.58, "AU": 0.70, "JP": 0.52, "KR": 0.46,
        "BR": 0.68, "MX": 0.76, "AR": 0.68, "CL": 0.62, "CO": 0.78,
        "PE": 0.50, "IN": 0.48, "EG": 0.42, "JO": 0.54, "IQ": 0.38,
        "TR": 0.56, "RU": 0.40, "UA": 0.38, "RO": 0.48, "TH": 0.68,
        "MY": 0.62, "CY": 0.64, "NZ": 0.74, "NL": 0.78, "GH": 0.48,
        "HK": 0.56,
    },
    "t_men_leaders": {  # agree/strongly agree
        "US": 0.22, "DE": 0.18, "AU": 0.20, "JP": 0.30, "KR": 0.48,
        "BR": 0.28, "MX": 0.28, "AR": 0.28, "CL": 0.30, "CO": 0.32,
        "PE": 0.34, "IN": 0.60, "EG": 0.84, "JO": 0.82, "IQ": 0.82,
        "TR": 0.58, "RU": 0.52, "UA": 0.48, "RO": 0.48, "TH": 0.48,
        "MY": 0.60, "CY": 0.44, "NZ": 0.16, "NL": 0.14, "GH": 0.64,
        "HK": 0.44,
    },
    "t_pride": {  # very proud
        "US": 0.72, "DE": 0.30, "AU": 0.70, "JP": 0.24, "KR": 0.40,
        "BR": 0.64, "MX": 0.78, "AR": 0.68, "CL": 0.72, "CO": 0.84,
        "PE": 0.70, "IN": 0.74, "EG": 0.90, "JO": 0.84, "IQ": 0.70,
        "TR": 0.78, "RU": 0.48, "UA": 0.42, "RO": 0.48, "TH": 0.86,
        "MY": 0.74, "CY": 0.60, "NZ": 0.70, "NL": 0.30, "GH": 0.86,
        "HK": 0.28,
    },
    "t_two_parent": {  # child needs both parents, agree
        "US": 0.62, "DE": 0.82, "AU": 0.60, "JP": 0.92, "KR": 0.90,
        "BR": 0.78, "MX": 0.82, "AR": 0.80, "CL": 0.78, "CO": 0.80,
        "PE": 0.84, "IN": 0.94, "EG": 0.98, "JO": 0.96, "IQ": 0.96,
        "TR": 0.94, "RU": 0.88, "UA": 0.90, "RO": 0.92, "TH": 0.94,
        "MY": 0.94, "CY": 0.94, "NZ": 0.58, "NL": 0.62, "GH": 0.92,
        "HK": 0.90,
    },
    "t_tech_good": {  # science/tech makes life better
        "US": 0.72, "DE": 0.68, "AU": 0.74, "JP": 0.70, "KR": 0.78,
        "BR": 0.78, "MX": 0.76, "AR": 0.70, "CL": 0.74, "CO": 0.76,
        "PE": 0.74, "IN": 0.84, "EG": 0.80, "JO": 0.78, "IQ": 0.74,
        "TR": 0.74, "RU": 0.70, "UA": 0.72, "RO": 0.76, "TH": 0.82,
        "MY": 0.80, "CY": 0.70, "NZ": 0.74, "NL": 0.70, "GH": 0.84,
        "HK": 0.74,
    },
    "t_death_penalty": {  # 6+/10 justifiable
        "US": 0.48, "DE": 0.28, "AU": 0.44, "JP": 0.52, "KR": 0.44,
        "BR": 0.38, "MX": 0.34, "AR": 0.30, "CL": 0.34, "CO": 0.30,
        "PE": 0.36, "IN": 0.40, "EG": 0.48, "JO": 0.52, "IQ": 0.50,
        "TR": 0.34, "RU": 0.44, "UA": 0.40, "RO": 0.36, "TH": 0.56,
        "MY": 0.48, "CY": 0.36, "NZ": 0.42, "NL": 0.30, "GH": 0.40,
        "HK": 0.52,
    },
    "t_environment": {  # environment priority over growth
        "US": 0.54, "DE": 0.62, "AU": 0.60, "JP": 0.50, "KR": 0.48,
        "BR": 0.62, "MX": 0.58, "AR": 0.60, "CL": 0.58, "CO": 0.68,
        "PE": 0.60, "IN": 0.52, "EG": 0.60, "JO": 0.54, "IQ": 0.42,
        "TR": 0.54, "RU": 0.44, "UA": 0.40, "RO": 0.48, "TH": 0.64,
        "MY": 0.62, "CY": 0.66, "NZ": 0.62, "NL": 0.60, "GH": 0.56,
        "HK": 0.58,
    },
    "t_hard_work": {  # hard work brings success, 6+/10
        "US": 0.68, "DE": 0.56, "AU": 0.62, "JP": 0.48, "KR": 0.62,
        "BR": 0.70, "MX": 0.66, "AR": 0.52, "CL": 0.60, "CO": 0.70,
        "PE": 0.64, "IN": 0.70, "EG": 0.74, "JO": 0.70, "IQ": 0.62,
        "TR": 0.62, "RU": 0.48, "UA": 0.46, "RO": 0.54, "TH": 0.74,
        "MY": 0.70, "CY": 0.58, "NZ": 0.64, "NL": 0.52, "GH": 0.82,
        "HK": 0.66,
    },
}
