---
name: image-gen
description: "Gera imagem por IA escolhendo o provedor pelo objetivo — gpt-image-2 para identidade facial e texto nítido, nano-banana-2 para volume barato. Use em criativo de ads, hero de LP, thumbnail ou capa. NOT for: vídeo (é /camera-moves)."
axis: ops
harnesses:
  claude-code: full
  codex: full
  cursor: limited
---

# /image-gen — Geração de Imagem com Escolha de Provedor

> **Funde `banana-image-gen` + `gpt-image-gen` (05-Set-2026).** As duas não eram duplicatas —
> eram complementares e já se referenciavam ("NOT for: … isso é /gpt-image-gen"). O problema era
> outro: **as duas dependiam de `~/Desktop/segunda-feira-jarvis/image_gen.py`, que não existe
> desde jul/2026.** O comando `/img` carrega o mesmo defeito. Esta versão chama a API direto por
> `curl`, sem módulo local.

## Escolha do provedor — decida antes de gerar

| O briefing pede | Provedor | Por quê |
|---|---|---|
| Preservar **rosto** de pessoa real (${CEO_NAME}, mentor, aluno) | **gpt-image-2** | `/edit` aceita até 16 refs, ~85-90% de fidelidade facial |
| **Texto dentro da imagem** legível | **gpt-image-2** | único que acerta tipografia de forma confiável |
| "Qualidade ChatGPT", hero de LP cinematográfico | **gpt-image-2** | é o modelo por trás do ChatGPT |
| **Volume** (20+ imagens), teste de ângulos | **nano-banana-2** | ~US$0,15/img |
| Fotorrealismo de pessoa **sem** identidade específica | **nano-banana-2** | mais permissivo, menos recusa |

Na dúvida entre os dois: gere **1 teste no nano-banana** e só suba para gpt-image se a
identidade ou o texto saírem errados. Erra barato antes de errar caro.

## Credenciais

```bash
# fonte única — criar se não existir (chmod 600)
cat ~/_secrets/image-gen.env
#   KIE_API_KEY=...    → https://kie.ai  (nano-banana-2)
#   FAL_KEY=...        → https://fal.ai/dashboard/keys  (gpt-image-2)
```
Nunca colar chave no corpo da skill — foi assim que as duas versões anteriores acabaram com
credencial em texto no `_secrets/_pre-skills-fix`.

## Pipeline nano-banana-2 (Kie.ai)

```bash
KEY=$(grep '^KIE_API_KEY=' ~/_secrets/image-gen.env | cut -d= -f2-)
# 1. cria a tarefa
TASK=$(curl -s -X POST https://api.kie.ai/api/v1/jobs/createTask \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"nano-banana-2","input":{"prompt":"SEU PROMPT"}}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["data"]["taskId"])')
# 2. faz polling a cada 5s, teto de 180s
curl -s "https://api.kie.ai/api/v1/jobs/recordInfo?taskId=$TASK" -H "Authorization: Bearer $KEY"
```

**Estados:** `waiting`/`pending` → `processing` → `success` | `failed`.

**Extrair a URL** — `data.resultJson` vem como **string JSON**, precisa de parse. Ordem de
tentativa: `resultUrls[0]` → `resultUrl` → `images[0]` → `url`/`image_url` → a própria string se
começar com `http` → `data.image_url` → `data.url`. Se nada casar, busque qualquer URL com
`.png`/`.jpg`/`.webp` no corpo.

## Regras de prompt (valem para os dois)

- Acrescente `"Image should be in {ratio} aspect ratio format."` — ajuda a compor para o frame.
- Descreva **luz, lente e enquadramento**, não só o objeto: "golden hour lateral, 85mm, plano médio".
- Para série consistente, fixe cenário e personagem e **varie um elemento por vez** — mesma
  disciplina do `/camera-moves`.

## Saída

Salvar em `~/Pictures/segunda-feira/` (diretório existe). Entregar ao CEO: caminho do arquivo,
provedor usado, custo estimado e oferta de variação.

## Anti-patterns

Escolher provedor pelo hábito e não pelo briefing · gerar 20 imagens no gpt-image quando o teste
cabia no nano-banana · pedir texto na imagem ao nano-banana · esquecer o parse do `resultJson`
(ele é string, não objeto) · depender de módulo Python local — foi o que matou as duas versões anteriores.
