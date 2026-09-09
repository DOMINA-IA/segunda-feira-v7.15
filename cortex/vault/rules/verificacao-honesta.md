---
id: verificacao-honesta
title: Verificação Honesta — o que parece testado e não está
type: rule
domain:
- meta
agents:
- dev
- qa
- devops
- data-engineer
- tester
tags:
- teste
- verificacao
- deploy
- producao
- auditoria
- correcao
triggers:
- corrigir
- correção
- deploy
- teste
- verificar
- auditoria
- produção
- "está funcionando"
- gate
- validar
axis: meta
severity: MUST
origem: "Destilado de 54 memórias de feedback + auditoria multi-agente do CLIENTE_EXEMPLO (06-Set-2026)"
links:
- target: clienteexemplo-auditoria-de-fechamento-11-ago-5-furos-de-permiss-o-em-rotas-novas
  type: auto-linked
- target: padr-es-claude-code-inema-hooks-acima-de-persuas-o-artifact-relay-cache-60-do-custo
  type: auto-linked
- target: escape-em-template-literal-os-3-modos-de-quebrar-e-como-n-o-escapar
  type: auto-linked
---

# Verificação Honesta

> **MUST** | @dev, @qa, @devops, @data-engineer, @tester
> Destilado de 54 memórias de feedback + auditoria multi-agente do CLIENTE_EXEMPLO (06-Set-2026)

**Regra de ouro:** verde não é prova. Prova é o verificador ter reprovado o
defeito conhecido pelo menos uma vez.

## Antes de dizer "está funcionando" — 5 perguntas

1. **O verificador já reprovou este defeito alguma vez?** Se nunca falhou contra
   um caso ruim, pode estar com o regex morto e devolver "tudo certo".
2. **Rodou o código ENTREGUE ou o arquivo em disco?** `node --check` aprova JS
   quebrado dentro de template literal do servidor (`\n` vira quebra real,
   `\s` vira `s`). Valide a página servida.
3. **Se falhasse, este comando diria?** `npm test | tail` devolve o código do
   `tail` (use `set -o pipefail`); `catch` que engole e avisa; `cmd; sleep; curl`
   devolve o do último; `process.exit()` sem veredito.
4. **A busca rodou no REPOSITÓRIO ou no arquivo aberto?** Para dizer "corrigi
   todos os pontos", `grep` no projeto inteiro — e o gate que **pula** etapa no
   seu arquivo não verificou aquela parte.
5. **O estado ficou como estava?** Teste que grava e não limpa envenena a rodada
   seguinte e produz falso defeito.

## Ao corrigir

- **Trava dentro da função que age**, nunca só na rota: script que chama a função
  direto passa por fora.
- **Uma implementação por regra.** Precisa em 3 telas? Vá para o compartilhado.
- **Asset cacheado exige `?v=` novo na mesma tarefa** — inventarie por `grep`
  global antes do `sed`.
- **`scp` → `restart` → testar.** Arquivo no servidor não é código valendo.
- **Toda medição sua dá certo e o defeito persiste no cliente?** Reproduza do
  lado de fora (`curl` no serviço de terceiro) antes de implementar a hipótese.
- **Reuse o que existe** (`makeLimiter`, `validaSenha`) antes de trazer
  biblioteca ou copiar função.

## Ao mexer em dado

- **Modo prévia por padrão**; `aplicar` é palavra explícita. É na prévia que
  aparece o caso onde a ação pedida não cabe.
- **Retrato antes → aplicação → prova de que os números voltaram.**
- **Aborte se não conseguir gravar o rastro na auditoria.** Correção sem registro
  é o pior dos dois mundos. (`action` costuma ter `CHECK` de lista fechada.)
- **Nunca use operação que muda estado para descobrir estado.** Uma sondagem
  cancelou uma NFS-e real de R$ X.XXX.
- **Compare agregado com detalhe, nas duas direções**: valor sem cobrança E
  dinheiro recebido em registro cancelado.

## Ao escrever teste

- Ancore no **nome**, não na linha literal (assinatura muda).
- **Nunca monte a entrada com a regra que o código lê** — use o artefato real do
  terceiro.
- Diga em uma frase **o que o código promete** antes da asserção; se a frase não
  contém o id que você ia comparar, compare a propriedade ou a coerência interna.
- **Cubra a jornada, não a rota**: rota que responde 400 certo pode fazer parte
  de um fluxo que não fecha.

*Detalhe e casos de origem: `~/cortex/vault/rules/verificacao-honesta-full.md`*
