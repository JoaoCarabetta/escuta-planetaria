/**
 * Client-side recommender v1 — preference from dwell/reading time + mais/menos.
 * Epsilon-greedy over cosine similarity to a localStorage profile.
 */

const STORAGE_KEY = "escuta.feed.profile.v1";
const EPSILON = 0.18;
const DWELL_WEIGHT = 1.0;
const EXPLICIT_WEIGHT = 2.4;
const MIN_DWELL_MS = 800;
const TARGET_READ_MS_PER_CHAR = 45; // ~ reading pace for scoring

/** @typedef {{ weights: Record<string, number>, seen: string[], history: Array<{id:string,dwellMs:number,signal:number,at:number}>, version: number }} Profile */

/** @returns {Profile} */
export function loadProfile() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyProfile();
    const p = JSON.parse(raw);
    if (!p || typeof p !== "object") return emptyProfile();
    return {
      weights: p.weights && typeof p.weights === "object" ? p.weights : {},
      seen: Array.isArray(p.seen) ? p.seen.slice(-800) : [],
      history: Array.isArray(p.history) ? p.history.slice(-200) : [],
      version: 1,
    };
  } catch {
    return emptyProfile();
  }
}

function emptyProfile() {
  return { weights: {}, seen: [], history: [], version: 1 };
}

/** @param {Profile} profile */
export function saveProfile(profile) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      weights: profile.weights,
      seen: profile.seen.slice(-800),
      history: profile.history.slice(-200),
      version: 1,
    }));
  } catch {
    /* quota / private mode */
  }
}

export function clearProfile() {
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* */ }
}

/**
 * Reading-time signal in [-1, 1.5]: short skips pull down, lingering pulls up.
 * @param {number} dwellMs
 * @param {number} charCount
 */
export function dwellSignal(dwellMs, charCount) {
  const expected = Math.max(2500, Math.min(45000, charCount * TARGET_READ_MS_PER_CHAR));
  const ratio = dwellMs / expected;
  if (dwellMs < MIN_DWELL_MS) return -0.15;
  if (ratio < 0.15) return -0.35; // bounce
  if (ratio < 0.35) return 0.05;
  if (ratio < 0.7) return 0.45;
  if (ratio < 1.2) return 0.9;
  return 1.25; // deep read
}

/**
 * @param {Profile} profile
 * @param {Record<string, number>} features
 * @param {number} delta  signed update strength
 */
export function updateWeights(profile, features, delta) {
  if (!features || !delta) return;
  for (const [k, v] of Object.entries(features)) {
    const w = (profile.weights[k] || 0) + delta * v;
    if (Math.abs(w) < 0.02) delete profile.weights[k];
    else profile.weights[k] = Math.max(-8, Math.min(8, w));
  }
}

/**
 * @param {Profile} profile
 * @param {{ id: string, features: Record<string, number>, charCount: number }} dream
 * @param {{ dwellMs: number, explicit?: -1 | 0 | 1 }} engagement
 */
export function recordEngagement(profile, dream, engagement) {
  const dwellMs = Math.max(0, engagement.dwellMs || 0);
  const explicit = engagement.explicit || 0;
  const fromDwell = dwellSignal(dwellMs, dream.charCount || 200) * DWELL_WEIGHT;
  const fromExplicit = explicit * EXPLICIT_WEIGHT;
  const signal = fromDwell + fromExplicit;

  updateWeights(profile, dream.features || {}, signal * 0.35);

  if (!profile.seen.includes(dream.id)) profile.seen.push(dream.id);
  profile.history.push({
    id: dream.id,
    dwellMs: Math.round(dwellMs),
    signal: Number(signal.toFixed(3)),
    at: Date.now(),
  });
  if (profile.history.length > 200) profile.history = profile.history.slice(-200);
  if (profile.seen.length > 800) profile.seen = profile.seen.slice(-800);

  saveProfile(profile);
  return signal;
}

/** Cosine similarity between sparse maps */
export function cosine(a, b) {
  const keys = Object.keys(a);
  if (!keys.length || !Object.keys(b).length) return 0;
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (const k of keys) {
    const av = a[k] || 0;
    na += av * av;
    const bv = b[k] || 0;
    if (bv) dot += av * bv;
  }
  for (const v of Object.values(b)) nb += v * v;
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

/**
 * Pick next unseen dream: epsilon-greedy over similarity to preference weights.
 * @param {Profile} profile
 * @param {Array<{id:string, features: Record<string, number>}>} pool
 * @param {{ epsilon?: number, rng?: () => number }} [opts]
 */
export function pickNext(profile, pool, opts = {}) {
  const epsilon = opts.epsilon ?? EPSILON;
  const rng = opts.rng || Math.random;
  const seen = new Set(profile.seen);
  const unseen = pool.filter((d) => !seen.has(d.id));
  if (!unseen.length) return null;

  const explore = rng() < epsilon || Object.keys(profile.weights).length < 2;
  if (explore) {
    return unseen[Math.floor(rng() * unseen.length)];
  }

  let best = unseen[0];
  let bestScore = -Infinity;
  // mild noise so ties break naturally
  for (const d of unseen) {
    const sim = cosine(profile.weights, d.features || {});
    const noise = (rng() - 0.5) * 0.04;
    const score = sim + noise;
    if (score > bestScore) {
      bestScore = score;
      best = d;
    }
  }
  return best;
}

export function profileSummary(profile) {
  const entries = Object.entries(profile.weights)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 5);
  if (!entries.length) return "perfil vazio · explorar";
  return entries
    .map(([k, v]) => `${k.replace(/^(place|mood|sym|pol|mot|lex):/, "")} ${v >= 0 ? "+" : ""}${v.toFixed(1)}`)
    .join(" · ");
}
