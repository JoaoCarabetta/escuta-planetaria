/**
 * laboratório · feed — infinite social scroll + like + dwell recommender.
 */
import {
  loadProfile,
  saveProfile,
  recordEngagement,
  recordLike,
  pickBatch,
  profileSummary,
  clearProfile,
  loadLikes,
  saveLikes,
} from "./recommender.js";

const $ = (sel) => document.querySelector(sel);

const streamEl = $("#stream");
const sentinelEl = $("#sentinel");
const vazioEl = $("#vazio");
const errEl = $("#err");
const loadingEl = $("#loading");
const statusEl = $("#status");
const metaNota = $("#meta-nota");
const btnIr = $("#btn-ir");
const btnVoltar = $("#btn-voltar");

const BATCH = 6;
const PREFETCH_PX = 900;

/** @type {Array<object>} */
let pool = [];
let profile = loadProfile();
/** @type {Set<string>} */
let likes = loadLikes();

/** @type {Map<string, { el: HTMLElement, dream: object, dwellAccumMs: number, dwellSegmentStart: number, visible: boolean, flushed: boolean }>} */
const cards = new Map();
/** @type {string[]} ordered dream ids in the stream */
const order = [];
/** ids already in stream */
const inStream = new Set();

let pageVisible = document.visibilityState === "visible";
let appending = false;
let focusIndex = 0;

function setStatus(msg) {
  statusEl.textContent = msg || "";
}

function updateMeta() {
  metaNota.textContent = `${order.length} no feed · ${likes.size} curtidos · ${pool.length} pool`;
}

function isDwellActive(state) {
  return state.visible && pageVisible;
}

function pauseDwell(state) {
  if (state.dwellSegmentStart) {
    state.dwellAccumMs += performance.now() - state.dwellSegmentStart;
    state.dwellSegmentStart = 0;
  }
}

function resumeDwell(state) {
  if (isDwellActive(state) && !state.dwellSegmentStart) {
    state.dwellSegmentStart = performance.now();
  }
}

function currentDwellMs(state) {
  let ms = state.dwellAccumMs;
  if (state.dwellSegmentStart) ms += performance.now() - state.dwellSegmentStart;
  return ms;
}

function flushDwell(state) {
  if (state.flushed) return;
  pauseDwell(state);
  const dwellMs = currentDwellMs(state);
  const signal = recordEngagement(profile, state.dream, { dwellMs });
  state.flushed = true;
  state.dwellAccumMs = 0;
  const sec = (dwellMs / 1000).toFixed(1);
  setStatus(`dwell ${sec}s · ${signal >= 0 ? "+" : ""}${signal.toFixed(2)} · ${profileSummary(profile)}`);
  updateMeta();
}

function renderTags(dream) {
  const bits = [];
  const seen = new Set();
  const add = (label, cls = "pill") => {
    if (!label || seen.has(label)) return;
    seen.add(label);
    bits.push(`<span class="${cls}">${label}</span>`);
  };
  if (dream.mood) add(dream.mood, `pill mood-${dream.mood}`);
  add(dream.place);
  for (const s of (dream.symbols || []).slice(0, 3)) add(s);
  return bits.length ? bits.join("") : "";
}

function heartSvg() {
  return `<svg class="heart-icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 21s-6.7-4.35-9.33-8.1C.5 9.7 1.1 5.9 4.4 4.2c1.9-1 4.2-.55 5.6 1.05C11.4 3.65 13.7 3.2 15.6 4.2c3.3 1.7 3.9 5.5 1.73 8.7C18.7 16.65 12 21 12 21z"/></svg>`;
}

function createCard(dream) {
  const article = document.createElement("article");
  article.className = "card entering";
  article.dataset.id = dream.id;
  article.dataset.visible = "false";
  article.setAttribute("role", "article");

  const liked = likes.has(dream.id);
  const tags = renderTags(dream);

  article.innerHTML = `
    ${tags ? `<p class="tags">${tags}</p>` : ""}
    <div class="texto-wrap">
      <p class="texto"></p>
    </div>
    <div class="card-bar">
      <button type="button" class="btn-like${liked ? " liked" : ""}" aria-pressed="${liked}" aria-label="${liked ? "Remover curtida" : "Curtir"}" title="Curtir">
        ${heartSvg()}
        <span class="like-label">${liked ? "curtido" : "curtir"}</span>
      </button>
    </div>
  `;
  article.querySelector(".texto").textContent = dream.text;

  const likeBtn = article.querySelector(".btn-like");
  likeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleLike(dream, likeBtn);
  });

  const state = {
    el: article,
    dream,
    dwellAccumMs: 0,
    dwellSegmentStart: 0,
    visible: false,
    flushed: false,
  };
  cards.set(dream.id, state);
  order.push(dream.id);
  inStream.add(dream.id);

  streamEl.appendChild(article);
  requestAnimationFrame(() => article.classList.remove("entering"));
  io.observe(article);
  return state;
}

function toggleLike(dream, btn) {
  const wasLiked = likes.has(dream.id);
  if (wasLiked) {
    likes.delete(dream.id);
    recordLike(profile, dream, false);
  } else {
    likes.add(dream.id);
    recordLike(profile, dream, true);
  }
  saveLikes(likes);
  const liked = likes.has(dream.id);
  btn.classList.toggle("liked", liked);
  btn.setAttribute("aria-pressed", String(liked));
  btn.setAttribute("aria-label", liked ? "Remover curtida" : "Curtir");
  const label = btn.querySelector(".like-label");
  if (label) label.textContent = liked ? "curtido" : "curtir";
  btn.classList.add("flash-like");
  setTimeout(() => btn.classList.remove("flash-like"), 320);
  setStatus(`${liked ? "♥ curtido" : "curtir removido"} · ${profileSummary(profile)}`);
  updateMeta();
}

function appendBatch(n = BATCH) {
  if (appending) return 0;
  appending = true;
  loadingEl.hidden = false;
  streamEl.setAttribute("aria-busy", "true");

  const batch = pickBatch(profile, pool, n, { exclude: inStream });
  for (const dream of batch) {
    if (!profile.seen.includes(dream.id)) {
      profile.seen.push(dream.id);
    }
    createCard(dream);
  }
  saveProfile(profile);

  appending = false;
  loadingEl.hidden = true;
  streamEl.setAttribute("aria-busy", "false");

  if (!batch.length) {
    vazioEl.hidden = false;
    setStatus("pool esgotado — ? limpa perfil");
  } else {
    vazioEl.hidden = true;
  }
  updateMeta();
  setStatus(profileSummary(profile));
  return batch.length;
}

const io = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      const id = entry.target.dataset.id;
      const state = cards.get(id);
      if (!state) continue;
      const nowVisible = entry.isIntersecting && entry.intersectionRatio >= 0.45;
      if (nowVisible === state.visible) continue;
      if (state.visible && !nowVisible) {
        flushDwell(state);
      }
      state.visible = nowVisible;
      entry.target.dataset.visible = nowVisible ? "true" : "false";
      if (nowVisible) {
        if (state.flushed) {
          state.flushed = false;
          state.dwellAccumMs = 0;
        }
        resumeDwell(state);
        const idx = order.indexOf(id);
        if (idx >= 0) focusIndex = idx;
      } else {
        pauseDwell(state);
      }
    }
  },
  { threshold: [0, 0.45, 0.75, 1], rootMargin: "0px" },
);

const infiniteIo = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) appendBatch();
    }
  },
  { rootMargin: `${PREFETCH_PX}px 0px` },
);

function scrollToIndex(idx, behavior = "smooth") {
  if (idx < 0 || idx >= order.length) return;
  focusIndex = idx;
  const state = cards.get(order[idx]);
  if (!state) return;
  state.el.scrollIntoView({ behavior, block: "center" });
}

function onIr() {
  if (focusIndex >= order.length - 2) appendBatch();
  const next = Math.min(focusIndex + 1, order.length - 1);
  if (next === focusIndex && focusIndex === order.length - 1) {
    const added = appendBatch();
    if (added) scrollToIndex(focusIndex + 1);
    return;
  }
  scrollToIndex(next);
}

function onVoltar() {
  scrollToIndex(Math.max(0, focusIndex - 1));
}

btnIr.addEventListener("click", onIr);
btnVoltar.addEventListener("click", onVoltar);

window.addEventListener("keydown", (e) => {
  if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
  if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter" || e.key === "j" || e.key === "J") {
    e.preventDefault();
    onIr();
  } else if (e.key === "ArrowLeft" || e.key === "k" || e.key === "K") {
    e.preventDefault();
    onVoltar();
  } else if (e.key === "l" || e.key === "L") {
    e.preventDefault();
    const id = order[focusIndex];
    const state = id && cards.get(id);
    if (state) {
      const btn = state.el.querySelector(".btn-like");
      if (btn) toggleLike(state.dream, btn);
    }
  } else if (e.key === "?" || (e.shiftKey && e.key === "/")) {
    e.preventDefault();
    if (confirm("Limpar perfil do feed (preferências + vistos + curtidas)?")) {
      clearProfile();
      profile = loadProfile();
      likes = loadLikes();
      for (const state of cards.values()) io.unobserve(state.el);
      streamEl.innerHTML = "";
      cards.clear();
      order.length = 0;
      inStream.clear();
      focusIndex = 0;
      vazioEl.hidden = true;
      appendBatch(BATCH);
      appendBatch(BATCH);
    }
  }
});

document.addEventListener("visibilitychange", () => {
  pageVisible = document.visibilityState === "visible";
  for (const state of cards.values()) {
    if (pageVisible) resumeDwell(state);
    else {
      pauseDwell(state);
      if (state.visible && !state.flushed) flushDwell(state);
    }
  }
});

window.addEventListener("blur", () => {
  for (const state of cards.values()) pauseDwell(state);
});
window.addEventListener("focus", () => {
  pageVisible = document.visibilityState === "visible";
  for (const state of cards.values()) resumeDwell(state);
});

window.addEventListener("beforeunload", () => {
  for (const state of cards.values()) {
    if (state.visible && !state.flushed) flushDwell(state);
  }
});

async function boot() {
  try {
    const res = await fetch("./sonhos.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    pool = await res.json();
    if (!Array.isArray(pool) || !pool.length) throw new Error("pool vazio");
    infiniteIo.observe(sentinelEl);
    appendBatch(BATCH);
    if (order.length < pool.length) appendBatch(BATCH);
  } catch (err) {
    errEl.hidden = false;
    errEl.textContent = `falha ao carregar sonhos.json — ${err.message || err}`;
    setStatus("erro");
  }
}

boot();
