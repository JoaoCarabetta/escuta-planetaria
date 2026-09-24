"""A lista de revisão — relatos que precisam de olho humano (ou de anotação cara),
e o porquê. Pedida pelo Fitipe em 24/09: uma tabela viva, alimentada sozinha
pelo moinho e editada quando um caso é resolvido.

Um relato pode estar na lista por mais de um motivo (uma linha por motivo).
Resolver = preencher `resolvido_em` e `resolucao`; a linha fica, como histórico.
`abrir()` usa INSERT OR IGNORE: um caso resolvido NÃO reabre se o moinho
regravar o mesmo relato.
"""
import json

MOTIVOS = {
    # o BERT decidiu o portão perto do muro de 0,5 (margem < 0,10). Os longos
    # dominam aqui — o aluno se perde neles (15% de indecisão).
    'portao_indeciso': 'portão decidido com margem < 0,10',
    # nenhuma classe do portão passou de 0,5: o BERT não soube o que é
    'portao_vazio': 'nenhuma classe do portão acima de 0,5',
    # passou do teto do embedder (8.192 tokens): o vetor só viu o começo
    'enorme': 'texto além do teto do embedder; embedding cortado',
}
MARGEM_INDECISO = 0.10

SCHEMA = """CREATE TABLE IF NOT EXISTS revisao (
    relato_id TEXT NOT NULL,
    motivo TEXT NOT NULL,
    detalhe TEXT,
    aberto_em TEXT DEFAULT (datetime('now')),
    resolvido_em TEXT,
    resolucao TEXT,
    PRIMARY KEY (relato_id, motivo))"""


def abrir(con, relato_id, motivo, detalhe=None):
    assert motivo in MOTIVOS, motivo
    con.execute("INSERT OR IGNORE INTO revisao (relato_id, motivo, detalhe) VALUES (?,?,?)",
                (relato_id, motivo, None if detalhe is None else
                 json.dumps(detalhe, ensure_ascii=False)))


def abrir_pela_predicao(con, relato_id, e):
    """`e` é o extra do BERT (portao, margem, p_literal, p_figurado)."""
    if not e:
        return
    if not e['portao']:
        abrir(con, relato_id, 'portao_vazio',
              {'p_literal': round(e['p_literal'], 3), 'p_figurado': round(e['p_figurado'], 3)})
    elif e['margem'] < MARGEM_INDECISO:
        abrir(con, relato_id, 'portao_indeciso',
              {'margem': round(e['margem'], 3), 'portao': e['portao']})
