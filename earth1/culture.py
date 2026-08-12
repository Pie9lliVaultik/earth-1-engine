"""Cultural data layer — Hofstede 6 dimensions + Inglehart-Welzel 2 dimensions.

Real research data for ~76 countries, normalized to 0-1 scale.
Hofstede scores from Hofstede Insights (original 0-100 scale / 100).
Inglehart-Welzel values from World Values Survey cultural map (original -2 to +2, rescaled to 0-1).
"""
from __future__ import annotations
from typing import Dict, List, Optional


# Hofstede 6 dimensions per country (normalized 0-1)
# PDI = Power Distance, IDV = Individualism, MAS = Masculinity,
# UAI = Uncertainty Avoidance, LTO = Long-Term Orientation, IVR = Indulgence
HOFSTEDE: Dict[str, Dict[str, float]] = {
    "AF": {"pdi": 0.95, "idv": 0.14, "mas": 0.62, "uai": 0.70, "lto": 0.12, "ivr": 0.34},
    "AL": {"pdi": 0.90, "idv": 0.20, "mas": 0.80, "uai": 0.70, "lto": 0.61, "ivr": 0.15},
    "DZ": {"pdi": 0.80, "idv": 0.35, "mas": 0.35, "uai": 0.68, "lto": 0.26, "ivr": 0.32},
    "AR": {"pdi": 0.49, "idv": 0.46, "mas": 0.56, "uai": 0.86, "lto": 0.20, "ivr": 0.62},
    "AU": {"pdi": 0.38, "idv": 0.90, "mas": 0.61, "uai": 0.51, "lto": 0.21, "ivr": 0.71},
    "AT": {"pdi": 0.11, "idv": 0.55, "mas": 0.79, "uai": 0.70, "lto": 0.60, "ivr": 0.63},
    "BD": {"pdi": 0.80, "idv": 0.20, "mas": 0.55, "uai": 0.60, "lto": 0.47, "ivr": 0.20},
    "BE": {"pdi": 0.65, "idv": 0.75, "mas": 0.54, "uai": 0.94, "lto": 0.82, "ivr": 0.57},
    "BA": {"pdi": 0.90, "idv": 0.30, "mas": 0.40, "uai": 0.87, "lto": 0.70, "ivr": 0.44},
    "BR": {"pdi": 0.69, "idv": 0.38, "mas": 0.49, "uai": 0.76, "lto": 0.44, "ivr": 0.59},
    "BG": {"pdi": 0.70, "idv": 0.30, "mas": 0.40, "uai": 0.85, "lto": 0.69, "ivr": 0.16},
    "CA": {"pdi": 0.39, "idv": 0.80, "mas": 0.52, "uai": 0.48, "lto": 0.36, "ivr": 0.68},
    "CL": {"pdi": 0.63, "idv": 0.23, "mas": 0.28, "uai": 0.86, "lto": 0.31, "ivr": 0.68},
    "CN": {"pdi": 0.80, "idv": 0.20, "mas": 0.66, "uai": 0.30, "lto": 0.87, "ivr": 0.24},
    "CO": {"pdi": 0.67, "idv": 0.13, "mas": 0.64, "uai": 0.80, "lto": 0.13, "ivr": 0.83},
    "CR": {"pdi": 0.35, "idv": 0.15, "mas": 0.21, "uai": 0.86, "lto": 0.00, "ivr": 0.90},
    "HR": {"pdi": 0.73, "idv": 0.33, "mas": 0.40, "uai": 0.80, "lto": 0.58, "ivr": 0.33},
    "CZ": {"pdi": 0.57, "idv": 0.58, "mas": 0.57, "uai": 0.74, "lto": 0.70, "ivr": 0.29},
    "DK": {"pdi": 0.18, "idv": 0.74, "mas": 0.16, "uai": 0.23, "lto": 0.35, "ivr": 0.70},
    "EC": {"pdi": 0.78, "idv": 0.08, "mas": 0.63, "uai": 0.67, "lto": 0.00, "ivr": 0.75},
    "EG": {"pdi": 0.70, "idv": 0.25, "mas": 0.45, "uai": 0.80, "lto": 0.07, "ivr": 0.04},
    "SV": {"pdi": 0.66, "idv": 0.19, "mas": 0.40, "uai": 0.94, "lto": 0.20, "ivr": 0.89},
    "EE": {"pdi": 0.40, "idv": 0.60, "mas": 0.30, "uai": 0.60, "lto": 0.82, "ivr": 0.16},
    "ET": {"pdi": 0.70, "idv": 0.20, "mas": 0.65, "uai": 0.55, "lto": 0.25, "ivr": 0.46},
    "FI": {"pdi": 0.33, "idv": 0.63, "mas": 0.26, "uai": 0.59, "lto": 0.38, "ivr": 0.57},
    "FR": {"pdi": 0.68, "idv": 0.71, "mas": 0.43, "uai": 0.86, "lto": 0.63, "ivr": 0.48},
    "DE": {"pdi": 0.35, "idv": 0.67, "mas": 0.66, "uai": 0.65, "lto": 0.83, "ivr": 0.40},
    "GH": {"pdi": 0.80, "idv": 0.15, "mas": 0.40, "uai": 0.65, "lto": 0.04, "ivr": 0.72},
    "GR": {"pdi": 0.60, "idv": 0.35, "mas": 0.57, "uai": 1.00, "lto": 0.45, "ivr": 0.50},
    "GT": {"pdi": 0.95, "idv": 0.06, "mas": 0.37, "uai": 1.01, "lto": 0.00, "ivr": 0.80},
    "HU": {"pdi": 0.46, "idv": 0.80, "mas": 0.88, "uai": 0.82, "lto": 0.58, "ivr": 0.31},
    "IN": {"pdi": 0.77, "idv": 0.48, "mas": 0.56, "uai": 0.40, "lto": 0.51, "ivr": 0.26},
    "ID": {"pdi": 0.78, "idv": 0.14, "mas": 0.46, "uai": 0.48, "lto": 0.62, "ivr": 0.38},
    "IR": {"pdi": 0.58, "idv": 0.41, "mas": 0.43, "uai": 0.59, "lto": 0.14, "ivr": 0.40},
    "IQ": {"pdi": 0.95, "idv": 0.30, "mas": 0.70, "uai": 0.85, "lto": 0.25, "ivr": 0.17},
    "IE": {"pdi": 0.28, "idv": 0.70, "mas": 0.68, "uai": 0.35, "lto": 0.24, "ivr": 0.65},
    "IL": {"pdi": 0.13, "idv": 0.54, "mas": 0.47, "uai": 0.81, "lto": 0.38, "ivr": 0.00},
    "IT": {"pdi": 0.50, "idv": 0.76, "mas": 0.70, "uai": 0.75, "lto": 0.61, "ivr": 0.30},
    "JP": {"pdi": 0.54, "idv": 0.46, "mas": 0.95, "uai": 0.92, "lto": 0.88, "ivr": 0.42},
    "JO": {"pdi": 0.70, "idv": 0.30, "mas": 0.45, "uai": 0.65, "lto": 0.16, "ivr": 0.43},
    "KE": {"pdi": 0.70, "idv": 0.25, "mas": 0.60, "uai": 0.50, "lto": 0.00, "ivr": 0.67},
    "KR": {"pdi": 0.60, "idv": 0.18, "mas": 0.39, "uai": 0.85, "lto": 1.00, "ivr": 0.29},
    "LV": {"pdi": 0.44, "idv": 0.70, "mas": 0.09, "uai": 0.63, "lto": 0.69, "ivr": 0.13},
    "LT": {"pdi": 0.42, "idv": 0.60, "mas": 0.19, "uai": 0.65, "lto": 0.82, "ivr": 0.16},
    "MY": {"pdi": 1.00, "idv": 0.26, "mas": 0.50, "uai": 0.36, "lto": 0.41, "ivr": 0.57},
    "MX": {"pdi": 0.81, "idv": 0.30, "mas": 0.69, "uai": 0.82, "lto": 0.24, "ivr": 0.97},
    "MA": {"pdi": 0.70, "idv": 0.46, "mas": 0.53, "uai": 0.68, "lto": 0.14, "ivr": 0.25},
    "NL": {"pdi": 0.38, "idv": 0.80, "mas": 0.14, "uai": 0.53, "lto": 0.67, "ivr": 0.68},
    "NZ": {"pdi": 0.22, "idv": 0.79, "mas": 0.58, "uai": 0.49, "lto": 0.33, "ivr": 0.75},
    "NG": {"pdi": 0.80, "idv": 0.30, "mas": 0.60, "uai": 0.55, "lto": 0.13, "ivr": 0.84},
    "NO": {"pdi": 0.31, "idv": 0.69, "mas": 0.08, "uai": 0.50, "lto": 0.35, "ivr": 0.55},
    "PK": {"pdi": 0.55, "idv": 0.14, "mas": 0.50, "uai": 0.70, "lto": 0.50, "ivr": 0.00},
    "PA": {"pdi": 0.95, "idv": 0.11, "mas": 0.44, "uai": 0.86, "lto": 0.00, "ivr": 0.97},
    "PE": {"pdi": 0.64, "idv": 0.16, "mas": 0.42, "uai": 0.87, "lto": 0.25, "ivr": 0.46},
    "PH": {"pdi": 0.94, "idv": 0.32, "mas": 0.64, "uai": 0.44, "lto": 0.27, "ivr": 0.42},
    "PL": {"pdi": 0.68, "idv": 0.60, "mas": 0.64, "uai": 0.93, "lto": 0.38, "ivr": 0.29},
    "PT": {"pdi": 0.63, "idv": 0.27, "mas": 0.31, "uai": 0.99, "lto": 0.28, "ivr": 0.33},
    "RO": {"pdi": 0.90, "idv": 0.30, "mas": 0.42, "uai": 0.90, "lto": 0.52, "ivr": 0.20},
    "RU": {"pdi": 0.93, "idv": 0.39, "mas": 0.36, "uai": 0.95, "lto": 0.81, "ivr": 0.20},
    "SA": {"pdi": 0.95, "idv": 0.25, "mas": 0.60, "uai": 0.80, "lto": 0.36, "ivr": 0.52},
    "RS": {"pdi": 0.86, "idv": 0.25, "mas": 0.43, "uai": 0.92, "lto": 0.52, "ivr": 0.28},
    "SG": {"pdi": 0.74, "idv": 0.20, "mas": 0.48, "uai": 0.08, "lto": 0.72, "ivr": 0.46},
    "SK": {"pdi": 1.00, "idv": 0.52, "mas": 1.00, "uai": 0.51, "lto": 0.77, "ivr": 0.28},
    "SI": {"pdi": 0.71, "idv": 0.27, "mas": 0.19, "uai": 0.88, "lto": 0.49, "ivr": 0.48},
    "ZA": {"pdi": 0.49, "idv": 0.65, "mas": 0.63, "uai": 0.49, "lto": 0.34, "ivr": 0.63},
    "ES": {"pdi": 0.57, "idv": 0.51, "mas": 0.42, "uai": 0.86, "lto": 0.48, "ivr": 0.44},
    "SE": {"pdi": 0.31, "idv": 0.71, "mas": 0.05, "uai": 0.29, "lto": 0.53, "ivr": 0.78},
    "CH": {"pdi": 0.34, "idv": 0.68, "mas": 0.70, "uai": 0.58, "lto": 0.74, "ivr": 0.66},
    "TW": {"pdi": 0.58, "idv": 0.17, "mas": 0.45, "uai": 0.69, "lto": 0.93, "ivr": 0.49},
    "TH": {"pdi": 0.64, "idv": 0.20, "mas": 0.34, "uai": 0.64, "lto": 0.32, "ivr": 0.45},
    "TR": {"pdi": 0.66, "idv": 0.37, "mas": 0.45, "uai": 0.85, "lto": 0.46, "ivr": 0.49},
    "UA": {"pdi": 0.92, "idv": 0.25, "mas": 0.27, "uai": 0.95, "lto": 0.86, "ivr": 0.18},
    "AE": {"pdi": 0.90, "idv": 0.25, "mas": 0.50, "uai": 0.80, "lto": 0.00, "ivr": 0.00},
    "GB": {"pdi": 0.35, "idv": 0.89, "mas": 0.66, "uai": 0.35, "lto": 0.51, "ivr": 0.69},
    "US": {"pdi": 0.40, "idv": 0.91, "mas": 0.62, "uai": 0.46, "lto": 0.26, "ivr": 0.68},
    "VE": {"pdi": 0.81, "idv": 0.12, "mas": 0.73, "uai": 0.76, "lto": 0.16, "ivr": 1.00},
    "VN": {"pdi": 0.70, "idv": 0.20, "mas": 0.40, "uai": 0.30, "lto": 0.57, "ivr": 0.35},
}

# Inglehart-Welzel World Cultural Map coordinates
# trad_sec: Traditional vs Secular-Rational (original -2..+2, rescaled to 0..1)
# surv_self: Survival vs Self-Expression (original -2..+2, rescaled to 0..1)
INGLEHART: Dict[str, Dict[str, float]] = {
    "AF": {"trad_sec": 0.10, "surv_self": 0.10},
    "AL": {"trad_sec": 0.35, "surv_self": 0.30},
    "DZ": {"trad_sec": 0.15, "surv_self": 0.25},
    "AR": {"trad_sec": 0.35, "surv_self": 0.55},
    "AU": {"trad_sec": 0.55, "surv_self": 0.80},
    "AT": {"trad_sec": 0.60, "surv_self": 0.70},
    "BD": {"trad_sec": 0.15, "surv_self": 0.20},
    "BE": {"trad_sec": 0.55, "surv_self": 0.70},
    "BA": {"trad_sec": 0.40, "surv_self": 0.30},
    "BR": {"trad_sec": 0.30, "surv_self": 0.50},
    "BG": {"trad_sec": 0.55, "surv_self": 0.25},
    "CA": {"trad_sec": 0.50, "surv_self": 0.80},
    "CL": {"trad_sec": 0.30, "surv_self": 0.50},
    "CN": {"trad_sec": 0.70, "surv_self": 0.30},
    "CO": {"trad_sec": 0.20, "surv_self": 0.45},
    "CR": {"trad_sec": 0.25, "surv_self": 0.55},
    "HR": {"trad_sec": 0.45, "surv_self": 0.35},
    "CZ": {"trad_sec": 0.75, "surv_self": 0.55},
    "DK": {"trad_sec": 0.70, "surv_self": 0.85},
    "EC": {"trad_sec": 0.20, "surv_self": 0.40},
    "EG": {"trad_sec": 0.10, "surv_self": 0.20},
    "SV": {"trad_sec": 0.20, "surv_self": 0.35},
    "EE": {"trad_sec": 0.70, "surv_self": 0.45},
    "ET": {"trad_sec": 0.10, "surv_self": 0.15},
    "FI": {"trad_sec": 0.65, "surv_self": 0.75},
    "FR": {"trad_sec": 0.55, "surv_self": 0.70},
    "DE": {"trad_sec": 0.75, "surv_self": 0.70},
    "GH": {"trad_sec": 0.15, "surv_self": 0.30},
    "GR": {"trad_sec": 0.40, "surv_self": 0.45},
    "GT": {"trad_sec": 0.15, "surv_self": 0.30},
    "HU": {"trad_sec": 0.55, "surv_self": 0.35},
    "IN": {"trad_sec": 0.25, "surv_self": 0.30},
    "ID": {"trad_sec": 0.15, "surv_self": 0.35},
    "IR": {"trad_sec": 0.25, "surv_self": 0.25},
    "IQ": {"trad_sec": 0.15, "surv_self": 0.15},
    "IE": {"trad_sec": 0.35, "surv_self": 0.70},
    "IL": {"trad_sec": 0.45, "surv_self": 0.55},
    "IT": {"trad_sec": 0.45, "surv_self": 0.60},
    "JP": {"trad_sec": 0.85, "surv_self": 0.55},
    "JO": {"trad_sec": 0.15, "surv_self": 0.20},
    "KE": {"trad_sec": 0.10, "surv_self": 0.25},
    "KR": {"trad_sec": 0.75, "surv_self": 0.45},
    "LV": {"trad_sec": 0.60, "surv_self": 0.35},
    "LT": {"trad_sec": 0.50, "surv_self": 0.35},
    "MY": {"trad_sec": 0.20, "surv_self": 0.40},
    "MX": {"trad_sec": 0.25, "surv_self": 0.50},
    "MA": {"trad_sec": 0.15, "surv_self": 0.25},
    "NL": {"trad_sec": 0.65, "surv_self": 0.80},
    "NZ": {"trad_sec": 0.55, "surv_self": 0.80},
    "NG": {"trad_sec": 0.10, "surv_self": 0.25},
    "NO": {"trad_sec": 0.70, "surv_self": 0.85},
    "PK": {"trad_sec": 0.10, "surv_self": 0.15},
    "PA": {"trad_sec": 0.20, "surv_self": 0.45},
    "PE": {"trad_sec": 0.25, "surv_self": 0.40},
    "PH": {"trad_sec": 0.15, "surv_self": 0.35},
    "PL": {"trad_sec": 0.45, "surv_self": 0.45},
    "PT": {"trad_sec": 0.40, "surv_self": 0.55},
    "RO": {"trad_sec": 0.35, "surv_self": 0.25},
    "RU": {"trad_sec": 0.65, "surv_self": 0.20},
    "SA": {"trad_sec": 0.10, "surv_self": 0.20},
    "RS": {"trad_sec": 0.50, "surv_self": 0.25},
    "SG": {"trad_sec": 0.45, "surv_self": 0.55},
    "SK": {"trad_sec": 0.55, "surv_self": 0.40},
    "SI": {"trad_sec": 0.55, "surv_self": 0.55},
    "ZA": {"trad_sec": 0.20, "surv_self": 0.35},
    "ES": {"trad_sec": 0.50, "surv_self": 0.65},
    "SE": {"trad_sec": 0.80, "surv_self": 0.90},
    "CH": {"trad_sec": 0.60, "surv_self": 0.80},
    "TW": {"trad_sec": 0.70, "surv_self": 0.50},
    "TH": {"trad_sec": 0.30, "surv_self": 0.35},
    "TR": {"trad_sec": 0.30, "surv_self": 0.30},
    "UA": {"trad_sec": 0.55, "surv_self": 0.20},
    "AE": {"trad_sec": 0.15, "surv_self": 0.40},
    "GB": {"trad_sec": 0.50, "surv_self": 0.75},
    "US": {"trad_sec": 0.40, "surv_self": 0.75},
    "VE": {"trad_sec": 0.20, "surv_self": 0.40},
    "VN": {"trad_sec": 0.55, "surv_self": 0.25},
}

_HOFSTEDE_KEYS = ("pdi", "idv", "mas", "uai", "lto", "ivr")
_INGLEHART_KEYS = ("trad_sec", "surv_self")


def get_culture(country_code: str) -> Optional[Dict[str, float]]:
    """Return merged Hofstede + Inglehart dict for a country, or None if missing."""
    h = HOFSTEDE.get(country_code)
    i = INGLEHART.get(country_code)
    if h is None and i is None:
        return None
    merged: Dict[str, float] = {}
    if h:
        merged.update(h)
    if i:
        merged.update(i)
    return merged


def get_hofstede(country_code: str) -> Optional[Dict[str, float]]:
    """Return Hofstede 6-dim dict for a country, or None."""
    return HOFSTEDE.get(country_code)


def get_inglehart(country_code: str) -> Optional[Dict[str, float]]:
    """Return Inglehart-Welzel 2-dim dict for a country, or None."""
    return INGLEHART.get(country_code)


def list_countries_with_culture() -> List[str]:
    """Return sorted list of country codes that have both Hofstede and Inglehart data."""
    return sorted(set(HOFSTEDE.keys()) & set(INGLEHART.keys()))


def list_hofstede_countries() -> List[str]:
    """Return sorted list of country codes with Hofstede data."""
    return sorted(HOFSTEDE.keys())


def list_inglehart_countries() -> List[str]:
    """Return sorted list of country codes with Inglehart data."""
    return sorted(INGLEHART.keys())
