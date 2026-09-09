#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Toda rule on-demand precisa CABER no que o router entrega.

O router (~/brain/thalamus/router.py) injeta as 3 rules com mais triggers
batendo no prompt, e corta o corpo em 3000 caracteres. Rule maior que isso
chega pela metade — e a metade perdida costuma ser o fim, onde mora o
checklist acionável.

Descoberto em 06-Set-2026: a primeira versão da verificacao-honesta.md tinha
5.918 chars; metade nunca chegaria, incluindo as 5 perguntas finais.
"""
import io, os, re, sys, yaml, glob

LIMITE = 3000
D = os.path.expanduser('~/cortex/vault/rules')
falhas, avisos = [], []

for rf in sorted(glob.glob(D + '/*.md')):
    txt = io.open(rf, encoding='utf-8').read()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', txt, re.DOTALL)
    nome = os.path.basename(rf)
    if not m:
        avisos.append((nome, 'sem frontmatter — o router ignora'))
        continue
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception as e:
        falhas.append((nome, 'frontmatter inválido: ' + str(e)[:40])); continue
    corpo = txt[m.end():].strip()
    trig = fm.get('triggers') or []
    if not trig:
        avisos.append((nome, 'sem triggers — nunca será selecionada'))
    if len(corpo) > LIMITE and not nome.endswith('-full.md'):
        perdido = len(corpo) - LIMITE
        secs = [l[3:] for l in corpo[LIMITE:].split('\n') if l.startswith('## ')]
        falhas.append((nome, '%d chars (perde %d)%s' % (
            len(corpo), perdido, ' — some: ' + ', '.join(secs[:3]) if secs else '')))

print()
print('  \033[1mrules on-demand que cabem no que o router entrega\033[0m')
print('  \033[2mlimite: %d chars de corpo; "-full" é referência, não é injetada\033[0m' % LIMITE)
print()
if falhas:
    for n, p in falhas:
        print('  \033[31m✗\033[0m %-46s %s' % (n[:46], p))
if avisos:
    for n, p in avisos:
        print('  \033[33m⚠\033[0m %-46s %s' % (n[:46], p))
if not falhas and not avisos:
    print('  \033[32mtodas cabem e têm triggers\033[0m')
print()
print('  %d rule(s) truncada(s) · %d aviso(s)' % (len(falhas), len(avisos)))
print()
sys.exit(1 if falhas else 0)
