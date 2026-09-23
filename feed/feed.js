/**
 * laboratório · feed — one-dream-at-a-time with reading-time recommender.
 */
import {
  loadProfile,
  recordEngagement,
  pickNext,
  profileSummary,
  clearProfile,
} from "./recommender.js";

const $ = (sel) => document.querySelector(sel);

const cardEl = $("#dream-card");
const textoEl = $("#texto");
const textoWrap = $("#texto-wrap");
const tagsEl = $("#tags");
const vazioEl = $("#vazio");
const errEl = $("#err");
const statusEl = $("#status");
const metaNota = $("#meta-nota");
const btnMais = $("#btn-mais");
const btnMenos = $("#btn-menos");
const btnPular = $("#btn-pular");
const btnProximo = $("#btn-proximo");

/** @type {Array<object>} */
let pool = [];
let profile = loadProfile();
/** @type {object | null} */
let current = null;

/** dwell tracking */
let dwellAccumMs = 0;
let dwellSegmentStart = 0;
let isIntersecting = false;
let pageVisible = document.visibilityState === "visible";
let explicitPending = 0; // -1 | 0 | 1 applied on advance
let scrollCooldown = false;

function setStatus(msg) {
  statusEl.textContent = msg || "";
}

function flash(btn, cls) {
  btn.classList.add(cls);
  setTimeout(() => btn.classList.remove(cls), 280);
}

function isDwellActive() {
  return isIntersecting && pageVisible && !!current;
}

function pauseDwell() {
  if (dwellSegmentStart) {
    dwellAccumMs += performance.now() - dwellSegmentStart;
    dwellSegmentStart = 0;
  }
}

function resumeDwell() {
  if (isDwellActive() && !dwellSegmentStart) {
    dwellSegmentStart = performance.now();
  }
}

function resetDwell() {
  pauseDwell();
  dwellAccumMs = 0;
  dwellSegmentStart = 0;
  explicitPending = 0;
}

function currentDwellMs() {
  let ms = dwellAccumMs;
  if (dwellSegmentStart) ms += performance.now() - dwellSegmentStart;
  return ms;
}

function renderTags(dream) {
  const bits = [];
  if (dream.mood) bits.push(`<span class="pill mood-${dream.mood}">${dream.mood}</span>`);
  if (dream.place) bits.push(`<span class="pill">${dream.place}</span>`);
  for (const s of (dream.symbols || []).slice(0, 3)) {
    bits.push(`<span class="pill">${s}</span>`);
  }
  if (!bits.length) {
    tagsEl.hidden = true;
    tagsEl.innerHTML = "";
    return;
  }
  tagsEl.hidden = false;
  tagsEl.innerHTML = bits.join("");
}

function showDream(dream) {
  current = dream;
  resetDwell();
  vazioEl.hidden = true;
  errEl.hidden = true;
  textoWrap.hidden = false;
  textoEl.textContent = dream.text;
  renderTags(dream);
  cardEl.classList.remove("entering");
  // reflow for animation
  void cardEl.offsetWidth;
  cardEl.classList.add("entering");
  textoWrap.scrollTop = 0;
  metaNota.textContent = `${profile.seen.length} vistos · ${pool.length} no pool`;
  setStatus(profileSummary(profile));
  resumeDwell();
}

function finishCurrent() {
  if (!current) return;
  pauseDwell();
  const dwellMs = currentDwellMs();
  const signal = recordEngagement(profile, current, {
    dwellMs,
    explicit: explicitPending,
  });
  const sec = (dwellMs / 1000).toFixed(1);
  setStatus(`dwell ${sec}s · sinal ${signal >= 0 ? "+" : ""}${signal.toFixed(2)} · ${profileSummary(profile)}`);
}

function advance({ skipBoost = false } = {}) {
  if (current) {
    if (skipBoost && !explicitPending && currentDwellMs() < 1200) {
      // treat very fast skip as mild negative without overriding explicit
      explicitPending = 0;
    }
    finishCurrent();
  }
  const next = pickNext(profile, pool);
  if (!next) {
    current = null;
    textoWrap.hidden = true;
    tagsEl.hidden = true;
    vazioEl.hidden = false;
    metaNota.textContent = `${pool.length} vistos · pool esgotado`;
    setStatus("pool esgotado — ? limpa perfil");
    return;
  }
  showDream(next);
}

function onMais() {
  explicitPending = 1;
  flash(btnMais, "flash-mais");
  advance();
}

function onMenos() {
  explicitPending = -1;
  flash(btnMenos, "flash-menos");
  advance();
}

function onPular() {
  advance({ skipBoost: true });
}

function onProximo() {
  advance();
}

btnMais.addEventListener("click", onMais);
btnMenos.addEventListener("click", onMenos);
btnPular.addEventListener("click", onPular);
btnProximo.addEventListener("click", onProximo);

window.addEventListener("keydown", (e) => {
  if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
  if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") {
    e.preventDefault();
    onProximo();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    onMais();
  } else if (e.key === "ArrowDown") {
    e.preventDefault();
    onMenos();
  } else if (e.key === "?" || (e.shiftKey && e.key === "/")) {
    e.preventDefault();
    if (confirm("Limpar perfil do feed (preferências + vistos)?")) {
      clearProfile();
      profile = loadProfile();
      advance();
    }
  }
});

/** Optional scroll-to-advance when at bottom of text */
textoWrap.addEventListener(
  "wheel",
  (e) => {
    if (!current || scrollCooldown) return;
    const atBottom =
      textoWrap.scrollHeight - textoWrap.scrollTop - textoWrap.clientHeight < 8;
    const atTop = textoWrap.scrollTop < 4;
    if (e.deltaY > 28 && atBottom) {
      scrollCooldown = true;
      onProximo();
      setTimeout(() => { scrollCooldown = false; }, 650);
    } else if (e.deltaY < -40 && atTop && e.shiftKey) {
      // shift+scroll up = mais
      scrollCooldown = true;
      onMais();
      setTimeout(() => { scrollCooldown = false; }, 650);
    }
  },
  { passive: true },
);

const io = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      isIntersecting = entry.isIntersecting && entry.intersectionRatio >= 0.45;
      cardEl.dataset.visible = isIntersecting ? "true" : "false";
      if (isIntersecting) resumeDwell();
      else pauseDwell();
    }
  },
  { threshold: [0, 0.45, 0.75, 1] },
);
io.observe(cardEl);

document.addEventListener("visibilitychange", () => {
  pageVisible = document.visibilityState === "visible";
  if (pageVisible) resumeDwell();
  else pauseDwell();
});

window.addEventListener("blur", pauseDwell);
window.addEventListener("focus", () => {
  pageVisible = document.visibilityState === "visible";
  resumeDwell();
});

async function boot() {
  try {
    const res = await fetch("./sonhos.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    pool = await res.json();
    if (!Array.isArray(pool) || !pool.length) throw new Error("pool vazio");
    metaNota.textContent = `${profile.seen.length} vistos · ${pool.length} no pool`;
    advance();
  } catch (err) {
    errEl.hidden = false;
    errEl.textContent = `falha ao carregar sonhos.json — ${err.message || err}`;
    setStatus("erro");
  }
}

boot();
