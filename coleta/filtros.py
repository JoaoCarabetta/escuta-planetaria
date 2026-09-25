"""Camada 0 — filtro de entrada da fila (validado no piloto de 2026-09-17).

Devolve (ok, motivo). Descarta só o que certamente não interessa;
na dúvida, deixa passar para a triagem (camada 1+).
"""
import re

# '[deleted]' NÃO entra aqui: conta apagada não invalida o relato — e em 11 anos
# é justamente o material mais antigo e mais vulnerável que some por esse motivo.
BOTS = {'AutoModerator', 'RemindMeBot', 'sneakpeekbot'}

# fazenda SEO de dicionário de sonhos (96% do r/sonhos no piloto)
SEO = re.compile(
    r'^(significado (completo )?d[eo]s? sonh|sonhar com\b.{0,60}(significa|significado)'
    r'|simbolismo d[ae]|o que significam?\b)', re.I)
SEO_SUFIXO = re.compile(r'significado d[oa]s (sonhos|símbolos)\s*\.{0,3}$', re.I)


def camada0(p):
    """p: dict de post do Reddit (formato Arctic Shift)."""
    selftext = (p.get('selftext') or '').strip()
    title = (p.get('title') or '').strip()

    if selftext in ('[removed]', '[deleted]'):
        return False, 'removido'
    if (p.get('author') or '') in BOTS:
        return False, 'bot'
    if len(title) + len(selftext) < 15:
        return False, 'curto'
    if SEO.search(title) or SEO_SUFIXO.search(title):
        return False, 'seo'

    if not selftext:
        url = p.get('url') or ''
        tem_midia = ('i.redd.it' in url or 'imgur' in url or 'v.redd.it' in url
                     or p.get('post_hint') in ('image', 'hosted:video')
                     or bool(p.get('media_metadata')) or bool(p.get('is_video')))
        if not tem_midia:
            # só título + link externo = promo/artigo; o relato não está aqui
            return False, 'link_externo'

    return True, None



def urls_de_galeria(p):
    """URLs diretas das imagens de um post de galeria do Reddit.

    O media_metadata vem indexado por id de mídia; a url fica em ['s']['u'] e
    chega com &amp; no lugar de &. Guarda no máximo 4: o que interessa é o texto
    dentro da imagem, e print de conversa raramente passa disso.
    """
    mm = p.get('media_metadata')
    if not isinstance(mm, dict):
        return None
    urls = []
    for k in (p.get('gallery_data', {}) or {}).get('items', []) or []:
        m = mm.get(k.get('media_id'))
        u = ((m or {}).get('s') or {}).get('u')
        if u:
            urls.append(u.replace('&amp;', '&'))
    if not urls:                          # sem gallery_data: pega na ordem do dict
        for m in mm.values():
            u = ((m or {}).get('s') or {}).get('u')
            if u:
                urls.append(u.replace('&amp;', '&'))
    return urls[:4] or None


def enxugar(p):
    """Reduz o payload ao essencial antes de guardar na fila."""
    url = p.get('url') or ''
    return {
        'id': p.get('id'),
        'subreddit': p.get('subreddit'),
        'title': p.get('title'),
        'selftext': p.get('selftext'),
        'created_utc': p.get('created_utc'),
        'permalink': p.get('permalink'),
        'author': p.get('author'),          # oficina apenas: bot/dedup; nunca sincroniza
        'url': url if ('reddit.com' not in url) else None,
        'post_hint': p.get('post_hint'),
        'is_video': bool(p.get('is_video')),
        # GALERIA: guardava só um booleano e jogava fora as URLs das imagens.
        # Como o post de galeria tem url 'reddit.com/gallery/...' (que vira None
        # na linha acima), o relato ficava sem nada além do título e o texto do
        # sonho, que estava na imagem, sumia sem deixar rastro.
        'imagens': urls_de_galeria(p),
        'tem_media_metadata': bool(p.get('media_metadata')),
        'num_comments': p.get('num_comments'),
    }
