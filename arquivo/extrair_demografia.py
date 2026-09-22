#!/usr/bin/env python3
"""Extrai idade/gênero DECLARADOS nos textos (regex conservador).

Convenções BR (r/desabafos etc.): H23 = homem 23; M20/F20 = mulher 20.
Convenções EN: 22M = male; 20F = female.
Só grava o que está explícito; demo_metodo='declarado'.
"""
import re
import sqlite3
from pathlib import Path

con = sqlite3.connect(Path(__file__).parent / 'arquivo.db')

# padrões: sigla+idade
SIGLA_PT = re.compile(r'\(?\b([HMF])\s?(\d{2})\b\)?')
SIGLA_EN = re.compile(r'\(?\b(\d{2})\s?([MF])\b\)?|\(?\b([MF])\s?(\d{2})\b\)?')
IDADE_PT = re.compile(r'\btenho (\d{1,2}) anos\b|\bsou um[a]? \w+ de (\d{1,2}) anos\b', re.I)
IDADE_EN = re.compile(r"\bI'?m (?:a )?(\d{1,2})(?:\s?years? old|\s?yo\b|\s?y/o\b)|\bgirl of (\d{1,2})\b", re.I)
GEN_PT = re.compile(r'\bsou (?:um )?(homem|mulher|garota|garoto|menina|menino|rapaz|moça)\b', re.I)
GEN_EN = re.compile(r"\bI'?m a (girl|boy|woman|man|guy|female|male)\b", re.I)

FEM = {'mulher', 'garota', 'menina', 'moça', 'girl', 'woman', 'female', 'f'}
MASC = {'homem', 'garoto', 'menino', 'rapaz', 'boy', 'man', 'guy', 'male', 'h'}


def extrair(texto, idioma):
    idade, genero = None, None
    t = texto[:600]  # declarações vêm no começo

    if idioma == 'pt':
        m = SIGLA_PT.search(t)
        if m:
            sig, num = m.group(1).lower(), int(m.group(2))
            if 10 <= num <= 90:
                idade = num
                genero = 'masculino' if sig == 'h' else 'feminino'  # M/F = mulher/feminino no BR
        m = GEN_PT.search(t)
        if m:
            g = m.group(1).lower()
            genero = 'feminino' if g in FEM else 'masculino' if g in MASC else genero
        m = IDADE_PT.search(t)
        if m:
            n = int(m.group(1) or m.group(2))
            if 10 <= n <= 90:
                idade = n
    else:
        m = SIGLA_EN.search(t)
        if m:
            g = (m.group(2) or m.group(3) or '').lower()
            n = int(m.group(1) or m.group(4) or 0)
            if g and 10 <= n <= 90:
                idade = n
                genero = 'feminino' if g == 'f' else 'masculino'
        m = GEN_EN.search(t)
        if m:
            g = m.group(1).lower()
            genero = 'feminino' if g in FEM else 'masculino' if g in MASC else genero
        m = IDADE_EN.search(t)
        if m:
            n = int(m.group(1) or m.group(2))
            if 10 <= n <= 90:
                idade = n

    return idade, genero


def _relatorio():
    achados = 0
    for rid, texto, idioma in con.execute("SELECT id, texto, idioma FROM relatos"):
        idade, genero = extrair(texto, idioma)
        if idade or genero:
            con.execute(
                """UPDATE relatos SET sonhador_idade=?, sonhador_genero=?,
                   demo_metodo='declarado', demo_confianca=0.85 WHERE id=?""",
                (idade, genero, rid))
            achados += 1
    con.commit()
    
    print(f"demografia declarada encontrada em {achados}/491 relatos")
    for row in con.execute("""SELECT sonhador_genero, COUNT(*), ROUND(AVG(sonhador_idade),1)
                              FROM relatos WHERE demo_metodo='declarado'
                              GROUP BY sonhador_genero"""):
        print(f"  {row[0] or 'só idade'}: {row[1]} relatos, idade média {row[2]}")


if __name__ == '__main__':
    _relatorio()
