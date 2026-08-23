"""GEOGRAPHY — continents, countries, regions, localities, cities as
addressable entities (API-COMPLETE-1, 2026-08-23). Pure readout layer:
nothing here is read by the dynamics.

Locality key (the unit the cascade block and presence use):
    loc = country_idx * 1000 + region_idx * 2 + urban
A CITY is the urban locality of a genesis region, named from the
region profile — it is the model's own urban population, not an
invented one; Earth-1 has no named settlements below region level.
"""
from __future__ import annotations

import numpy as np

AF, AS, EU, NA, SA, OC = ("Africa", "Asia", "Europe", "North America",
                          "South America", "Oceania")
CONTINENT = {
 "IN": AS, "CN": AS, "US": NA, "ID": AS, "PK": AS, "NG": AF, "BR": SA, "BD": AS, "RU": EU, "ET": AF,
 "MX": NA, "JP": AS, "EG": AF, "PH": AS, "CD": AF, "VN": AS, "IR": AS, "TR": AS, "DE": EU, "TH": AS,
 "GB": EU, "TZ": AF, "FR": EU, "ZA": AF, "IT": EU, "KE": AF, "MM": AS, "CO": SA, "KR": AS, "SD": AF,
 "UG": AF, "ES": EU, "DZ": AF, "IQ": AS, "AR": SA, "AF": AS, "YE": AS, "CA": NA, "PL": EU, "MA": AF,
 "AO": AF, "UA": EU, "UZ": AS, "MY": AS, "MZ": AF, "GH": AF, "PE": SA, "SA": AS, "CI": AF, "MG": AF,
 "NP": AS, "CM": AF, "VE": SA, "NE": AF, "AU": OC, "KP": AS, "ML": AF, "SY": AS, "BF": AF, "LK": AS,
 "MW": AF, "ZM": AF, "KZ": AS, "TD": AF, "CL": SA, "SO": AF, "RO": EU, "SN": AF, "GT": NA, "EC": SA,
 "NL": EU, "KH": AS, "ZW": AF, "GN": AF, "BJ": AF, "RW": AF, "BI": AF, "BO": SA, "TN": AF, "HT": NA,
 "BE": EU, "JO": AS, "DO": NA, "AE": AS, "CU": NA, "HN": NA, "CZ": EU, "SE": EU, "PG": OC, "TJ": AS,
 "PT": EU, "AZ": AS, "GR": EU, "HU": EU, "TG": AF, "IL": AS, "BY": EU, "AT": EU, "CH": EU, "SL": AF,
 "LA": AS, "HK": AS, "LY": AF, "TM": AS, "KG": AS, "NI": NA, "PY": SA, "BG": EU, "RS": EU, "SV": NA,
 "CG": AF, "DK": EU, "SG": AS, "LR": AF, "FI": EU, "NO": EU, "PS": AS, "LB": AS, "CF": AF, "IE": EU,
 "SK": EU, "CR": NA, "MR": AF, "NZ": OC, "KW": AS, "OM": AS, "PA": NA, "HR": EU, "GE": AS, "ER": AF,
 "MN": AS, "UY": SA, "PR": NA, "BA": EU, "QA": AS, "NA": AF, "AM": AS, "MD": EU, "LT": EU, "JM": NA,
 "AL": EU, "BW": AF, "GM": AF, "GA": AF, "LS": AF, "GW": AF, "SI": EU, "GQ": AF, "LV": EU, "MK": EU,
 "BH": AS, "XK": EU, "TT": NA, "EE": EU, "CY": AS, "MU": AF, "SZ": AF, "DJ": AF, "FJ": OC, "RE": AF,
 "KM": AF, "BT": AS, "SB": OC, "LU": EU, "ME": EU, "SR": SA, "MT": EU, "MV": AS, "CV": AF, "BN": AS,
 "BS": NA, "BZ": NA, "IS": EU, "BB": NA, "VU": OC, "LC": NA, "WS": OC, "ST": AF, "GD": NA, "TO": OC,
 "KI": OC, "FM": OC, "SC": AF, "AG": NA, "AD": EU, "DM": NA, "MC": EU, "LI": EU, "MH": OC, "SM": EU,
 "PW": OC, "NR": OC, "TV": OC, "VA": EU,
}
CONTINENTS = (AF, AS, EU, NA, SA, OC)


def country_codes():
    from earth1.genesis import GENESIS_COUNTRY_CODES
    return GENESIS_COUNTRY_CODES


def continent_of(iso2: str) -> str:
    return CONTINENT.get(iso2, "Unknown")


def locality_key(civ) -> np.ndarray:
    return (civ.country.astype(np.int64) * 1000
            + civ.region.astype(np.int64) * 2 + civ.urban.astype(np.int64))


def split_key(loc: int):
    loc = int(loc)
    return loc // 1000, (loc % 1000) // 2, loc % 2


def region_profile(iso2: str, region_idx: int):
    from earth1.regions import get_regions
    regs = get_regions(iso2)
    if 0 <= region_idx < len(regs):
        return regs[region_idx]
    return None


def locality_name(loc: int) -> str:
    ci, ri, urb = split_key(loc)
    codes = country_codes()
    iso2 = codes[ci] if ci < len(codes) else f"#{ci}"
    prof = region_profile(iso2, ri)
    rname = prof.name if prof is not None else f"region {ri}"
    return f"{rname} — {'urban' if urb else 'rural'}"


def city_name(loc: int) -> str:
    ci, ri, urb = split_key(loc)
    codes = country_codes()
    iso2 = codes[ci] if ci < len(codes) else f"#{ci}"
    prof = region_profile(iso2, ri)
    rname = prof.name if prof is not None else f"region {ri}"
    return f"urban centre of {rname}"


def localities(w, alive_only: bool = True):
    """(key, pop) for every occupied locality."""
    loc = locality_key(w.civ)
    m = w.health.alive if alive_only else np.ones(w.civ.n, bool)
    u, c = np.unique(loc[m], return_counts=True)
    return u, c
