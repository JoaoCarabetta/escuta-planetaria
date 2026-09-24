"""O embedder do arquivo — um só, usado pelo moinho e pelo backfill.

Decidido por medição (24/09, `aluno/testar_janelas.py`): texto INTEIRO, sem
corte, janela nem limpeza. Truncar destrói os longos (a metade de um relato
acha a outra em 58% com texto cru, 4,5% truncado em 120).

Dois limites escondidos do Ollama, achados na mesma tarde:
- `num_ctx` sozinho não basta: sem `num_batch` igual, ele corta em 2.048 tokens
  (~8 mil caracteres) CALADO. O moinho antigo ainda cortava em 2.000 caracteres
  antes disso.
- o teto do bge-m3 é 8.192 tokens (~32 mil caracteres). Acima disso o corte é
  inevitável, e é detectável: `prompt_eval_count` volta exatamente 8.192. Esses
  são os ENORMES, e vão para a tabela `revisao`.
"""
import json
import urllib.request

import numpy as np

MODELO = 'bge-m3'
TETO = 8192
VERSAO = f'{MODELO}:{TETO}'   # vai para relatos.embed_versao
_OPCOES = {'num_ctx': TETO, 'num_batch': TETO}


def _pedir(entrada):
    req = urllib.request.Request(
        'http://localhost:11434/api/embed',
        data=json.dumps({'model': MODELO, 'input': entrada,
                         'options': _OPCOES}).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def embeddar(texto):
    """→ (bytes float32, cortado: bool). Um texto por chamada, para que a
    contagem de tokens seja dele e o corte seja detectável."""
    d = _pedir(texto)
    v = np.array(d['embeddings'][0], dtype='float32')
    return v.tobytes(), d.get('prompt_eval_count', 0) >= TETO


def embeddar_lote(textos):
    """Para textos curtos (bem abaixo do teto), em lote: → lista de bytes.
    A contagem de tokens do lote é somada, então NÃO serve para detectar corte —
    quem chama garante que nenhum texto chega perto do teto."""
    d = _pedir(textos)
    return [np.array(e, dtype='float32').tobytes() for e in d['embeddings']]
