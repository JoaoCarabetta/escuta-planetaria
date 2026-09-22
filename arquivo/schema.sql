-- Escuta Planetária — schema da OFICINA (SQLite local)
-- O arquivo público (Supabase) recebe só o derivado, via sync que EXCLUI os campos interno_*.

CREATE TABLE IF NOT EXISTS relatos (
  id TEXT PRIMARY KEY,              -- hash estável: sha256(fonte:id_original)[:16]
  natureza TEXT NOT NULL CHECK(natureza IN ('escrito','oral','curado')),
  fonte TEXT NOT NULL,              -- reddit | bluesky | dreambank | youtube | ...
  comunidade TEXT,                  -- subreddit / instância / canal / corpus
  data_relato TEXT,                 -- ISO 8601 COMPLETO (UTC, com hora quando a fonte der)
  precisao_data TEXT NOT NULL DEFAULT 'dia'
    CHECK(precisao_data IN ('hora','dia','mes','ano','decada')),
  data_coleta TEXT NOT NULL,
  idioma TEXT,
  texto TEXT NOT NULL,              -- anonimizado; extrações marcadas [texto extraído da ...]
  tem_midia INTEGER NOT NULL DEFAULT 0,
  midia_extraida INTEGER NOT NULL DEFAULT 0,
  categoria INTEGER CHECK(categoria BETWEEN 1 AND 7),
  confianca REAL,
  julgador TEXT,                    -- veredito corrente (espelho do último julgamento aceito)
  tem_relato_onirico INTEGER,
  keywords TEXT,                    -- JSON array
  embedding BLOB,                   -- float32[1024] bge-m3
  geo_pais TEXT,                    -- ISO 3166 (BR, US...) ou NULL
  geo_regiao TEXT,                  -- UF / estado quando houver
  geo_metodo TEXT                   -- comunidade | perfil | mencao | veiculo | estudo
    CHECK(geo_metodo IN ('comunidade','perfil','mencao','veiculo','estudo') OR geo_metodo IS NULL),
  geo_confianca REAL,
  -- quem sonha (só o que é público/declarado; método e confiança sempre juntos)
  sonhador_idade INTEGER,
  sonhador_genero TEXT,             -- feminino | masculino | outro | NULL
  sonhador_nacionalidade TEXT,      -- ISO 3166, quando declarada/derivada (≠ geo do post)
  demo_metodo TEXT                  -- declarado | inferido | corpus
    CHECK(demo_metodo IN ('declarado','inferido','corpus') OR demo_metodo IS NULL),
  demo_confianca REAL,
  canonico_de TEXT REFERENCES relatos(id),  -- NULL = este é o canônico
  -- auditoria interna: NUNCA sincroniza para o arquivo público
  interno_url TEXT,
  interno_id_original TEXT
);
CREATE INDEX IF NOT EXISTS idx_relatos_cat ON relatos(categoria);
CREATE INDEX IF NOT EXISTS idx_relatos_data ON relatos(data_relato);
CREATE INDEX IF NOT EXISTS idx_relatos_fonte ON relatos(fonte, comunidade);

CREATE TABLE IF NOT EXISTS julgamentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  relato_id TEXT NOT NULL REFERENCES relatos(id),
  julgador TEXT NOT NULL,           -- heuristica | ollama:<modelo> | claude:<modelo> | humano:<nome>
  versao TEXT,                      -- versão do prompt/rubrica (ex.: rubrica-v1)
  categoria INTEGER NOT NULL CHECK(categoria BETWEEN 1 AND 7),
  confianca REAL,
  tem_relato_onirico INTEGER,
  criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_julg_relato ON julgamentos(relato_id);

CREATE TABLE IF NOT EXISTS fila_brutos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fonte TEXT NOT NULL,
  lote TEXT,
  payload TEXT NOT NULL,            -- JSON cru da fonte
  status TEXT NOT NULL DEFAULT 'pendente'
    CHECK(status IN ('pendente','triado','descartado','erro')),
  coletado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pulso (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fonte TEXT NOT NULL,              -- trends | wikipedia | gdelt
  termo TEXT NOT NULL,
  geo_pais TEXT,
  geo_regiao TEXT,
  data TEXT NOT NULL,
  granularidade TEXT NOT NULL DEFAULT 'semana',
  valor REAL,
  unidade TEXT
);
CREATE INDEX IF NOT EXISTS idx_pulso ON pulso(termo, geo_pais, geo_regiao, data);

CREATE TABLE IF NOT EXISTS continentes (
  id INTEGER,
  rodada TEXT NOT NULL,             -- versão da projeção (ex.: piloto-2026-09-18)
  nome_ollama TEXT,
  nome_curado TEXT,                 -- curadoria Fitipe/João prevalece
  centroid TEXT,                    -- JSON [x,y,z]
  n_membros INTEGER,
  PRIMARY KEY (rodada, id)
);
