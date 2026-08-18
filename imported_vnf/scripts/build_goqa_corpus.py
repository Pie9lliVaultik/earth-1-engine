"""
build_goqa_corpus.py — flatten the FULL GlobalOpinionQA item bank
(Anthropic/llm_global_opinions: Pew Global Attitudes Survey + WVS Wave 7)
into benchmark_calibrations-shaped seeds.

Input : /tmp/goqa.csv  (HF: Anthropic/llm_global_opinions, 2,556 rows)
Output: /tmp/goqa_seeds_full.json  (list of {question_text, question_type,
        source, target_by_group:{country_XX: yes_share}, notes})

Rules
-----
* selections is a python-repr defaultdict → parsed with a regex.
* Country names → ISO2 via census_country_targets names + alias table.
  Sub-national rows ("Britain", "Northern Ireland", "Czech Rep.") are aliased;
  unmappable rows are dropped (never guessed).
* DK / Refused / "No answer" options are removed from BOTH numerator and
  denominator before computing the yes share.
* yes_indices: agree/favor/approve/support/good/yes/trust-style options.
  When no lexical hit exists we fall back to the top half of an ordinal scale
  (the project's long-standing GOQA convention) and tag notes with `cut=half`
  so the binarization is auditable.
* Seeds need >= 3 mapped countries.
"""
import ast, csv, json, os, re, sys

SRC = "/tmp/goqa.csv"
OUT = "/tmp/goqa_seeds_full.json"

ALIASES = {
    "britain": "GB", "great britain": "GB", "united kingdom": "GB", "uk": "GB",
    "northern ireland": "GB", "s. korea": "KR", "south korea": "KR",
    "north korea": "KP", "czech rep.": "CZ", "czechia": "CZ", "czech republic": "CZ",
    "slovak rep.": "SK", "slovakia": "SK", "russia": "RU", "russian federation": "RU",
    "united states": "US", "u.s.": "US", "usa": "US", "america": "US",
    "palest. ter.": "PS", "palestinian ter.": "PS", "palestinian territories": "PS",
    "bosnia herz.": "BA", "bosnia and herzegovina": "BA", "macedonia": "MK",
    "north macedonia": "MK", "ivory coast": "CI", "cote d'ivoire": "CI",
    "côte d'ivoire": "CI", "burkina faso": "BF", "el salvador": "SV",
    "hong kong sar": "HK", "hong kong": "HK", "macau": "MO", "macau sar": "MO", "bosnia herzegovina": "BA", "macao sar": "MO",
    "taiwan roc": "TW", "taiwan": "TW", "vietnam": "VN", "viet nam": "VN",
    "iran": "IR", "syria": "SY", "tanzania": "TZ", "venezuela": "VE",
    "bolivia": "BO", "moldova": "MD", "laos": "LA", "myanmar": "MM", "burma": "MM",
    "congo": "CG", "dem. rep. congo": "CD", "drc": "CD", "s. africa": "ZA",
    "south africa": "ZA", "uae": "AE", "united arab emirates": "AE",
    "puerto rico": "PR", "andorra": "AD", "kosovo": "XK", "serbia": "RS",
    "turkey": "TR", "türkiye": "TR", "egypt": "EG", "germany": "DE",
    "netherlands": "NL", "the netherlands": "NL", "philippines": "PH",
    "dominican rep.": "DO", "dominican republic": "DO", "trinidad": "TT",
    "guinea bissau": "GW", "guinea-bissau": "GW", "cape verde": "CV",
    "cabo verde": "CV", "swaziland": "SZ", "eswatini": "SZ",
}

DK_RX = re.compile(
    r"^(dk|dk/refus|dk/ref|don'?t know|do not know|no answer|refused|refuse|"
    r"none of these|no opinion|not sure|neither|dk/na|na|missing|other)\b",
    re.I,
)
YES_RX = re.compile(
    r"(strongly\s+)?(agree|favor|favour|approve|support|trust|good|yes|"
    r"very good|somewhat good|a great deal|quite a lot|better|more|"
    r"very important|rather important|satisfied|confident|justifiable|"
    r"very well|somewhat well|positive|increase|should)\b",
    re.I,
)
NO_RX = re.compile(
    r"(strongly\s+)?(disagree|oppose|disapprove|distrust|bad|no\b|not\s|"
    r"never|unimportant|dissatisfied|worse|less|decrease|should not|"
    r"not at all|not very|very bad|somewhat bad|negative)",
    re.I,
)


def load_name_map():
    """iso2 lookup from the census table (names) merged with the alias table."""
    import subprocess
    out = subprocess.run(
        ["psql", "-At", "-F", "\t", "-c", "select iso2, name from census_country_targets"],
        capture_output=True, text=True, check=True,
    ).stdout
    m = {}
    for line in out.strip().splitlines():
        iso2, name = line.split("\t")
        m[name.lower().strip()] = iso2
    m.update(ALIASES)
    return m


# Pew ships several sample frames per country. Keep national frames only,
# preferring the current national sample over older ones; drop non-national
# (urban-only / oversample) frames entirely so panels stay comparable.
PAREN_RX = re.compile(r"\s*\(([^)]*)\)\s*$")


def normalize_country(cname):
    """-> (lowercased base name, preference rank) or (None, None) to drop."""
    raw = cname.strip()
    m = PAREN_RX.search(raw)
    rank = 1
    if m:
        qual = m.group(1).lower()
        base = PAREN_RX.sub("", raw).strip()
        if "non-national" in qual:
            return None, None
        if "current national" in qual:
            rank = 0
        elif "old national" in qual:
            rank = 2
        elif "national" in qual:
            rank = 1
        else:
            return None, None
        raw = base
    return raw.lower().strip(), rank


SEL_RX = re.compile(r"'([^']+)'\s*:\s*\[([^\]]*)\]")


def parse_selections(s):
    return {
        k: [float(x) for x in v.split(",") if x.strip()]
        for k, v in SEL_RX.findall(s)
    }


def parse_options(s):
    try:
        v = ast.literal_eval(s)
        return [str(x) for x in v] if isinstance(v, (list, tuple)) else []
    except Exception:
        return []


def yes_indices(options):
    keep = [i for i, o in enumerate(options) if not DK_RX.match(o.strip())]
    if len(keep) < 2:
        return None, None, None
    yes = [i for i in keep if YES_RX.search(options[i]) and not NO_RX.match(options[i].strip())]
    no = [i for i in keep if i not in yes]
    cut = "lexical"
    if not yes or not no:
        half = max(1, len(keep) // 2)
        yes, no = keep[:half], keep[half:]
        cut = "half"
    return yes, keep, cut


def main():
    name_map = load_name_map()
    seeds, dropped, unmapped = [], {"few_countries": 0, "bad_options": 0}, {}
    with open(SRC, newline="", encoding="utf-8") as f:
        for idx, row in enumerate(csv.DictReader(f)):
            options = parse_options(row["options"])
            if len(options) < 2:
                dropped["bad_options"] += 1
                continue
            yes, keep, cut = yes_indices(options)
            if yes is None:
                dropped["bad_options"] += 1
                continue
            sel = parse_selections(row["selections"] or "")
            targets, ranks = {}, {}
            for cname, pcts in sel.items():
                base, rank = normalize_country(cname)
                if base is None:
                    continue
                iso2 = name_map.get(base)
                if not iso2:
                    unmapped[cname] = unmapped.get(cname, 0) + 1
                    continue
                if len(pcts) != len(options):
                    continue
                denom = sum(pcts[i] for i in keep)
                if denom <= 0:
                    continue
                share = sum(pcts[i] for i in yes) / denom
                if 0.0 <= share <= 1.0:
                    key = f"country_{iso2}"
                    prev = ranks.get(key)
                    if prev is None or rank < prev:
                        ranks[key] = rank
                        targets[key] = round(share, 6)
            if len(targets) < 3:
                dropped["few_countries"] += 1
                continue
            src = "Pew Global Attitudes Survey" if row["source"] == "GAS" else "WVS Wave 7"
            seeds.append({
                "question_text": row["question"].strip(),
                "question_type": "goqa_seed",
                "source": src,
                "target_by_group": targets,
                "notes": f"goqa#{idx};src={row['source']};opts={len(options)};yes=[{','.join(map(str, yes))}];cut={cut}",
            })
    # de-dupe on normalized text, keep the widest country panel
    best = {}
    for s in seeds:
        k = re.sub(r"\s+", " ", s["question_text"].lower()).strip()
        if k not in best or len(s["target_by_group"]) > len(best[k]["target_by_group"]):
            best[k] = s
    seeds = list(best.values())
    json.dump(seeds, open(OUT, "w"), ensure_ascii=False)
    print(f"seeds={len(seeds)} dropped={dropped}")
    print("top unmapped:", sorted(unmapped.items(), key=lambda x: -x[1])[:15])
    by_src = {}
    for s in seeds:
        by_src[s["source"]] = by_src.get(s["source"], 0) + 1
    print("by source:", by_src)
    print("median countries:", sorted(len(s["target_by_group"]) for s in seeds)[len(seeds) // 2])


if __name__ == "__main__":
    main()
