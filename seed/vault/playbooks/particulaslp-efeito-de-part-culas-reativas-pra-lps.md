---
id: particulaslp-efeito-de-part-culas-reativas-pra-lps
title: PARTICULASLP — Efeito de partículas reativas pra LPs
type: playbook
status: active
created: '2026-04-25'
last_verified: '2026-04-25'
domain:
- creative
agents:
- dev
- ux-design-expert
- content
tags:
- webgl
- threejs
- particles
- lp
- hero
- efeito-visual
- reusable
decay_rate: 0.02
links:
- target: skills-apresentacao
  type: auto-linked
- target: segunda-feira-voice
  type: auto-linked
- target: clienteexemplo-capi-pixel-setup
  type: auto-linked
axis: ops
---

# PARTICULASLP — Efeito de partículas reativas pra LPs

Componente WebGL custom que transforma foto em partículas reativas ao cursor com explosão dourada no clique do CTA. Inspirado em wearebrand.io. Usa Three.js + GLSL custom shader. Estados: idle (foto sólida) → cursor hover (repulsão radial dourada) → click no CTA (explosão completa + scroll smooth). API: new ParticulasLP({canvas, image, clickSelector, clickScrollTo, emberColor, hotColor}). Componente em ~/dev/particulaslp/. Skill em ~/.claude/skills/particulaslp.md. Primeira aplicação: ~/Desktop/segunda-feira-jarvis/lp-desafio/. Setup ~70min: refator + readme + skill + cortex. Performance: ~38K partículas em desktop, auto-reduz pra ~25K em mobile. Reduz pra 15K se precisar de >60fps em GPUs fracas.