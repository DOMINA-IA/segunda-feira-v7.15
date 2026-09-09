# Seed — memória inicial do framework

O framework aprende com o uso, mas começar do zero absoluto é lento. Este seed dá
a partida com **lições de engenharia** já destiladas, para que o loop de aprendizado
tenha o que injetar desde a primeira sessão.

## O que tem aqui

| Arquivo | Conteúdo |
|---|---|
| `heuristics-seed.jsonl` | 714 heurísticas de engenharia (deploy, cache, timezone, testes, migração, segurança, arquitetura de agentes) |
| `vault/` | 73 notas de arquitetura de sistema (padrões de agente, pipelines, otimização, orquestração multi-IA) |

## O que NÃO tem — e por quê

Nenhum dado. Foi tudo filtrado por **dois critérios independentes** que falham de
formas diferentes:

1. **Filtro de domínio** — a lição continua verdadeira depois de trocar todo nome
   próprio por placeholder? Se não, é implementação de um sistema específico, não
   conhecimento transferível.
2. **Gate de publicação** (`tools/validate-publish.py`) — casa com padrão de
   cliente, credencial, PII, IP, host, valor financeiro ou métrica de negócio?

Das 992 heurísticas de origem, 327 foram descartadas. O gate sozinho pegou uma que
o filtro de domínio havia aprovado — por isso os dois rodam sempre, nunca um só.

## Confiança reiniciada

Toda heurística do seed entra com `confidence: 0.5` e `times_validated: 0`. Ela foi
validada no ambiente de origem, **não no seu**. Conforme você usa e cita o `#handle`
como aplicada ou falhada, a confiança sobe ou a heurística é aposentada — no seu
contexto, com os seus resultados.

É de propósito: herdar confiança alta de outro ambiente cria certeza sem lastro.

## Regenerar

```bash
python3 tools/extract-seed-memory.py --heuristics <origem.jsonl> --out seed/
```
