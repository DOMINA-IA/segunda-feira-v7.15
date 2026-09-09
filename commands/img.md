---
description: Gera imagem por IA (gpt-image-2 ou nano-banana-2) via /image-gen
argument-hint: <descrição da imagem>
---

O pipeline antigo (`~/Desktop/segunda-feira-jarvis/image_gen.py`) foi removido em jul/2026 e
este comando ficou quebrado por 2 meses. Agora ele delega para a skill.

Use a skill **`/image-gen`** com o prompt: `$ARGUMENTS`

Ela escolhe o provedor pelo objetivo (identidade facial e texto → gpt-image-2; volume e
fotorrealismo barato → nano-banana-2), chama a API por curl e salva em `~/Pictures/segunda-feira/`.
