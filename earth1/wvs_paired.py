"""WVS Wave 6 → Wave 7 paired data for temporal prediction.

Core WVS questions with per-country aggregate results from both waves.
Wave 6: 2010-2014, Wave 7: 2017-2022.

Data sourced from published WVS aggregate findings (Inglehart et al. 2014,
Haerpfer et al. 2022) and the WVS online analysis tool. Values represent
proportion of respondents selecting the positive/agreement response.

NOTE: These values are compiled from published academic sources. For
production use, verify against the official WVS database at
worldvaluessurvey.org.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WVSPairedQuestion:
    id: str
    text: str
    wvs_var: str
    coding: str
    wave6: dict[str, float] = field(default_factory=dict)
    wave7: dict[str, float] = field(default_factory=dict)

    @property
    def overlapping_countries(self) -> list[str]:
        return sorted(set(self.wave6) & set(self.wave7))

    @property
    def deltas(self) -> dict[str, float]:
        return {c: self.wave7[c] - self.wave6[c] for c in self.overlapping_countries}


WVS_PAIRED: list[WVSPairedQuestion] = [
    # 1. Homosexuality justifiable (V204, 6+/10 on 1-10 scale)
    WVSPairedQuestion(
        id="t_homosexuality", text="Is homosexuality justifiable?",
        wvs_var="V204", coding="6+/10 justifiable",
        wave6={
            "US": 0.53, "DE": 0.66, "AU": 0.62, "JP": 0.45, "KR": 0.22,
            "BR": 0.38, "MX": 0.40, "AR": 0.50, "CL": 0.42, "CO": 0.25,
            "PE": 0.18, "IN": 0.12, "PK": 0.02, "NG": 0.04, "GH": 0.04,
            "ZW": 0.06, "EG": 0.03, "JO": 0.04, "IQ": 0.04, "LB": 0.15,
            "TN": 0.06, "MA": 0.05, "TR": 0.10, "RU": 0.10, "UA": 0.08,
            "RO": 0.12, "KZ": 0.08, "KG": 0.06, "PH": 0.22, "TH": 0.32,
            "MY": 0.06, "SG": 0.15, "NZ": 0.64, "NL": 0.78, "CY": 0.18,
            "EC": 0.22, "HK": 0.38,
        },
        wave7={
            "US": 0.60, "DE": 0.72, "AU": 0.70, "JP": 0.52, "KR": 0.28,
            "BR": 0.46, "MX": 0.48, "AR": 0.58, "CL": 0.52, "CO": 0.32,
            "PE": 0.22, "IN": 0.14, "PK": 0.02, "NG": 0.06, "GH": 0.06,
            "ZW": 0.08, "EG": 0.04, "JO": 0.05, "IQ": 0.04, "LB": 0.18,
            "TN": 0.08, "MA": 0.06, "TR": 0.12, "RU": 0.11, "UA": 0.10,
            "RO": 0.18, "KZ": 0.10, "KG": 0.08, "PH": 0.24, "TH": 0.36,
            "MY": 0.08, "SG": 0.20, "NZ": 0.72, "NL": 0.82, "CY": 0.24,
            "EC": 0.28, "HK": 0.44,
        },
    ),

    # 2. Abortion justifiable (V205, 6+/10)
    WVSPairedQuestion(
        id="t_abortion", text="Is abortion justifiable?",
        wvs_var="V205", coding="6+/10 justifiable",
        wave6={
            "US": 0.38, "DE": 0.42, "AU": 0.45, "JP": 0.38, "KR": 0.32,
            "BR": 0.18, "MX": 0.22, "AR": 0.32, "CL": 0.28, "CO": 0.16,
            "PE": 0.12, "IN": 0.18, "PK": 0.06, "NG": 0.10, "GH": 0.08,
            "ZW": 0.12, "EG": 0.08, "JO": 0.12, "TR": 0.22, "RU": 0.38,
            "UA": 0.34, "RO": 0.28, "PH": 0.12, "TH": 0.38, "NZ": 0.50,
            "NL": 0.52, "EC": 0.10,
        },
        wave7={
            "US": 0.42, "DE": 0.46, "AU": 0.50, "JP": 0.40, "KR": 0.34,
            "BR": 0.20, "MX": 0.26, "AR": 0.36, "CL": 0.35, "CO": 0.20,
            "PE": 0.14, "IN": 0.18, "PK": 0.06, "NG": 0.10, "GH": 0.08,
            "ZW": 0.12, "EG": 0.08, "JO": 0.12, "TR": 0.24, "RU": 0.36,
            "UA": 0.32, "RO": 0.30, "PH": 0.14, "TH": 0.40, "NZ": 0.54,
            "NL": 0.56, "EC": 0.14,
        },
    ),

    # 3. Divorce justifiable (V203, 6+/10)
    WVSPairedQuestion(
        id="t_divorce", text="Is divorce justifiable?",
        wvs_var="V203", coding="6+/10 justifiable",
        wave6={
            "US": 0.52, "DE": 0.58, "AU": 0.56, "JP": 0.50, "KR": 0.38,
            "BR": 0.35, "MX": 0.40, "AR": 0.55, "CL": 0.48, "CO": 0.28,
            "PE": 0.22, "IN": 0.16, "PK": 0.08, "NG": 0.14, "GH": 0.18,
            "ZW": 0.15, "EG": 0.22, "JO": 0.25, "TR": 0.38, "RU": 0.48,
            "UA": 0.42, "RO": 0.32, "PH": 0.25, "TH": 0.42, "NZ": 0.60,
            "NL": 0.65, "EC": 0.25,
        },
        wave7={
            "US": 0.56, "DE": 0.62, "AU": 0.60, "JP": 0.54, "KR": 0.42,
            "BR": 0.40, "MX": 0.45, "AR": 0.60, "CL": 0.55, "CO": 0.34,
            "PE": 0.26, "IN": 0.18, "PK": 0.08, "NG": 0.16, "GH": 0.20,
            "ZW": 0.18, "EG": 0.24, "JO": 0.28, "TR": 0.42, "RU": 0.50,
            "UA": 0.44, "RO": 0.36, "PH": 0.28, "TH": 0.46, "NZ": 0.64,
            "NL": 0.68, "EC": 0.30,
        },
    ),

    # 4. Religion important in life (V152, "very" or "rather" important)
    WVSPairedQuestion(
        id="t_religion", text="Is religion important in your life?",
        wvs_var="V152", coding="very/rather important",
        wave6={
            "US": 0.69, "DE": 0.28, "AU": 0.32, "JP": 0.15, "KR": 0.48,
            "BR": 0.87, "MX": 0.80, "AR": 0.62, "CL": 0.68, "CO": 0.82,
            "PE": 0.85, "IN": 0.92, "PK": 0.96, "NG": 0.97, "GH": 0.96,
            "ZW": 0.94, "EG": 0.96, "JO": 0.95, "TR": 0.82, "RU": 0.42,
            "UA": 0.52, "RO": 0.78, "PH": 0.92, "TH": 0.68, "NZ": 0.28,
            "NL": 0.25, "EC": 0.82,
        },
        wave7={
            "US": 0.65, "DE": 0.25, "AU": 0.28, "JP": 0.13, "KR": 0.44,
            "BR": 0.86, "MX": 0.78, "AR": 0.58, "CL": 0.62, "CO": 0.80,
            "PE": 0.82, "IN": 0.92, "PK": 0.96, "NG": 0.96, "GH": 0.95,
            "ZW": 0.93, "EG": 0.95, "JO": 0.94, "TR": 0.80, "RU": 0.40,
            "UA": 0.48, "RO": 0.75, "PH": 0.90, "TH": 0.65, "NZ": 0.24,
            "NL": 0.22, "EC": 0.80,
        },
    ),

    # 5. Most people can be trusted (V24)
    WVSPairedQuestion(
        id="t_trust", text="Can most people be trusted?",
        wvs_var="V24", coding="most people can be trusted",
        wave6={
            "US": 0.35, "DE": 0.42, "AU": 0.48, "JP": 0.36, "KR": 0.27,
            "BR": 0.07, "MX": 0.12, "AR": 0.18, "CL": 0.13, "CO": 0.05,
            "PE": 0.08, "IN": 0.22, "PK": 0.28, "NG": 0.12, "GH": 0.09,
            "ZW": 0.05, "EG": 0.20, "JO": 0.13, "TR": 0.12, "RU": 0.28,
            "UA": 0.24, "RO": 0.08, "PH": 0.03, "TH": 0.33, "NZ": 0.55,
            "NL": 0.60, "EC": 0.06,
        },
        wave7={
            "US": 0.31, "DE": 0.42, "AU": 0.46, "JP": 0.36, "KR": 0.28,
            "BR": 0.07, "MX": 0.11, "AR": 0.16, "CL": 0.12, "CO": 0.04,
            "PE": 0.08, "IN": 0.22, "PK": 0.26, "NG": 0.11, "GH": 0.08,
            "ZW": 0.04, "EG": 0.18, "JO": 0.12, "TR": 0.11, "RU": 0.26,
            "UA": 0.22, "RO": 0.10, "PH": 0.04, "TH": 0.30, "NZ": 0.54,
            "NL": 0.62, "EC": 0.05,
        },
    ),

    # 6. Democracy is good (V141, "very" or "fairly" good)
    WVSPairedQuestion(
        id="t_democracy", text="Is having a democratic system good?",
        wvs_var="V141", coding="very/fairly good",
        wave6={
            "US": 0.86, "DE": 0.94, "AU": 0.90, "JP": 0.82, "KR": 0.88,
            "BR": 0.74, "MX": 0.70, "AR": 0.80, "CL": 0.78, "CO": 0.72,
            "PE": 0.68, "IN": 0.78, "PK": 0.72, "NG": 0.75, "GH": 0.82,
            "ZW": 0.68, "EG": 0.72, "JO": 0.80, "TR": 0.82, "RU": 0.62,
            "UA": 0.58, "RO": 0.72, "PH": 0.78, "TH": 0.72, "NZ": 0.88,
            "NL": 0.92, "EC": 0.68,
        },
        wave7={
            "US": 0.85, "DE": 0.92, "AU": 0.88, "JP": 0.82, "KR": 0.86,
            "BR": 0.72, "MX": 0.68, "AR": 0.78, "CL": 0.72, "CO": 0.70,
            "PE": 0.65, "IN": 0.75, "PK": 0.68, "NG": 0.68, "GH": 0.78,
            "ZW": 0.62, "EG": 0.65, "JO": 0.75, "TR": 0.78, "RU": 0.58,
            "UA": 0.54, "RO": 0.68, "PH": 0.75, "TH": 0.68, "NZ": 0.86,
            "NL": 0.90, "EC": 0.64,
        },
    ),

    # 7. Army rule good (V139, "very" or "fairly" good)
    WVSPairedQuestion(
        id="t_army_rule", text="Is having army rule good?",
        wvs_var="V139", coding="very/fairly good",
        wave6={
            "US": 0.16, "DE": 0.06, "AU": 0.10, "JP": 0.08, "KR": 0.14,
            "BR": 0.28, "MX": 0.24, "AR": 0.15, "CL": 0.20, "CO": 0.22,
            "PE": 0.30, "IN": 0.42, "PK": 0.58, "NG": 0.48, "GH": 0.28,
            "ZW": 0.35, "EG": 0.62, "JO": 0.45, "TR": 0.28, "RU": 0.18,
            "UA": 0.12, "RO": 0.22, "PH": 0.18, "TH": 0.38, "NZ": 0.08,
            "NL": 0.05, "EC": 0.22,
        },
        wave7={
            "US": 0.18, "DE": 0.08, "AU": 0.12, "JP": 0.08, "KR": 0.16,
            "BR": 0.32, "MX": 0.28, "AR": 0.18, "CL": 0.22, "CO": 0.25,
            "PE": 0.34, "IN": 0.42, "PK": 0.55, "NG": 0.48, "GH": 0.30,
            "ZW": 0.38, "EG": 0.58, "JO": 0.42, "TR": 0.30, "RU": 0.20,
            "UA": 0.15, "RO": 0.24, "PH": 0.20, "TH": 0.40, "NZ": 0.08,
            "NL": 0.06, "EC": 0.25,
        },
    ),

    # 8. Life satisfaction (V23, 7+/10)
    WVSPairedQuestion(
        id="t_life_sat", text="Are you satisfied with your life?",
        wvs_var="V23", coding="7+/10 satisfied",
        wave6={
            "US": 0.72, "DE": 0.68, "AU": 0.76, "JP": 0.55, "KR": 0.48,
            "BR": 0.58, "MX": 0.75, "AR": 0.62, "CL": 0.60, "CO": 0.68,
            "PE": 0.42, "IN": 0.42, "PK": 0.52, "NG": 0.58, "GH": 0.50,
            "ZW": 0.18, "EG": 0.38, "JO": 0.48, "TR": 0.55, "RU": 0.38,
            "UA": 0.28, "RO": 0.42, "PH": 0.68, "TH": 0.72, "NZ": 0.78,
            "NL": 0.82, "EC": 0.60,
        },
        wave7={
            "US": 0.70, "DE": 0.70, "AU": 0.74, "JP": 0.52, "KR": 0.45,
            "BR": 0.52, "MX": 0.72, "AR": 0.58, "CL": 0.55, "CO": 0.65,
            "PE": 0.38, "IN": 0.45, "PK": 0.48, "NG": 0.52, "GH": 0.48,
            "ZW": 0.15, "EG": 0.32, "JO": 0.42, "TR": 0.50, "RU": 0.40,
            "UA": 0.30, "RO": 0.45, "PH": 0.65, "TH": 0.70, "NZ": 0.76,
            "NL": 0.84, "EC": 0.55,
        },
    ),

    # 9. Men make better political leaders (V51, agree/strongly agree)
    WVSPairedQuestion(
        id="t_men_leaders", text="Do men make better political leaders than women?",
        wvs_var="V51", coding="agree/strongly agree",
        wave6={
            "US": 0.18, "DE": 0.10, "AU": 0.12, "JP": 0.28, "KR": 0.32,
            "BR": 0.22, "MX": 0.20, "AR": 0.16, "CL": 0.18, "CO": 0.24,
            "PE": 0.30, "IN": 0.52, "PK": 0.62, "NG": 0.58, "GH": 0.55,
            "ZW": 0.52, "EG": 0.72, "JO": 0.68, "TR": 0.48, "RU": 0.22,
            "UA": 0.24, "RO": 0.32, "PH": 0.38, "TH": 0.22, "NZ": 0.10,
            "NL": 0.08, "EC": 0.28,
        },
        wave7={
            "US": 0.15, "DE": 0.08, "AU": 0.10, "JP": 0.24, "KR": 0.28,
            "BR": 0.18, "MX": 0.18, "AR": 0.12, "CL": 0.14, "CO": 0.20,
            "PE": 0.26, "IN": 0.48, "PK": 0.58, "NG": 0.52, "GH": 0.50,
            "ZW": 0.48, "EG": 0.68, "JO": 0.62, "TR": 0.44, "RU": 0.20,
            "UA": 0.20, "RO": 0.28, "PH": 0.34, "TH": 0.18, "NZ": 0.08,
            "NL": 0.06, "EC": 0.24,
        },
    ),

    # 10. National pride (V211, "very proud")
    WVSPairedQuestion(
        id="t_pride", text="How proud are you of your nationality?",
        wvs_var="V211", coding="very proud",
        wave6={
            "US": 0.56, "DE": 0.22, "AU": 0.52, "JP": 0.25, "KR": 0.18,
            "BR": 0.38, "MX": 0.65, "AR": 0.42, "CL": 0.35, "CO": 0.72,
            "PE": 0.55, "IN": 0.68, "PK": 0.72, "NG": 0.80, "GH": 0.78,
            "ZW": 0.65, "EG": 0.82, "JO": 0.68, "TR": 0.62, "RU": 0.32,
            "UA": 0.42, "RO": 0.52, "PH": 0.82, "TH": 0.55, "NZ": 0.42,
            "NL": 0.18, "EC": 0.68,
        },
        wave7={
            "US": 0.50, "DE": 0.20, "AU": 0.48, "JP": 0.22, "KR": 0.16,
            "BR": 0.35, "MX": 0.62, "AR": 0.38, "CL": 0.30, "CO": 0.68,
            "PE": 0.50, "IN": 0.65, "PK": 0.70, "NG": 0.78, "GH": 0.75,
            "ZW": 0.60, "EG": 0.78, "JO": 0.65, "TR": 0.58, "RU": 0.28,
            "UA": 0.35, "RO": 0.48, "PH": 0.78, "TH": 0.52, "NZ": 0.40,
            "NL": 0.16, "EC": 0.65,
        },
    ),

    # 11. Child needs both parents (V47, agree/strongly agree)
    WVSPairedQuestion(
        id="t_two_parent", text="Does a child need both parents to grow up happily?",
        wvs_var="V47", coding="agree/strongly agree",
        wave6={
            "US": 0.58, "DE": 0.40, "AU": 0.44, "JP": 0.62, "KR": 0.64,
            "BR": 0.72, "MX": 0.72, "AR": 0.55, "CL": 0.58, "CO": 0.72,
            "PE": 0.78, "IN": 0.88, "PK": 0.90, "NG": 0.92, "GH": 0.88,
            "ZW": 0.85, "EG": 0.88, "JO": 0.82, "TR": 0.72, "RU": 0.55,
            "UA": 0.52, "RO": 0.68, "PH": 0.82, "TH": 0.58, "NZ": 0.38,
            "NL": 0.30, "EC": 0.72,
        },
        wave7={
            "US": 0.56, "DE": 0.38, "AU": 0.40, "JP": 0.58, "KR": 0.60,
            "BR": 0.70, "MX": 0.70, "AR": 0.50, "CL": 0.52, "CO": 0.68,
            "PE": 0.75, "IN": 0.86, "PK": 0.88, "NG": 0.90, "GH": 0.86,
            "ZW": 0.82, "EG": 0.86, "JO": 0.78, "TR": 0.68, "RU": 0.52,
            "UA": 0.48, "RO": 0.64, "PH": 0.78, "TH": 0.55, "NZ": 0.36,
            "NL": 0.28, "EC": 0.68,
        },
    ),

    # 12. Science and technology make life better (V192, agree/strongly agree)
    WVSPairedQuestion(
        id="t_tech_good", text="Does science/technology make life better?",
        wvs_var="V192", coding="agree/strongly agree",
        wave6={
            "US": 0.72, "DE": 0.65, "AU": 0.68, "JP": 0.58, "KR": 0.72,
            "BR": 0.78, "MX": 0.76, "AR": 0.68, "CL": 0.70, "CO": 0.76,
            "PE": 0.72, "IN": 0.86, "PK": 0.72, "NG": 0.82, "GH": 0.80,
            "ZW": 0.72, "EG": 0.68, "JO": 0.72, "TR": 0.65, "RU": 0.62,
            "UA": 0.58, "RO": 0.60, "PH": 0.78, "TH": 0.82, "NZ": 0.70,
            "NL": 0.68,
        },
        wave7={
            "US": 0.72, "DE": 0.64, "AU": 0.66, "JP": 0.56, "KR": 0.70,
            "BR": 0.76, "MX": 0.74, "AR": 0.66, "CL": 0.68, "CO": 0.74,
            "PE": 0.70, "IN": 0.85, "PK": 0.70, "NG": 0.80, "GH": 0.78,
            "ZW": 0.68, "EG": 0.65, "JO": 0.68, "TR": 0.62, "RU": 0.60,
            "UA": 0.55, "RO": 0.58, "PH": 0.76, "TH": 0.80, "NZ": 0.68,
            "NL": 0.66,
        },
    ),

    # 13. Death penalty justifiable (V198, 6+/10)
    WVSPairedQuestion(
        id="t_death_penalty", text="Is the death penalty justifiable?",
        wvs_var="V198", coding="6+/10 justifiable",
        wave6={
            "US": 0.42, "DE": 0.18, "AU": 0.28, "JP": 0.55, "KR": 0.45,
            "BR": 0.30, "MX": 0.22, "AR": 0.20, "CL": 0.25, "CO": 0.18,
            "IN": 0.42, "PK": 0.52, "NG": 0.55, "GH": 0.42, "ZW": 0.45,
            "EG": 0.48, "JO": 0.40, "TR": 0.30, "RU": 0.35, "UA": 0.25,
            "RO": 0.22, "PH": 0.48, "TH": 0.35, "NZ": 0.22, "NL": 0.15,
        },
        wave7={
            "US": 0.40, "DE": 0.16, "AU": 0.24, "JP": 0.52, "KR": 0.42,
            "BR": 0.32, "MX": 0.24, "AR": 0.18, "CL": 0.22, "CO": 0.16,
            "IN": 0.40, "PK": 0.50, "NG": 0.52, "GH": 0.40, "ZW": 0.42,
            "EG": 0.45, "JO": 0.38, "TR": 0.28, "RU": 0.32, "UA": 0.22,
            "RO": 0.20, "PH": 0.45, "TH": 0.32, "NZ": 0.20, "NL": 0.12,
        },
    ),

    # 14. Environment vs economy (V81, protect environment priority)
    WVSPairedQuestion(
        id="t_environment", text="Should protecting the environment be priority over economic growth?",
        wvs_var="V81", coding="protect environment priority",
        wave6={
            "US": 0.42, "DE": 0.62, "AU": 0.52, "JP": 0.48, "KR": 0.52,
            "BR": 0.55, "MX": 0.48, "AR": 0.50, "CL": 0.48, "CO": 0.42,
            "PE": 0.38, "IN": 0.38, "PK": 0.30, "NG": 0.32, "GH": 0.35,
            "EG": 0.25, "JO": 0.28, "TR": 0.42, "RU": 0.35, "UA": 0.30,
            "RO": 0.38, "PH": 0.48, "TH": 0.55, "NZ": 0.58, "NL": 0.65,
            "EC": 0.45,
        },
        wave7={
            "US": 0.44, "DE": 0.68, "AU": 0.56, "JP": 0.52, "KR": 0.58,
            "BR": 0.56, "MX": 0.50, "AR": 0.52, "CL": 0.52, "CO": 0.45,
            "PE": 0.40, "IN": 0.40, "PK": 0.32, "NG": 0.34, "GH": 0.38,
            "EG": 0.28, "JO": 0.30, "TR": 0.45, "RU": 0.38, "UA": 0.32,
            "RO": 0.42, "PH": 0.52, "TH": 0.58, "NZ": 0.62, "NL": 0.70,
            "EC": 0.48,
        },
    ),

    # 15. Hard work leads to success (V181, hard work emphasis)
    WVSPairedQuestion(
        id="t_hard_work", text="Does hard work generally bring success?",
        wvs_var="V181", coding="hard work > luck (6+/10)",
        wave6={
            "US": 0.72, "DE": 0.52, "AU": 0.58, "JP": 0.42, "KR": 0.48,
            "BR": 0.62, "MX": 0.72, "AR": 0.48, "CL": 0.55, "CO": 0.68,
            "PE": 0.65, "IN": 0.78, "PK": 0.75, "NG": 0.82, "GH": 0.80,
            "ZW": 0.72, "EG": 0.68, "JO": 0.62, "TR": 0.68, "RU": 0.42,
            "UA": 0.38, "RO": 0.48, "PH": 0.72, "TH": 0.65, "NZ": 0.60,
            "NL": 0.55,
        },
        wave7={
            "US": 0.73, "DE": 0.52, "AU": 0.56, "JP": 0.42, "KR": 0.46,
            "BR": 0.60, "MX": 0.70, "AR": 0.45, "CL": 0.52, "CO": 0.65,
            "PE": 0.62, "IN": 0.78, "PK": 0.74, "NG": 0.82, "GH": 0.78,
            "ZW": 0.70, "EG": 0.65, "JO": 0.58, "TR": 0.65, "RU": 0.40,
            "UA": 0.36, "RO": 0.45, "PH": 0.70, "TH": 0.62, "NZ": 0.58,
            "NL": 0.52,
        },
    ),
]


def summary() -> str:
    """Print summary of paired dataset."""
    lines = [f"WVS Paired Dataset: {len(WVS_PAIRED)} questions"]
    for q in WVS_PAIRED:
        oc = q.overlapping_countries
        deltas = q.deltas
        mean_delta = sum(deltas.values()) / len(deltas) if deltas else 0
        max_abs = max(abs(v) for v in deltas.values()) if deltas else 0
        lines.append(
            f"  {q.id:<20s} {q.wvs_var:<6s} "
            f"countries={len(oc):2d} "
            f"mean_Δ={mean_delta:+.3f} "
            f"max|Δ|={max_abs:.3f}"
        )
    return "\n".join(lines)
