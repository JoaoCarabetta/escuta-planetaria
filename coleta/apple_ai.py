"""IAs nativas da Apple no pipeline — locais, gratuitas, instantâneas.

- detectar_idioma(texto): NLLanguageRecognizer (framework NaturalLanguage).
  Substitui a inferência de idioma por comunidade/LLM na triagem.
- ocr_imagem(caminho): Apple Vision / Live Text via ocrmac.
  Estágio de extração multimodal (texto dentro de prints/memes).
"""
from ocrmac import ocrmac as _ocr
import NaturalLanguage as _nl


def detectar_idioma(texto, minimo_confianca=0.5):
    """Devolve (codigo_iso, confianca) — ex.: ('pt', 0.92) — ou (None, 0)."""
    rec = _nl.NLLanguageRecognizer.alloc().init()
    rec.processString_(texto[:1000])
    hyp = rec.languageHypothesesWithMaximum_(1)
    if not hyp:
        return None, 0.0
    lang = list(hyp.keys())[0]
    conf = float(hyp[lang])
    if conf < minimo_confianca:
        return None, conf
    return str(lang), conf


def ocr_imagem(caminho, idiomas=('pt-BR', 'en-US')):
    """Devolve o texto reconhecido na imagem (Apple Vision, accurate)."""
    anotacoes = _ocr.OCR(caminho, recognition_level='accurate',
                         language_preference=list(idiomas)).recognize()
    return '\n'.join(a[0] for a in anotacoes)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        print(ocr_imagem(sys.argv[1]))
    else:
        for t in ('Sonhei que voava sobre a minha escola',
                  'I dreamt I was flying over my school',
                  'Soñé que volaba sobre mi escuela'):
            print(t[:40], '→', detectar_idioma(t))
