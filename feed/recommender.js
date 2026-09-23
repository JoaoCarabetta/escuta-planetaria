/**
 * Client-side recommender v2 — preference from dwell + likes (localStorage).
 * Epsilon-greedy over cosine similarity to a local profile.
 */

const STORAGE_KEY = "escuta.feed.profile.v1";
const LIKES_KEY = "escuta.feed.likes.v1";
const EPSILON = 0.18;
const DWELL_WEIGHT = 1.0;
const LIKE_WEIGHT = 3.6; // stronger than dwell; replaces old mais/menos
const MIN_DWELL_MS = 800;
const TARGET_READ_MS_PER_CHAR = 45;

/** @typedef {{ weights: Record<string, number>, seen: string[], history: Array<{id:string,dwellMs:number,signal:number,at:number,kind?:string}>, version: number }} Profile */

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
  try { localStorage.removeItem(LIKES_KEY); } catch { /* */ }
}

/** @returns {Set<string>} */
export function loadLikes() {
  try {
    const raw = localStorage.getItem(LIKES_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    return new Set(Array.isArray(arr) ? arr.filter((x) => typeof x === "string") : []);
  } catch {
    return new Set();
  }
}

/** @param {Set<string>} likes */
export function saveLikes(likes) {
  try {
    localStorage.setItem(LIKES_KEY, JSON.stringify([...likes].slice(-2000)));
  } catch {
    /* */
  }
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
  if (ratio < 0.15) return -0.35;
  if (ratio < 0.35) return 0.05;
  if (ratio < 0.7) return 0.45;
  if (ratio < 1.2) return 0.9;
  return 1.25;
}

/**
 * @param {Profile} profile
 * @param {Record<string, number>} features
 * @param {number} delta
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
 * @param {{ dwellMs: number, explicit?: -1 | 0 | 1, like?: boolean }} engagement
 */
export function recordEngagement(profile, dream, engagement) {
  const dwellMs = Math.max(0, engagement.dwellMs || 0);
  const explicit = engagement.explicit || 0;
  const fromDwell = dwellSignal(dwellMs, dream.charCount || 200) * DWELL_WEIGHT;
  // explicit kept for back-compat; likes use recordLike
  const fromExplicit = explicit * LIKE_WEIGHT * 0.66;
  const signal = fromDwell + fromExplicit;

  updateWeights(profile, dream.features || {}, signal * 0.35);

  if (!profile.seen.includes(dream.id)) profile.seen.push(dream.id);
  profile.history.push({
    id: dream.id,
    dwellMs: Math.round(dwellMs),
    signal: Number(signal.toFixed(3)),
    at: Date.now(),
    kind: "dwell",
  });
  if (profile.history.length > 200) profile.history = profile.history.slice(-200);
  if (profile.seen.length > 800) profile.seen = profile.seen.slice(-800);

  saveProfile(profile);
  return signal;
}

/**
 * Strong preference update from like / unlike.
 * @param {Profile} profile
 * @param {{ id: string, features: Record<string, number> }} dream
 * @param {boolean} liked  true = like on, false = unlike (reverts)
 */
export function recordLike(profile, dream, liked) {
  const delta = (liked ? 1 : -1) * LIKE_WEIGHT * 0.45;
  updateWeights(profile, dream.features || {}, delta);
  if (!profile.seen.includes(dream.id)) profile.seen.push(dream.id);
  profile.history.push({
    id: dream.id,
    dwellMs: 0,
    signal: Number((liked ? LIKE_WEIGHT : -LIKE_WEIGHT).toFixed(3)),
    at: Date.now(),
    kind: liked ? "like" : "unlike",
  });
  if (profile.history.length > 200) profile.history = profile.history.slice(-200);
  saveProfile(profile);
  return delta;
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
 * @param {{ epsilon?: number, rng?: () => number, exclude?: Set<string> }} [opts]
 */
export function pickNext(profile, pool, opts = {}) {
  const epsilon = opts.epsilon ?? EPSILON;
  const rng = opts.rng || Math.random;
  const seen = new Set(profile.seen);
  if (opts.exclude) {
    for (const id of opts.exclude) seen.add(id);
  }
  const unseen = pool.filter((d) => !seen.has(d.id));
  if (!unseen.length) return null;

  const explore = rng() < epsilon || Object.keys(profile.weights).length < 2;
  if (explore) {
    return unseen[Math.floor(rng() * unseen.length)];
  }

  let best = unseen[0];
  let bestScore = -Infinity;
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

/**
 * Append a batch of recommended dreams for infinite scroll.
 * @param {Profile} profile
 * @param {Array<{id:string, features: Record<string, number>}>} pool
 * @param {number} n
 * @param {{ exclude?: Set<string> }} [opts]
 */
export function pickBatch(profile, pool, n, opts = {}) {
  const out = [];
  const exclude = new Set(opts.exclude || []);
  for (let i = 0; i < n; i++) {
    const next = pickNext(profile, pool, { exclude });
    if (!next) break;
    out.push(next);
    exclude.add(next.id);
  }
  return out;
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
