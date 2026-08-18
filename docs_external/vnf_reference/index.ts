// aggregate-wvs-microdata — Streaming aggregator for WVS Wave 7 raw microdata.
//
// Reads raw/WVS_Cross-National_Wave_7_csv_v6_0.csv from the wvs-uploads bucket
// line-by-line (never buffers), applies survey weights (W_WEIGHT), excludes
// negative missing-value codes (-1,-2,-4,-5), and emits two seed CSVs:
//
//   wvs_wave7_seeds_v1.csv        — country-axis seeds (target_<iso2>)
//   wvs_wave7_cohort_seeds_v1.csv — cohort-axis seeds pooled across countries
//                                    (target_far_left…target_far_right from
//                                    Q240, plus target age buckets from Q262).
//
// Refuses to overwrite the shortlist. If the spot-check block at the end
// disagrees with known Wave 7 published figures (US "most people can be
// trusted" ~37–40%, importance-of-God US ≫ DE ≫ JP), the function returns
// a spot_check_failed error and DOES NOT write the CSVs.
//
// POST body: { dry_run?: boolean }  — always safe; only writes on success.
//
// deno-lint-ignore-file no-explicit-any
import { createClient } from "npm:@supabase/supabase-js@2.45.0";

const cors: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// ---------------------------------------------------------------------------
// Question spec table. Each entry defines how to convert a raw WVS response
// value into a binary "yes" for aggregation. Missing-value codes (negative)
// are ALWAYS excluded from both numerator and denominator upstream, so the
// predicate here only sees valid non-negative response values.
// ---------------------------------------------------------------------------
type Rule =
  | { kind: "binary_1"; noteTag: "rule=binary_yes=1" }
  | { kind: "top2of4"; noteTag: "rule=top2of4" }
  | { kind: "range_6to10of10"; noteTag: "rule=6-10of10" }
  | { kind: "neighbor_mentioned"; noteTag: "rule=neighbor_mentioned" };

interface QSpec {
  code: string;             // WVS column name
  text: string;             // Human-readable question text for the seed row
  rule: Rule;
  starred?: boolean;        // Include in cohort-axis file too
}

const RULE_BIN: Rule       = { kind: "binary_1",           noteTag: "rule=binary_yes=1" };
const RULE_TOP2: Rule      = { kind: "top2of4",            noteTag: "rule=top2of4" };
const RULE_IMP: Rule       = { kind: "range_6to10of10",    noteTag: "rule=6-10of10" };
const RULE_NEIGH: Rule     = { kind: "neighbor_mentioned", noteTag: "rule=neighbor_mentioned" };

const QUESTIONS: QSpec[] = [
  // Generalised trust (binary)
  { code: "Q57",  text: "Most people can be trusted",                          rule: RULE_BIN,  starred: true  },

  // Neighbours you would not like (Q18–Q26): "mentioned" = would not want
  { code: "Q18",  text: "Would not want as neighbours: drug addicts",          rule: RULE_NEIGH },
  { code: "Q19",  text: "Would not want as neighbours: people of different race", rule: RULE_NEIGH, starred: true },
  { code: "Q20",  text: "Would not want as neighbours: people with AIDS",      rule: RULE_NEIGH },
  { code: "Q21",  text: "Would not want as neighbours: immigrants/foreign workers", rule: RULE_NEIGH, starred: true },
  { code: "Q22",  text: "Would not want as neighbours: homosexuals",           rule: RULE_NEIGH, starred: true },
  { code: "Q23",  text: "Would not want as neighbours: people of a different religion", rule: RULE_NEIGH },
  { code: "Q24",  text: "Would not want as neighbours: heavy drinkers",        rule: RULE_NEIGH },
  { code: "Q25",  text: "Would not want as neighbours: unmarried couples living together", rule: RULE_NEIGH },
  { code: "Q26",  text: "Would not want as neighbours: people who speak a different language", rule: RULE_NEIGH },

  // Confidence in institutions (Q65–Q89): top2of4 (great deal + quite a lot)
  { code: "Q65",  text: "Confidence: the churches",                            rule: RULE_TOP2, starred: true },
  { code: "Q66",  text: "Confidence: the armed forces",                        rule: RULE_TOP2, starred: true },
  { code: "Q67",  text: "Confidence: the press",                               rule: RULE_TOP2 },
  { code: "Q68",  text: "Confidence: television",                              rule: RULE_TOP2 },
  { code: "Q69",  text: "Confidence: labour unions",                           rule: RULE_TOP2 },
  { code: "Q70",  text: "Confidence: the police",                              rule: RULE_TOP2, starred: true },
  { code: "Q71",  text: "Confidence: the courts / justice system",             rule: RULE_TOP2, starred: true },
  { code: "Q72",  text: "Confidence: the government",                          rule: RULE_TOP2, starred: true },
  { code: "Q73",  text: "Confidence: political parties",                       rule: RULE_TOP2 },
  { code: "Q74",  text: "Confidence: parliament",                              rule: RULE_TOP2, starred: true },
  { code: "Q75",  text: "Confidence: the civil service",                       rule: RULE_TOP2 },
  { code: "Q76",  text: "Confidence: universities",                            rule: RULE_TOP2 },
  { code: "Q77",  text: "Confidence: elections",                               rule: RULE_TOP2, starred: true },
  { code: "Q78",  text: "Confidence: major companies",                         rule: RULE_TOP2 },
  { code: "Q79",  text: "Confidence: banks",                                   rule: RULE_TOP2 },
  { code: "Q80",  text: "Confidence: environmental protection movement",       rule: RULE_TOP2 },
  { code: "Q81",  text: "Confidence: the women's movement",                    rule: RULE_TOP2 },
  { code: "Q82",  text: "Confidence: charitable/humanitarian organizations",   rule: RULE_TOP2 },
  { code: "Q83",  text: "Confidence: regional/local government",               rule: RULE_TOP2 },
  { code: "Q84",  text: "Confidence: regional integration organization",       rule: RULE_TOP2 },
  { code: "Q85",  text: "Confidence: the United Nations",                      rule: RULE_TOP2, starred: true },
  { code: "Q86",  text: "Confidence: the International Monetary Fund",         rule: RULE_TOP2 },
  { code: "Q88",  text: "Confidence: the World Health Organization",           rule: RULE_TOP2 },
  { code: "Q89",  text: "Confidence: the World Bank",                          rule: RULE_TOP2 },

  // Religiosity beliefs (binary, yes=1)
  { code: "Q165", text: "Believe in God",                                      rule: RULE_BIN,  starred: true },
  { code: "Q166", text: "Believe in life after death",                         rule: RULE_BIN },
  { code: "Q167", text: "Believe in hell",                                     rule: RULE_BIN,  starred: true },
  { code: "Q168", text: "Believe in heaven",                                   rule: RULE_BIN },

  // Importance / attitude 1–10 (yes = 6..10)
  { code: "Q106", text: "Incomes should be made more equal (agree, 6–10 of 10)", rule: RULE_IMP },
  { code: "Q107", text: "Private ownership of business should be increased (6–10 of 10)", rule: RULE_IMP },
  { code: "Q108", text: "Government should take more responsibility (6–10 of 10)", rule: RULE_IMP },
  { code: "Q158", text: "Science and technology make life healthier, easier, more comfortable (6–10 of 10)", rule: RULE_IMP },
  { code: "Q159", text: "Science and technology give more opportunities to next generation (6–10 of 10)", rule: RULE_IMP },
  { code: "Q160", text: "Because of science and technology there will be more opportunities for next generation (6–10 of 10)", rule: RULE_IMP },
  { code: "Q161", text: "We depend too much on science, not enough on faith (6–10 of 10)", rule: RULE_IMP, starred: true },
  { code: "Q162", text: "Science and technology are making our lives change too fast (6–10 of 10)", rule: RULE_IMP },
  { code: "Q163", text: "It is not important for me to know about science in my daily life (6–10 of 10)", rule: RULE_IMP },
  { code: "Q164", text: "Importance of God in your life (6–10 of 10)",         rule: RULE_IMP, starred: true },
  { code: "Q250", text: "Importance of living in a democratically governed country (6–10 of 10)", rule: RULE_IMP, starred: true },

  // Justifiability 1–10 (yes = 6..10)
  { code: "Q177", text: "Justifiable: claiming government benefits you are not entitled to (6–10)", rule: RULE_IMP },
  { code: "Q178", text: "Justifiable: avoiding a fare on public transport (6–10)", rule: RULE_IMP },
  { code: "Q179", text: "Justifiable: stealing property (6–10)",               rule: RULE_IMP },
  { code: "Q180", text: "Justifiable: cheating on taxes (6–10)",               rule: RULE_IMP, starred: true },
  { code: "Q181", text: "Justifiable: someone accepting a bribe (6–10)",       rule: RULE_IMP, starred: true },
  { code: "Q182", text: "Justifiable: homosexuality (6–10)",                   rule: RULE_IMP, starred: true },
  { code: "Q183", text: "Justifiable: prostitution (6–10)",                    rule: RULE_IMP },
  { code: "Q184", text: "Justifiable: abortion (6–10)",                        rule: RULE_IMP, starred: true },
  { code: "Q185", text: "Justifiable: divorce (6–10)",                         rule: RULE_IMP, starred: true },
  { code: "Q186", text: "Justifiable: sex before marriage (6–10)",             rule: RULE_IMP },
  { code: "Q187", text: "Justifiable: suicide (6–10)",                         rule: RULE_IMP },
  { code: "Q188", text: "Justifiable: euthanasia (6–10)",                      rule: RULE_IMP },
  { code: "Q189", text: "Justifiable: for a man to beat his wife (6–10)",      rule: RULE_IMP, starred: true },
  { code: "Q190", text: "Justifiable: parents beating children (6–10)",        rule: RULE_IMP },
  { code: "Q191", text: "Justifiable: violence against other people (6–10)",   rule: RULE_IMP },
  { code: "Q192", text: "Justifiable: terrorism as a political, ideological or religious means (6–10)", rule: RULE_IMP },
  { code: "Q193", text: "Justifiable: casual sex (6–10)",                      rule: RULE_IMP },
  { code: "Q194", text: "Justifiable: political violence (6–10)",              rule: RULE_IMP },
  { code: "Q195", text: "Justifiable: death penalty (6–10)",                   rule: RULE_IMP },
];

// ---------------------------------------------------------------------------
// ISO3 → ISO2 map (Wave 7 respondent countries).
// ---------------------------------------------------------------------------
const ISO3_TO_ISO2: Record<string, string> = {
  AND:"AD", ARG:"AR", ARM:"AM", AUS:"AU", BGD:"BD", BOL:"BO", BRA:"BR", CAN:"CA",
  CHL:"CL", CHN:"CN", COL:"CO", CYP:"CY", CZE:"CZ", DEU:"DE", ECU:"EC", EGY:"EG",
  ETH:"ET", GBR:"GB", GRC:"GR", GTM:"GT", HKG:"HK", IDN:"ID", IND:"IN", IRN:"IR",
  IRQ:"IQ", JOR:"JO", JPN:"JP", KAZ:"KZ", KEN:"KE", KGZ:"KG", KOR:"KR", LBN:"LB",
  LBY:"LY", MAC:"MO", MAR:"MA", MDV:"MV", MEX:"MX", MMR:"MM", MNG:"MN", MYS:"MY",
  NGA:"NG", NIC:"NI", NIR:"GB", NLD:"NL", NZL:"NZ", PAK:"PK", PER:"PE", PHL:"PH",
  PRI:"PR", ROU:"RO", RUS:"RU", SGP:"SG", SRB:"RS", SVK:"SK", THA:"TH", TJK:"TJ",
  TUN:"TN", TUR:"TR", TWN:"TW", UKR:"UA", URY:"UY", USA:"US", UZB:"UZ", VEN:"VE",
  VNM:"VN", ZWE:"ZW",
};

// ---------------------------------------------------------------------------
// Predicate: does this raw WVS value count as "yes" under the given rule?
// Preconditions: v is finite AND v >= 0 (missing codes already excluded).
// ---------------------------------------------------------------------------
function isYes(rule: Rule, v: number): boolean {
  switch (rule.kind) {
    case "binary_1":           return v === 1;
    case "top2of4":            return v === 1 || v === 2;
    case "range_6to10of10":    return v >= 6 && v <= 10;
    case "neighbor_mentioned": return v === 1;
  }
}

// ---------------------------------------------------------------------------
// Minimal CSV row splitter — handles double-quoted fields with embedded
// commas and escaped quotes. WVS data is numeric so escapes are rare, but we
// still handle them correctly.
// ---------------------------------------------------------------------------
function splitCsv(line: string): string[] {
  const out: string[] = [];
  let cur = "";
  let inQ = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQ) {
      if (c === '"') {
        if (line[i + 1] === '"') { cur += '"'; i++; }
        else inQ = false;
      } else cur += c;
    } else {
      if (c === ',')      { out.push(cur); cur = ""; }
      else if (c === '"') { inQ = true; }
      else                { cur += c; }
    }
  }
  out.push(cur);
  return out;
}

// ---------------------------------------------------------------------------
// Accumulators
// ---------------------------------------------------------------------------
type Acc = { sw: number; swy: number; n: number };
const mk = (): Acc => ({ sw: 0, swy: 0, n: 0 });

// per (qcode, iso2)
const countryAcc = new Map<string, Map<string, Acc>>();
// per (qcode, left_right_bucket)   buckets: far_left|left|centrist|right|far_right
const lrAcc = new Map<string, Map<string, Acc>>();
// per (qcode, age_bucket)          buckets: 18_29|30_44|45_59|60_plus
const ageAcc = new Map<string, Map<string, Acc>>();

function bump(map: Map<string, Map<string, Acc>>, qcode: string, key: string, w: number, yes: boolean) {
  let m = map.get(qcode);
  if (!m) { m = new Map(); map.set(qcode, m); }
  let a = m.get(key);
  if (!a) { a = mk(); m.set(key, a); }
  a.sw += w;
  if (yes) a.swy += w;
  a.n += 1;
}

function lrBucket(v: number): string | null {
  if (v < 1 || v > 10) return null;
  if (v <= 2) return "far_left";
  if (v <= 4) return "left";
  if (v <= 6) return "centrist";
  if (v <= 8) return "right";
  return "far_right";
}

function ageBucket(v: number): string | null {
  if (v < 15 || v > 120) return null;
  if (v <= 29) return "18_29";
  if (v <= 44) return "30_44";
  if (v <= 59) return "45_59";
  return "60_plus";
}

// ---------------------------------------------------------------------------
// Stream loop
// ---------------------------------------------------------------------------
async function processStream(
  stream: ReadableStream<Uint8Array>,
  onHeader: (header: string[]) => void,
  onRow: (row: string[]) => void,
) {
  const reader = stream.pipeThrough(new TextDecoderStream("utf-8")).getReader();
  let buf = "";
  let headerDone = false;
  let rowCount = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (value) buf += value;
    let nl: number;
    while ((nl = buf.indexOf("\n")) >= 0) {
      let line = buf.slice(0, nl);
      buf = buf.slice(nl + 1);
      if (line.endsWith("\r")) line = line.slice(0, -1);
      if (!line.length) continue;
      const cells = splitCsv(line);
      if (!headerDone) { onHeader(cells); headerDone = true; }
      else             { onRow(cells); rowCount++; }
    }
    if (done) break;
  }
  if (buf.trim().length) {
    const cells = splitCsv(buf);
    if (headerDone) { onRow(cells); rowCount++; }
    else            { onHeader(cells); }
  }
  return rowCount;
}

// ---------------------------------------------------------------------------
// CSV writers
// ---------------------------------------------------------------------------
const MIN_WEIGHTED_N = 500;

function fmtPct(a: Acc): string {
  if (a.sw <= 0) return "";
  return (a.swy / a.sw).toFixed(6);
}

function buildCountryCsv(): { csv: string; rows: number } {
  const iso2List = [...new Set(Object.values(ISO3_TO_ISO2))].sort();
  const header = ["question_text","question_type","source","notes", ...iso2List.map((c) => `target_${c}`)].join(",");
  const lines: string[] = [header];
  let emitted = 0;
  for (const q of QUESTIONS) {
    const m = countryAcc.get(q.code);
    if (!m) continue;
    const targets = iso2List.map((iso2) => {
      const a = m.get(iso2);
      if (!a || a.n < MIN_WEIGHTED_N || a.sw <= 0) return "";
      return fmtPct(a);
    });
    const hasAny = targets.some((t) => t !== "");
    if (!hasAny) continue;
    const notes = `wvs_code=${q.code};${q.rule.noteTag}`;
    const text = q.text.replace(/"/g, '""');
    lines.push(`"${text}","wvs_seed","WVS Wave 7","${notes}",${targets.join(",")}`);
    emitted++;
  }
  return { csv: lines.join("\n") + "\n", rows: emitted };
}

function buildCohortCsv(): { csv: string; rows: number } {
  const lrCols = ["far_left","left","centrist","right","far_right"];
  const ageCols = ["18_29","30_44","45_59","60_plus"];
  const header = [
    "question_text","question_type","source","notes",
    ...lrCols.map((c) => `target_${c}`),
    ...ageCols.map((c) => `target_age_${c}`),
  ].join(",");
  const lines: string[] = [header];
  let emitted = 0;
  for (const q of QUESTIONS) {
    if (!q.starred) continue;
    const lrM = lrAcc.get(q.code);
    const ageM = ageAcc.get(q.code);
    if (!lrM && !ageM) continue;
    const lrTargets = lrCols.map((k) => {
      const a = lrM?.get(k);
      if (!a || a.n < MIN_WEIGHTED_N) return "";
      return fmtPct(a);
    });
    const ageTargets = ageCols.map((k) => {
      const a = ageM?.get(k);
      if (!a || a.n < MIN_WEIGHTED_N) return "";
      return fmtPct(a);
    });
    // Need ≥3 non-empty cohorts total for the seed to be usable by the solver
    const nonEmpty = [...lrTargets, ...ageTargets].filter((t) => t !== "").length;
    if (nonEmpty < 3) continue;
    const notes = `wvs_code=${q.code};${q.rule.noteTag};cohorts=lr+age`;
    const text = q.text.replace(/"/g, '""');
    lines.push(`"${text}","wvs_cohort_seed","WVS Wave 7","${notes}",${lrTargets.join(",")},${ageTargets.join(",")}`);
    emitted++;
  }
  return { csv: lines.join("\n") + "\n", rows: emitted };
}

// ---------------------------------------------------------------------------
// Spot-check gate. Refuses to write CSVs if these known-good published Wave 7
// figures come out wildly wrong. Bands are wide enough to allow legitimate
// methodology drift; failure indicates a mapping or missing-code bug.
// ---------------------------------------------------------------------------
function spotCheck(): { ok: boolean; details: any } {
  const q57 = countryAcc.get("Q57");
  const q164 = countryAcc.get("Q164");
  const usTrust = q57?.get("US");
  const usGod  = q164?.get("US");
  const deGod  = q164?.get("DE");
  const jpGod  = q164?.get("JP");

  const details: any = {};
  const checks: { name: string; pass: boolean; got?: any; band?: string }[] = [];

  const usTrustPct = usTrust && usTrust.sw > 0 ? usTrust.swy / usTrust.sw : null;
  details.us_trust = usTrustPct;
  checks.push({
    name: "US Q57 trust ~0.34–0.42 band",
    pass: usTrustPct !== null && usTrustPct >= 0.30 && usTrustPct <= 0.45,
    got: usTrustPct, band: "0.30..0.45",
  });

  const usGodPct = usGod && usGod.sw > 0 ? usGod.swy / usGod.sw : null;
  const deGodPct = deGod && deGod.sw > 0 ? deGod.swy / deGod.sw : null;
  const jpGodPct = jpGod && jpGod.sw > 0 ? jpGod.swy / jpGod.sw : null;
  details.us_god = usGodPct;
  details.de_god = deGodPct;
  details.jp_god = jpGodPct;
  checks.push({
    name: "Importance of God ordering US > DE > JP",
    pass: usGodPct !== null && deGodPct !== null && jpGodPct !== null
       && usGodPct > deGodPct && deGodPct > jpGodPct,
    got: { us: usGodPct, de: deGodPct, jp: jpGodPct },
  });

  details.checks = checks;
  return { ok: checks.every((c) => c.pass), details };
}

// ---------------------------------------------------------------------------
// Deno.serve entrypoint
// ---------------------------------------------------------------------------
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });
  const json = (b: unknown, status = 200) =>
    new Response(JSON.stringify(b), { status, headers: { ...cors, "Content-Type": "application/json" } });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
  const SERVICE_KEY  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const supa = createClient(SUPABASE_URL, SERVICE_KEY);

  const t0 = Date.now();
  const body = await req.json().catch(() => ({}));
  const dry_run: boolean = body?.dry_run === true;
  const source_path: string = body?.source_path ?? "raw/WVS_Cross-National_Wave_7_csv_v6_0.csv";

  // Reset accumulators (safety: function may be warm)
  countryAcc.clear(); lrAcc.clear(); ageAcc.clear();


  // Header column index map
  const colIdx = new Map<string, number>();
  const qCodes = new Set(QUESTIONS.map((q) => q.code));
  qCodes.add("Q240"); // left-right self-placement
  qCodes.add("Q262"); // age in years

  let idxW = -1;
  let idxCtry = -1;
  let idxLR = -1;
  let idxAge = -1;
  const qIdx = new Map<string, number>();

  let rows = 0;
  let ignoredNoCountry = 0;
  let ignoredNoWeight  = 0;

  // Stream via signed URL fetch — avoids materialising the whole 182MB blob
  // in memory (which is what happens if we `.download()` and call `.stream()`
  // on the returned Blob). A true HTTP body stream is chunked.
  const { data: signed, error: signErr } = await supa.storage
    .from("wvs-uploads").createSignedUrl(source_path, 600);
  if (signErr || !signed?.signedUrl) return json({ error: `sign failed: ${signErr?.message}` }, 500);
  const resp = await fetch(signed.signedUrl);
  if (!resp.ok || !resp.body) return json({ error: `fetch failed: ${resp.status}` }, 500);
  const stream = resp.body;
  await processStream(
    stream,
    (header) => {
      for (let i = 0; i < header.length; i++) {
        const raw = header[i].trim();
        colIdx.set(raw, i);
      }
      idxW    = colIdx.get("W_WEIGHT") ?? -1;
      idxCtry = colIdx.get("B_COUNTRY_ALPHA") ?? -1;
      idxLR   = colIdx.get("Q240") ?? -1;
      idxAge  = colIdx.get("Q262") ?? -1;
      for (const q of QUESTIONS) {
        const j = colIdx.get(q.code);
        if (j !== undefined) qIdx.set(q.code, j);
      }
    },
    (row) => {
      rows++;
      if (idxCtry < 0 || idxW < 0) return;
      const iso3 = (row[idxCtry] ?? "").trim();
      const iso2 = ISO3_TO_ISO2[iso3];
      if (!iso2) { ignoredNoCountry++; return; }

      const w = Number(row[idxW]);
      if (!Number.isFinite(w) || w <= 0) { ignoredNoWeight++; return; }

      // Cohort keys — only used for starred questions
      const lrVal = idxLR >= 0 ? Number(row[idxLR]) : NaN;
      const lrKey = Number.isFinite(lrVal) && lrVal >= 0 ? lrBucket(lrVal) : null;
      const ageVal = idxAge >= 0 ? Number(row[idxAge]) : NaN;
      const ageKey = Number.isFinite(ageVal) && ageVal >= 0 ? ageBucket(ageVal) : null;

      for (const q of QUESTIONS) {
        const j = qIdx.get(q.code);
        if (j === undefined) continue;
        const raw = row[j];
        if (raw === "" || raw === undefined) continue;
        const v = Number(raw);
        // MISSING-VALUE GUARD: WVS negatives (-1..-5) are missing codes and
        // MUST be excluded from both numerator and denominator.
        if (!Number.isFinite(v) || v < 0) continue;
        const yes = isYes(q.rule, v);

        bump(countryAcc, q.code, iso2, w, yes);
        if (q.starred) {
          if (lrKey)  bump(lrAcc,  q.code, lrKey,  w, yes);
          if (ageKey) bump(ageAcc, q.code, ageKey, w, yes);
        }
      }
    },
  );

  const check = spotCheck();

  // Build both CSVs regardless — we return their sizes and always include the
  // spot-check block so the operator can see the numbers.
  const country = buildCountryCsv();
  const cohort = buildCohortCsv();

  const shouldWrite = check.ok && !dry_run;

  const result: any = {
    ok: check.ok,
    rows_processed: rows,
    ignored_no_country: ignoredNoCountry,
    ignored_no_weight: ignoredNoWeight,
    country_seeds: country.rows,
    cohort_seeds: cohort.rows,
    spot_check: check.details,
    wrote: false,
    dry_run,
    elapsed_ms: Date.now() - t0,
  };

  if (!check.ok) {
    return json({ ...result, error: "spot_check_failed — refusing to write CSVs" }, 422);
  }

  if (shouldWrite) {
    const enc = new TextEncoder();
    const up1 = await supa.storage.from("wvs-uploads").upload(
      "wvs_wave7_seeds_v1.csv", enc.encode(country.csv),
      { contentType: "text/csv", upsert: true },
    );
    const up2 = await supa.storage.from("wvs-uploads").upload(
      "wvs_wave7_cohort_seeds_v1.csv", enc.encode(cohort.csv),
      { contentType: "text/csv", upsert: true },
    );
    if (up1.error || up2.error) {
      return json({ ...result, error: `upload failed: ${up1.error?.message ?? up2.error?.message}` }, 500);
    }
    result.wrote = true;
    result.paths = ["wvs_wave7_seeds_v1.csv", "wvs_wave7_cohort_seeds_v1.csv"];
  } else {
    // Dry-run — attach small previews so operator can eyeball the output
    result.country_csv_head = country.csv.split("\n").slice(0, 4).join("\n");
    result.cohort_csv_head  = cohort.csv.split("\n").slice(0, 4).join("\n");
  }

  return json(result);
});
