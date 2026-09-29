import json,collections
R={json.loads(l)['id']:json.loads(l) for l in open('lotes/revisao_cega_respostas_fitipe.jsonl')}
G={json.loads(l)['id']:json.loads(l) for l in open('lotes/revisao_cega_GABARITO_nao_abrir.jsonl')}
T={json.loads(l)['id']:json.loads(l)['tipo'] for l in open('lotes/revisao_cega_fitipe.jsonl')}
def S(v):
    if isinstance(v,str) and v.startswith('['): v=json.loads(v)
    return set(v) if isinstance(v,list) else ({v} if v else set())
t=collections.defaultdict(collections.Counter); rows=[]
for i,g in G.items():
    f=R[i]; fl='nao_dormido' not in f['portao']; gl=bool(g['literal'])
    for key in [(T[i],g['confianca']),(T[i],'*'),('*',g['confianca'])]:
        c=t[key]; c['n']+=1; c['portao_ok']+= fl==gl
        if fl and gl:
            c['ambos_lit']+=1
            fc,gc=S(f['carga']),S(g['carga']); c['carga_igual']+=fc==gc; c['carga_toca']+=bool(fc&gc)
            fd,gd=S(f['despertar'])-{'nada'},S(g['despertar']); c['desp_igual']+=fd==gd
    rows.append((g['n'],T[i],g['confianca'],gl,fl,g['carga'],f['carga'],g['despertar'],f['despertar'],f['comentario'][:90],(g.get('nota') or '')[:90]))
for k in sorted(t): print(k, dict(t[k]))
print('--- portão divergente')
for r in sorted(rows):
    if r[3]!=r[4]: print(r[0],r[1],r[2],'M_lit=',r[3],'F_lit=',r[4],'|F:',r[9],'|M:',r[10])
print('--- carga divergente (ambos literal)')
for r in sorted(rows):
    if r[3] and r[4] and S(r[5])!=S(r[6]): print(r[0],r[1],r[2],'M',r[5],'F',r[6],'| desp M',r[7],'F',r[8])
c=collections.Counter(); dd=collections.Counter(); pp=collections.Counter()
for f in R.values(): c.update(f['carga']); dd.update(f['despertar']); pp.update(f['portao'])
print(c); print(dd); print(pp)
print('comentários:', sum(bool(f['comentario'].strip()) for f in R.values()))
