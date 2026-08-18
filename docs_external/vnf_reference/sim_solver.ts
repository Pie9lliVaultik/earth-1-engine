// Sprint 3.5 — Simulation-calibrated inverse weight solver.
//
// Replaces the closed-form ridge solver with a population-simulated
// gradient-descent solver that fits the SAME function the runtime vote
// RPC computes — eliminating the Jensen / cohort-mean gap, the geometric
// noise gap, and the trait-distribution mismatch in one shot.
//
// Runtime vote function (per agent i in cohort g):
//   s_i  = Σ β_t · (t_i - pm_t)                  [stance_raw]
//   pol_i = ps_g · β_pol                          [political_term]
//   inner_i = 0.5 + 0.5·β0 + 0.5·tanh(s_i) + pol_i
//   yes_score_i = clip(W_GEO·0.5 + W_STANCE·inner_i, 0, 1)
//                            (we assume geometric ≈ 0.5 at solve time,
//                             since seeds have no question embedding)
//   P_i = σ(K · (yes_score_i - 0.5))
// Per-cohort predicted YES share = mean_i in g (P_i).
//
// Loss = Σ_g w_g · (mean P_i in g - target_g)²  +  ridge regularisation.
//
// Optimises 8 scalars: β0 baseline, 6 trait β (desire, risk, doubt,
// empathy, openness, economics), β_pol. fear/collective remain 0 — they
// are deterministic linear combinations of the primitives.

import { SOLVER_TRAITS, TRAIT_ORDER, type TraitKey } from "./inverse_solver.ts";

const W_GEO = 0.10;          // matches v_w_geo when p_requires_knowledge
const W_STANCE = 0.90;
const K_DECISION = 4.0;
const GEOMETRIC_ASSUMED = 0.5;

export interface SampledAgent {
  desire: number; risk: number; doubt: number; empathy: number;
  openness: number; economics: number;
}

export interface SimCohort {
  cohort: string;
  target_yes: number;          // (0,1)
  weight: number;              // population share
  political_scalar: number;    // [-1,+1]
  agents: SampledAgent[];      // raw trait values (NOT centered)
}

export interface SimSolveOptions {
  populationMeans: Record<TraitKey, number>;
  /** Ridge on trait β (default 0.05). */
  lambdaTraits?: number;
  /** Ridge on political β (default 0.001). */
  lambdaPolitical?: number;
  /** Ridge on baseline (default 0.01). */
  lambdaBaseline?: number;
  weightCap?: number;          // default 1.0
  politicalWeightCap?: number; // default 3.0
  baselineCap?: number;        // default 1.5
  /** Adam learning rate (default 0.05). */
  lr?: number;
  /** Max iterations (default 800). */
  maxIter?: number;
  /** Convergence tolerance on loss delta (default 1e-7). */
  tol?: number;
}

export interface SimSolved {
  baseline: number;
  weights: Record<TraitKey, number>;
  political_weight: number;
  per_cohort: { cohort: string; target: number; predicted: number; resid: number; n: number }[];
  residual_rms: number;
  iterations: number;
  final_loss: number;
  n_cohorts: number;
  method: "sim_gradient_descent";
}

function sigmoid(x: number): number {
  if (x >= 0) { const e = Math.exp(-x); return 1 / (1 + e); }
  const e = Math.exp(x); return e / (1 + e);
}
function clip(x: number, lo: number, hi: number) {
  return x < lo ? lo : (x > hi ? hi : x);
}

// Param packing: [β0, β_desire, β_risk, β_doubt, β_empathy, β_openness, β_economics, β_pol]
const NPARAM = 1 + SOLVER_TRAITS.length + 1; // 8

interface PrepCohort {
  cohort: string;
  target: number;
  weight: number;
  ps: number;
  // Pre-centered per-agent trait values: agents[i][traitIdx] = (raw - pm)
  centered: number[][]; // [N][6]
}

function prep(cohorts: SimCohort[], pm: Record<TraitKey, number>): PrepCohort[] {
  return cohorts.map((c) => ({
    cohort: c.cohort,
    target: clip(c.target_yes, 1e-3, 1 - 1e-3),
    weight: Math.max(1e-6, c.weight),
    ps: Number.isFinite(c.political_scalar) ? c.political_scalar : 0,
    centered: c.agents.map((a) =>
      SOLVER_TRAITS.map((t) => (a as any)[t] - pm[t])
    ),
  }));
}

/** Compute loss + gradient at theta. Returns [loss, grad(NPARAM)]. */
function lossAndGrad(
  theta: number[],
  cohorts: PrepCohort[],
  lambdas: { traits: number; political: number; baseline: number },
): { loss: number; grad: number[] } {
  const b0 = theta[0];
  const bt = theta.slice(1, 1 + SOLVER_TRAITS.length); // 6
  const bp = theta[1 + SOLVER_TRAITS.length];
  const grad = new Array(NPARAM).fill(0);
  let loss = 0;

  for (const c of cohorts) {
    const N = c.centered.length;
    if (N === 0) continue;
    // Forward pass aggregating mean(P_i) and accumulating per-agent
    // partial derivatives dP_i/dθ.
    let sumP = 0;
    // We'll need per-agent intermediates to backprop; store as we go.
    // To save memory, accumulate dMeanP/dθ directly.
    const dMean = new Array(NPARAM).fill(0);

    for (let i = 0; i < N; i++) {
      const tv = c.centered[i]; // length 6
      // stance_raw
      let s = 0;
      for (let k = 0; k < tv.length; k++) s += bt[k] * tv[k];
      const tanhS = Math.tanh(s);
      const inner = 0.5 + 0.5 * b0 + 0.5 * tanhS + c.ps * bp;
      const raw = W_GEO * GEOMETRIC_ASSUMED + W_STANCE * inner;
      // yes_score clipped 0..1. Outside clip dP/draw = 0.
      let clipped = raw;
      const dRaw_dInner = W_STANCE;
      let active = true;
      if (raw <= 0) { clipped = 0; active = false; }
      else if (raw >= 1) { clipped = 1; active = false; }
      const z = K_DECISION * (clipped - 0.5);
      const P = sigmoid(z);
      sumP += P;

      if (active) {
        const dP_dz = P * (1 - P);
        const dP_dRaw = dP_dz * K_DECISION;
        const dP_dInner = dP_dRaw * dRaw_dInner;
        // dInner/db0 = 0.5
        dMean[0] += dP_dInner * 0.5;
        // dInner/dbp = ps
        dMean[1 + SOLVER_TRAITS.length] += dP_dInner * c.ps;
        // dInner/dtanhS = 0.5; dtanhS/ds = 1 - tanhS²; ds/dbt[k] = tv[k]
        const dInner_ds = 0.5 * (1 - tanhS * tanhS);
        const chain = dP_dInner * dInner_ds;
        for (let k = 0; k < tv.length; k++) {
          dMean[1 + k] += chain * tv[k];
        }
      }
    }

    const meanP = sumP / N;
    const resid = meanP - c.target;
    loss += c.weight * resid * resid;
    // dLoss/dθ from this cohort = w · 2·resid · (1/N) · sum(dP_i/dθ)
    const scale = c.weight * 2 * resid / N;
    for (let p = 0; p < NPARAM; p++) grad[p] += scale * dMean[p];
  }

  // Ridge
  loss += lambdas.baseline * theta[0] * theta[0];
  grad[0] += 2 * lambdas.baseline * theta[0];
  for (let k = 0; k < SOLVER_TRAITS.length; k++) {
    loss += lambdas.traits * bt[k] * bt[k];
    grad[1 + k] += 2 * lambdas.traits * bt[k];
  }
  loss += lambdas.political * bp * bp;
  grad[1 + SOLVER_TRAITS.length] += 2 * lambdas.political * bp;

  return { loss, grad };
}

export function solveSim(cohorts: SimCohort[], opts: SimSolveOptions): SimSolved {
  if (cohorts.length < 3) throw new Error(`solveSim: need ≥3 cohorts, got ${cohorts.length}`);
  const pm = opts.populationMeans;
  const lambdas = {
    traits:    opts.lambdaTraits    ?? 0.05,
    political: opts.lambdaPolitical ?? 0.001,
    baseline:  opts.lambdaBaseline  ?? 0.01,
  };
  const weightCap = opts.weightCap ?? 1.0;
  const polCap    = opts.politicalWeightCap ?? 3.0;
  const baseCap   = opts.baselineCap ?? 1.5;
  const lr        = opts.lr ?? 0.05;
  const maxIter   = opts.maxIter ?? 800;
  const tol       = opts.tol ?? 1e-7;

  const prepped = prep(cohorts, pm);

  // Init: zeros (baseline + traits) and a small positive political guess
  // aligned with the cohort target gradient along ps.
  const theta = new Array(NPARAM).fill(0);
  // Crude warm start: regress target_logit on ps to seed β_pol & β0.
  {
    let sw = 0, sps = 0, st = 0, sps2 = 0, spst = 0;
    for (const c of prepped) {
      const w = c.weight, z = Math.log(c.target / (1 - c.target));
      sw += w; sps += w * c.ps; st += w * z;
      sps2 += w * c.ps * c.ps; spst += w * c.ps * z;
    }
    const meanPs = sps / sw, meanZ = st / sw;
    const denom = sps2 - sw * meanPs * meanPs;
    const slope = denom > 1e-9 ? (spst - sw * meanPs * meanZ) / denom : 0;
    const inter = meanZ - slope * meanPs;
    // Translate logit-of-target ≈ inter + slope·ps into our parametrisation.
    // yes_score - 0.5 ≈ W_STANCE · (0.5·b0 + ps·bp). Set bp ≈ slope/(4·W_STANCE),
    // b0 ≈ inter/(2·W_STANCE).
    theta[0] = clip(inter / (2 * W_STANCE * K_DECISION), -baseCap, baseCap);
    theta[1 + SOLVER_TRAITS.length] =
      clip(slope / (K_DECISION * W_STANCE), -polCap, polCap);
  }

  // Adam
  const m = new Array(NPARAM).fill(0);
  const v = new Array(NPARAM).fill(0);
  const b1 = 0.9, b2 = 0.999, eps = 1e-8;
  let prevLoss = Infinity, finalLoss = Infinity, iter = 0;

  for (iter = 1; iter <= maxIter; iter++) {
    const { loss, grad } = lossAndGrad(theta, prepped, lambdas);
    finalLoss = loss;
    for (let p = 0; p < NPARAM; p++) {
      m[p] = b1 * m[p] + (1 - b1) * grad[p];
      v[p] = b2 * v[p] + (1 - b2) * grad[p] * grad[p];
      const mh = m[p] / (1 - Math.pow(b1, iter));
      const vh = v[p] / (1 - Math.pow(b2, iter));
      theta[p] -= lr * mh / (Math.sqrt(vh) + eps);
    }
    // Project onto caps each step (keeps Adam stable near boundary).
    theta[0] = clip(theta[0], -baseCap, baseCap);
    for (let k = 0; k < SOLVER_TRAITS.length; k++)
      theta[1 + k] = clip(theta[1 + k], -weightCap, weightCap);
    theta[1 + SOLVER_TRAITS.length] = clip(theta[1 + SOLVER_TRAITS.length], -polCap, polCap);

    if (Math.abs(prevLoss - loss) < tol && iter > 30) break;
    prevLoss = loss;
  }

  // Evaluate per-cohort predictions at final theta.
  const b0 = theta[0];
  const bt = theta.slice(1, 1 + SOLVER_TRAITS.length);
  const bp = theta[1 + SOLVER_TRAITS.length];

  const per_cohort = prepped.map((c) => {
    const N = c.centered.length;
    let sumP = 0;
    for (let i = 0; i < N; i++) {
      const tv = c.centered[i];
      let s = 0; for (let k = 0; k < tv.length; k++) s += bt[k] * tv[k];
      const inner = 0.5 + 0.5 * b0 + 0.5 * Math.tanh(s) + c.ps * bp;
      const raw = clip(W_GEO * GEOMETRIC_ASSUMED + W_STANCE * inner, 0, 1);
      sumP += sigmoid(K_DECISION * (raw - 0.5));
    }
    const pred = N > 0 ? sumP / N : 0.5;
    return { cohort: c.cohort, target: c.target, predicted: pred, resid: pred - c.target, n: N };
  });
  const sumW = per_cohort.reduce((s, _, i) => s + prepped[i].weight, 0);
  const sse = per_cohort.reduce((s, r, i) => s + prepped[i].weight * r.resid * r.resid, 0);
  const residual_rms = Math.sqrt(sse / Math.max(1e-9, sumW));

  const weights = {} as Record<TraitKey, number>;
  for (const t of TRAIT_ORDER) weights[t] = 0;
  for (let k = 0; k < SOLVER_TRAITS.length; k++) weights[SOLVER_TRAITS[k]] = bt[k];

  return {
    baseline: b0,
    weights,
    political_weight: bp,
    per_cohort,
    residual_rms,
    iterations: iter,
    final_loss: finalLoss,
    n_cohorts: prepped.length,
    method: "sim_gradient_descent",
  };
}
