/**
 * laboratório · experimento #1
 * Dream text → client-side knobs → deterministic canvas collage.
 * No secrets; no third-party LLM in v1.
 */

const COLORS = {
  vazio: "#05060b",
  sonho: "#6ba8ff",
  desejo: "#ffbe5c",
  sofrer: "#ff6376",
  texto: "#c6c9d6",
  fraco: "#6f7488",
};

const SYMBOL_VOCAB = [
  "água", "queda", "casa", "dente", "perseguidor", "voo", "ex", "morte",
  "escola", "porta", "escada", "animal", "criança", "espelho", "fogo", "cidade",
];

const PLACE_RULES = [
  { place: "água", keys: ["mar", "rio", "lago", "água", "água", "piscina", "afog", "chuva", "onda", "praia"] },
  { place: "doméstico", keys: ["casa", "quarto", "cozinha", "sala", "apartamento", "porta", "janela", "cama", "banheiro"] },
  { place: "cidade", keys: ["rua", "cidade", "prédio", "ônibus", "carro", "avenida", "metrô", "metro", "shopping"] },
  { place: "escola", keys: ["escola", "faculdade", "sala de aula", "prova", "professor", "coleg"] },
  { place: "natureza", keys: ["floresta", "mata", "campo", "montanha", "árvore", "arvore", "jardim", "céu", "ceu"] },
  { place: "liminar", keys: ["corredor", "escada", "elevador", "túnel", "tunel", "ponte", "entre", "limiar"] },
];

const SYMBOL_RULES = [
  { tag: "água", keys: ["água", "agua", "mar", "rio", "afog", "nado", "natação", "chuva"] },
  { tag: "queda", keys: ["caí", "cai", "queda", "caindo", "desci", "precipício", "precipicio"] },
  { tag: "casa", keys: ["casa", "quarto", "lar", "apartamento"] },
  { tag: "dente", keys: ["dente", "dentes", "boca"] },
  { tag: "perseguidor", keys: ["persegui", "fugindo", "correr", "corría", "corria", "caça", "caca", "assombra"] },
  { tag: "voo", keys: ["voar", "voando", "voa", "voo", "asas", "fantasma"] },
  { tag: "ex", keys: ["ex ", "ex-", "namorad", "ex-namor"] },
  { tag: "morte", keys: ["morr", "morte", "morto", "cadáver", "cadaver", "funeral", "cemitério", "cemiterio"] },
  { tag: "escola", keys: ["escola", "prova", "professor", "aula"] },
  { tag: "porta", keys: ["porta", "portão", "portao"] },
  { tag: "escada", keys: ["escada", "degrau"] },
  { tag: "animal", keys: ["cachorro", "gato", "cobra", "pássaro", "passaro", "lobo", "animal", "bicho"] },
  { tag: "criança", keys: ["criança", "crianca", "filho", "filha", "bebê", "bebe"] },
  { tag: "espelho", keys: ["espelho", "reflexo"] },
  { tag: "fogo", keys: ["fogo", "queim", "incêndio", "incendio", "chama"] },
  { tag: "cidade", keys: ["cidade", "rua", "prédio", "predio"] },
];

const MOOD_RULES = [
  { mood: "dread", keys: ["medo", "assust", "pesadelo", "terror", "pavor", "horror", "macabro", "gritei"], accent: "sofrer" },
  { mood: "longing", keys: ["saudade", "ex", "voltar", "juntos", "amor", "beij", "abraç", "abrac"], accent: "desejo" },
  { mood: "wonder", keys: ["lúcido", "lucido", "mágico", "magico", "voar", "luz", "estrel", "céu", "ceu"], accent: "sonho" },
  { mood: "shame", keys: ["vergonha", "nu ", "nua", "exposto", "constrang"], accent: "sofrer" },
  { mood: "joy", keys: ["feliz", "alegria", "rindo", "festa", "riso"], accent: "desejo" },
  { mood: "calm", keys: ["calmo", "tranquilo", "paz", "silêncio", "silencio", "suave"], accent: "sonho" },
  { mood: "numb", keys: ["vazio", "nada", "preto", "escuro", "sem sentir"], accent: "sonho" },
];

const $ = (sel) => document.querySelector(sel);

const relatoEl = $("#relato");
const knobsEl = $("#knobs");
const statusEl = $("#status");
const canvas = $("#colagem");
const ctx = canvas.getContext("2d");
const hintEl = $("#vazio-hint");
const tituloEl = $("#titulo-linha");
const wrapEl = document.querySelector(".canvas-wrap");

let pool = [];
let lastUsedId = null;
let animId = null;
let currentKnobs = null;
let t0 = performance.now();

function setStatus(msg) {
  statusEl.textContent = msg || "";
}

function titleFromText(text) {
  const words = text.trim().split(/\s+/).filter(Boolean).slice(0, 8);
  return words.join(" ") + (text.trim().split(/\s+/).length > 8 ? "…" : "");
}

function countHits(low, keys) {
  let n = 0;
  for (const k of keys) {
    if (low.includes(k)) n += 1;
  }
  return n;
}

/** Client-side ShapeShift-style mock: typed knobs from keyword heuristics. */
function extractKnobs(text) {
  const raw = (text || "").trim();
  const low = raw.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");
  const lowRaw = raw.toLowerCase();

  let place = "sem-lugar";
  let placeScore = 0;
  for (const rule of PLACE_RULES) {
    const s = countHits(low, rule.keys.map((k) => k.normalize("NFD").replace(/\p{M}/gu, "")));
    if (s > placeScore) {
      placeScore = s;
      place = rule.place;
    }
  }

  const symbolHits = SYMBOL_RULES
    .map((rule) => ({
      tag: rule.tag,
      score: countHits(low, rule.keys.map((k) => k.normalize("NFD").replace(/\p{M}/gu, ""))),
    }))
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);

  const symbols = symbolHits.slice(0, 3).map((x) => x.tag);
  if (symbols.length === 0) symbols.push("porta");

  let mood = "numb";
  let accent = "sonho";
  let moodScore = 0;
  for (const rule of MOOD_RULES) {
    const s = countHits(low, rule.keys.map((k) => k.normalize("NFD").replace(/\p{M}/gu, "")));
    if (s > moodScore) {
      moodScore = s;
      mood = rule.mood;
      accent = rule.accent;
    }
  }

  // fear ← → desire polarity (0 fear … 2 desire)
  const fearKeys = ["medo", "fuga", "morte", "pesadelo", "persegui", "queda", "afog"];
  const desireKeys = ["amor", "beij", "juntos", "desejo", "quero", "saudade", "ex"];
  const fearN = countHits(low, fearKeys);
  const desireN = countHits(low, desireKeys);
  let polarity = 1;
  if (fearN + desireN > 0) {
    polarity = Math.max(0, Math.min(2, 1 + (desireN - fearN) * 0.45));
  }
  if (mood === "dread" || mood === "shame") polarity = Math.min(polarity, 0.55);
  if (mood === "longing" || mood === "joy") polarity = Math.max(polarity, 1.35);

  const motionKeys = ["correndo", "correr", "fugindo", "caindo", "voando", "trem", "rápido", "rapido", "gritei", "chaos", "caos"];
  const stillKeys = ["parado", "olhando", "sentado", "deitado", "silêncio", "silencio", "espera"];
  const motionRaw = 0.35 + countHits(low, motionKeys) * 0.28 - countHits(low, stillKeys) * 0.15;
  const motion = Math.max(0, Math.min(1, motionRaw));

  let colorMood = "dark";
  if (polarity >= 1.4) colorMood = "warm";
  else if (polarity <= 0.6) colorMood = "cool";
  else if (mood === "wonder") colorMood = "vivid";

  const readiness = Math.max(
    0.15,
    Math.min(1, raw.length / 280 + symbols.length * 0.08 + (place !== "sem-lugar" ? 0.12 : 0)),
  );

  const visualGenre = mood === "dread" || mood === "shame"
    ? "collage-harsh"
    : polarity > 1.3
      ? "postcard-warm"
      : "spectral-field";

  return {
    visualGenre,
    mood,
    accent,
    polarity: Number(polarity.toFixed(2)),
    symbols,
    place,
    colorMood,
    motion: Number(motion.toFixed(2)),
    readiness: Number(readiness.toFixed(2)),
    title: titleFromText(raw),
    charCount: raw.length,
    vocab: SYMBOL_VOCAB,
  };
}

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

function accentHex(name) {
  if (name === "desejo") return COLORS.desejo;
  if (name === "sofrer") return COLORS.sofrer;
  return COLORS.sonho;
}

function placePlate(ctx, w, h, place, accent, polarity) {
  const a = hexToRgb(accent);
  ctx.fillStyle = COLORS.vazio;
  ctx.fillRect(0, 0, w, h);

  const g = ctx.createRadialGradient(w * 0.55, h * 0.4, 20, w * 0.5, h * 0.5, w * 0.7);
  if (place === "água") {
    g.addColorStop(0, `rgba(${a.r},${a.g},${a.b},0.18)`);
    g.addColorStop(0.45, "rgba(20,40,80,0.55)");
    g.addColorStop(1, COLORS.vazio);
  } else if (place === "doméstico") {
    g.addColorStop(0, `rgba(${a.r},${a.g},${a.b},0.12)`);
    g.addColorStop(0.5, "rgba(30,28,40,0.7)");
    g.addColorStop(1, COLORS.vazio);
  } else if (place === "cidade") {
    g.addColorStop(0, "rgba(40,48,70,0.5)");
    g.addColorStop(1, COLORS.vazio);
  } else if (place === "natureza") {
    g.addColorStop(0, `rgba(${Math.min(255, a.r)},${a.g + 20},${a.b},0.1)`);
    g.addColorStop(0.6, "rgba(18,32,28,0.65)");
    g.addColorStop(1, COLORS.vazio);
  } else if (place === "liminar" || place === "escola") {
    g.addColorStop(0, "rgba(50,55,80,0.35)");
    g.addColorStop(1, COLORS.vazio);
  } else {
    g.addColorStop(0, `rgba(${a.r},${a.g},${a.b},${0.06 + polarity * 0.04})`);
    g.addColorStop(1, COLORS.vazio);
  }
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, w, h);

  // horizon / architecture hints
  ctx.strokeStyle = `rgba(${a.r},${a.g},${a.b},0.22)`;
  ctx.lineWidth = 1;
  if (place === "água") {
    for (let i = 0; i < 5; i++) {
      const y = h * 0.55 + i * 18;
      ctx.beginPath();
      for (let x = 0; x <= w; x += 12) {
        const yy = y + Math.sin(x * 0.02 + i) * (4 + i);
        if (x === 0) ctx.moveTo(x, yy);
        else ctx.lineTo(x, yy);
      }
      ctx.stroke();
    }
  } else if (place === "cidade") {
    ctx.fillStyle = "rgba(12,14,22,0.85)";
    for (let i = 0; i < 9; i++) {
      const bw = 40 + (i * 37) % 50;
      const bh = 80 + (i * 53) % 160;
      const bx = 30 + i * 95;
      ctx.fillRect(bx, h - bh - 40, bw, bh);
      ctx.strokeRect(bx, h - bh - 40, bw, bh);
    }
  } else if (place === "doméstico") {
    ctx.strokeRect(w * 0.22, h * 0.28, w * 0.56, h * 0.48);
    ctx.beginPath();
    ctx.moveTo(w * 0.22, h * 0.28);
    ctx.lineTo(w * 0.5, h * 0.14);
    ctx.lineTo(w * 0.78, h * 0.28);
    ctx.stroke();
  } else if (place === "liminar") {
    ctx.beginPath();
    ctx.moveTo(w * 0.5, h * 0.1);
    ctx.lineTo(w * 0.5, h * 0.9);
    ctx.stroke();
    for (let i = 0; i < 6; i++) {
      const y = h * 0.2 + i * 60;
      ctx.beginPath();
      ctx.moveTo(w * 0.35, y);
      ctx.lineTo(w * 0.65, y + 10);
      ctx.stroke();
    }
  }
}

function drawSymbol(ctx, tag, x, y, size, accent, seed) {
  const a = hexToRgb(accent);
  ctx.save();
  ctx.translate(x, y);
  ctx.strokeStyle = `rgba(${a.r},${a.g},${a.b},0.85)`;
  ctx.fillStyle = `rgba(${a.r},${a.g},${a.b},0.12)`;
  ctx.lineWidth = 1.5;

  if (tag === "água") {
    ctx.beginPath();
    ctx.arc(0, 0, size * 0.45, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-size * 0.4, size * 0.1);
    ctx.quadraticCurveTo(0, size * 0.45, size * 0.4, size * 0.1);
    ctx.stroke();
  } else if (tag === "queda") {
    ctx.beginPath();
    ctx.moveTo(0, -size * 0.5);
    ctx.lineTo(0, size * 0.35);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-size * 0.2, size * 0.1);
    ctx.lineTo(0, size * 0.35);
    ctx.lineTo(size * 0.2, size * 0.1);
    ctx.stroke();
  } else if (tag === "casa") {
    ctx.beginPath();
    ctx.rect(-size * 0.35, -size * 0.1, size * 0.7, size * 0.55);
    ctx.moveTo(-size * 0.4, -size * 0.1);
    ctx.lineTo(0, -size * 0.5);
    ctx.lineTo(size * 0.4, -size * 0.1);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  } else if (tag === "voo") {
    ctx.beginPath();
    ctx.moveTo(-size * 0.5, 0);
    ctx.quadraticCurveTo(-size * 0.1, -size * 0.35, 0, 0);
    ctx.quadraticCurveTo(size * 0.1, -size * 0.35, size * 0.5, 0);
    ctx.stroke();
  } else if (tag === "morte") {
    ctx.beginPath();
    ctx.arc(0, -size * 0.15, size * 0.28, 0, Math.PI * 2);
    ctx.moveTo(0, size * 0.1);
    ctx.lineTo(0, size * 0.45);
    ctx.moveTo(-size * 0.25, size * 0.22);
    ctx.lineTo(size * 0.25, size * 0.22);
    ctx.stroke();
  } else if (tag === "perseguidor") {
    ctx.beginPath();
    ctx.ellipse(0, 0, size * 0.35, size * 0.5, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(-size * 0.12, -size * 0.1, 3, 0, Math.PI * 2);
    ctx.arc(size * 0.12, -size * 0.1, 3, 0, Math.PI * 2);
    ctx.fill();
  } else if (tag === "espelho") {
    ctx.beginPath();
    ctx.ellipse(0, 0, size * 0.28, size * 0.45, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-size * 0.15, -size * 0.2);
    ctx.lineTo(size * 0.1, size * 0.25);
    ctx.stroke();
  } else if (tag === "fogo") {
    ctx.beginPath();
    ctx.moveTo(0, size * 0.4);
    ctx.quadraticCurveTo(-size * 0.35, 0, 0, -size * 0.5);
    ctx.quadraticCurveTo(size * 0.35, 0, 0, size * 0.4);
    ctx.fill();
    ctx.stroke();
  } else if (tag === "porta") {
    ctx.beginPath();
    ctx.rect(-size * 0.25, -size * 0.45, size * 0.5, size * 0.9);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(size * 0.1, 0, 3, 0, Math.PI * 2);
    ctx.fill();
  } else if (tag === "escada") {
    for (let i = 0; i < 4; i++) {
      const yy = -size * 0.4 + i * size * 0.25;
      ctx.strokeRect(-size * 0.35 + i * 8, yy, size * 0.55, size * 0.18);
    }
  } else if (tag === "dente") {
    ctx.beginPath();
    ctx.moveTo(-size * 0.2, -size * 0.2);
    ctx.lineTo(-size * 0.15, size * 0.35);
    ctx.lineTo(0, size * 0.15);
    ctx.lineTo(size * 0.15, size * 0.35);
    ctx.lineTo(size * 0.2, -size * 0.2);
    ctx.closePath();
    ctx.stroke();
  } else if (tag === "ex") {
    ctx.beginPath();
    ctx.moveTo(-size * 0.3, -size * 0.3);
    ctx.lineTo(size * 0.3, size * 0.3);
    ctx.moveTo(size * 0.3, -size * 0.3);
    ctx.lineTo(-size * 0.3, size * 0.3);
    ctx.stroke();
  } else if (tag === "animal") {
    ctx.beginPath();
    ctx.arc(0, 0, size * 0.32, 0, Math.PI * 2);
    ctx.moveTo(-size * 0.2, -size * 0.35);
    ctx.lineTo(-size * 0.05, -size * 0.15);
    ctx.moveTo(size * 0.2, -size * 0.35);
    ctx.lineTo(size * 0.05, -size * 0.15);
    ctx.stroke();
  } else {
    // geometric mark fallback
    ctx.beginPath();
    const n = 3 + (seed % 3);
    for (let i = 0; i < n; i++) {
      const ang = (Math.PI * 2 * i) / n - Math.PI / 2;
      const px = Math.cos(ang) * size * 0.4;
      const py = Math.sin(ang) * size * 0.4;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.stroke();
  }
  ctx.restore();
}

function grainOverlay(ctx, w, h, motion, time) {
  const density = 800 + Math.floor(motion * 2200);
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  // light noise pass on a sparse grid for performance
  for (let i = 0; i < density; i++) {
    const x = (Math.sin(i * 12.9898 + time) * 43758.5453) % 1;
    const y = (Math.sin(i * 78.233 + time * 0.7) * 23421.631) % 1;
    const px = Math.floor(Math.abs(x) * w);
    const py = Math.floor(Math.abs(y) * h);
    const idx = (py * w + px) * 4;
    const v = 30 + (i % 40);
    d[idx] = Math.min(255, d[idx] + v);
    d[idx + 1] = Math.min(255, d[idx + 1] + v);
    d[idx + 2] = Math.min(255, d[idx + 2] + v);
  }
  ctx.putImageData(img, 0, 0);

  // scanlines / motion streaks
  if (motion > 0.25) {
    ctx.save();
    ctx.globalAlpha = 0.04 + motion * 0.08;
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1;
    const speed = time * (0.5 + motion * 2);
    for (let y = 0; y < h; y += Math.max(3, 14 - Math.floor(motion * 10))) {
      const offset = Math.sin(y * 0.05 + speed) * motion * 8;
      ctx.beginPath();
      ctx.moveTo(0, y + offset);
      ctx.lineTo(w, y + offset);
      ctx.stroke();
    }
    ctx.restore();
  }
}

function drawTitle(ctx, w, h, title, accent) {
  ctx.save();
  ctx.fillStyle = "rgba(5,6,11,0.55)";
  ctx.fillRect(0, h - 72, w, 72);
  ctx.font = "italic 200 28px Spectral, Georgia, serif";
  ctx.fillStyle = COLORS.texto;
  ctx.textBaseline = "middle";
  ctx.fillText(title, 28, h - 36);
  ctx.fillStyle = accentHex(accent);
  ctx.fillRect(28, h - 18, 48, 2);
  ctx.restore();
}

function renderFrame(knobs, time) {
  const w = canvas.width;
  const h = canvas.height;
  const accent = accentHex(knobs.accent);
  const readiness = knobs.readiness;

  ctx.clearRect(0, 0, w, h);
  ctx.globalAlpha = 0.35 + readiness * 0.65;
  placePlate(ctx, w, h, knobs.place, accent, knobs.polarity);
  ctx.globalAlpha = 1;

  const positions = [
    [w * 0.28, h * 0.42],
    [w * 0.62, h * 0.38],
    [w * 0.48, h * 0.62],
  ];
  knobs.symbols.forEach((tag, i) => {
    const [x, y] = positions[i] || [w * 0.5, h * 0.5];
    const jitter = knobs.motion * 12;
    const jx = x + Math.sin(time * (1 + i) + i) * jitter;
    const jy = y + Math.cos(time * (0.8 + i * 0.3)) * jitter;
    const size = 55 + readiness * 30 - i * 8;
    drawSymbol(ctx, tag, jx, jy, size, accent, i + tag.length);
  });

  // polarity bloom vs bleed
  const a = hexToRgb(accent);
  const bloom = ctx.createRadialGradient(w * 0.5, h * 0.45, 10, w * 0.5, h * 0.45, w * 0.45);
  if (knobs.polarity >= 1.2) {
    bloom.addColorStop(0, `rgba(${a.r},${a.g},${a.b},0.14)`);
    bloom.addColorStop(1, "rgba(0,0,0,0)");
  } else if (knobs.polarity <= 0.7) {
    bloom.addColorStop(0, "rgba(0,0,0,0)");
    bloom.addColorStop(1, `rgba(${a.r},${a.g},${a.b},0.12)`);
  } else {
    bloom.addColorStop(0, `rgba(${a.r},${a.g},${a.b},0.06)`);
    bloom.addColorStop(1, "rgba(0,0,0,0)");
  }
  ctx.fillStyle = bloom;
  ctx.fillRect(0, 0, w, h);

  grainOverlay(ctx, w, h, knobs.motion, time);
  drawTitle(ctx, w, h, knobs.title, knobs.accent);
}

function startLoop(knobs) {
  currentKnobs = knobs;
  if (animId) cancelAnimationFrame(animId);
  const tick = (now) => {
    const time = (now - t0) / 1000;
    renderFrame(currentKnobs, time);
    animId = requestAnimationFrame(tick);
  };
  animId = requestAnimationFrame(tick);
}

function generate() {
  const text = relatoEl.value.trim();
  if (!text) {
    setStatus("cole ou sorteie um sonho primeiro");
    return;
  }
  wrapEl.classList.add("gerando");
  setStatus("mapeando knobs…");
  const knobs = extractKnobs(text);
  knobsEl.textContent = JSON.stringify(knobs, null, 2);
  hintEl.hidden = true;
  tituloEl.hidden = false;
  tituloEl.textContent = knobs.title;
  startLoop(knobs);
  wrapEl.classList.remove("gerando");
  setStatus(`colagem · ${knobs.mood} · ${knobs.place} · movimento ${knobs.motion}`);
}

async function loadPool() {
  try {
    const res = await fetch("./sonhos.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    pool = Array.isArray(data) ? data : [];
    setStatus(`${pool.length} sonhos no pool local`);
  } catch (err) {
    pool = [];
    setStatus(`pool indisponível (${err.message}) — cole um relato`);
  }
}

function sortear() {
  if (!pool.length) {
    setStatus("pool vazio — ainda carregando ou falhou o fetch");
    return;
  }
  let pick = pool[Math.floor(Math.random() * pool.length)];
  if (pool.length > 1) {
    let guard = 0;
    while (pick.id === lastUsedId && guard < 8) {
      pick = pool[Math.floor(Math.random() * pool.length)];
      guard += 1;
    }
  }
  lastUsedId = pick.id;
  relatoEl.value = pick.text;
  setStatus(`sorteado · ${pick.id}`);
  generate();
}

$("#sortear").addEventListener("click", sortear);
$("#gerar").addEventListener("click", generate);
relatoEl.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") generate();
});

loadPool();
