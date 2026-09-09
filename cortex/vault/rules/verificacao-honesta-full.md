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
- está funcionando
- gate
- validar
axis: meta
severity: MUST
origem: Destilado de 54 memórias de feedback + auditoria multi-agente do CLIENTE_EXEMPLO (06-Set-2026)
links:
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: related
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: related
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: related
- target: plano-correcao-framework-05-set-2026
  type: related
---

# Verificação Honesta

> **Severidade:** MUST | **Aplica-se a:** @dev, @qa, @devops, @data-engineer, @tester

## Princípio

Quase todo defeito que chegou à produção nos projetos do CEO passou por alguma
verificação **que disse estar tudo bem**. O problema raramente é a falta de
teste — é o teste que confirma a própria suposição.

> **Regra de ouro:** "Verde não é prova. Prova é o verificador ter reprovado o
> defeito conhecido pelo menos uma vez."

---

## 1. O verde que não testou nada

| Armadilha | Como acontece | O que fazer |
|---|---|---|
| **Sintaxe do arquivo ≠ código entregue** | `node --check` aprova JS quebrado dentro de template literal do servidor: `\n` vira quebra real, `\s` vira `s` | Validar a **página servida** (pedir por HTTP, passar os `<script>` por parser) |
| **Pipe engole o código de saída** | `npm test \| tail -2 \|\| FALHOU=1` lê o resultado do `tail`, sempre 0 | `set -o pipefail`, ou testar `${PIPESTATUS[0]}` |
| **Encadeado devolve o último** | `cmd_que_falha; sleep 8; curl` sai com 0 | Medir o **estado**, não o código de saída |
| **Script sai 0 tendo achado erro** | `process.exit()` sem refletir o resultado | Exit code = veredito |
| **Detector nunca viu o defeito** | regex quebrado devolve "nenhum problema" | O verificador **roda a si mesmo** contra um caso ruim conhecido e aborta se não pegar |
| **`grep` encontra a si mesmo** | `pgrep -f "node server.js"` casa com o próprio shell | Filtrar por `cwd`/PID, não por texto |
| **`IS NOT NULL` ≠ tem conteúdo** | string vazia passa | `LENGTH(TRIM(COALESCE(x,''))) >= n` |

## 2. O teste que confirma a suposição

- **Ancorado em texto literal** quebra quando a assinatura muda, e reprova
  código correto. Ancore no **nome** da função, não na linha inteira.
- **Monta a entrada com a mesma regra que o código lê** → passa sempre. Use o
  artefato real do terceiro (arquivo de retorno, XML, extrato).
- **Exige um id específico onde o código promete outra coisa.** Antes da
  asserção, diga em uma frase o que o código promete; se a frase não contém o
  identificador, compare outra coisa — a propriedade, ou a coerência interna.
- **Verificador ancorado na forma da solução** reprova toda implementação
  diferente da prevista, inclusive a melhor. Pergunte *"o que precisa ser
  verdade?"*, não *"que código espero ver?"*.
- **Teste que grava e não limpa** envenena a rodada seguinte — e o falso defeito
  manda o diagnóstico para o lugar errado.

## 3. A correção que não pegou tudo

- **`grep` no arquivo aberto ≠ no repositório.** Para dizer "corrigi todos os
  pontos", a busca roda no projeto inteiro. (Custou 5 pontos de `wa.me` em 3
  módulos depois de eu declarar os 4 do arquivo em que estava.)
- **A trava mora na função que age**, não na rota comum. Script que chama a
  função direto passa por fora de guarda posta no caminho.
- **Três implementações da mesma regra** divergem um dia. Ponha no lugar
  compartilhado — no CLIENTE_EXEMPLO, o JS que todas as telas carregam.
- **Asset cacheado exige `?v=` novo na mesma tarefa**, ou o navegador serve o
  código velho e a função nova não existe. Inventarie por `grep` global antes
  do `sed`.
- **`scp` → `restart` → testar**, nessa ordem. Arquivo no servidor não é código
  valendo: o processo tem o módulo antigo em memória.

## 4. Medir antes de afirmar

- **Nunca use operação que muda estado para descobrir estado.** (Uma sondagem
  cancelou uma NFS-e real de R$ X.XXX.)
- Quando toda medição do seu lado dá certo e o defeito persiste no cliente,
  **reproduza do lado de fora** — `curl` no serviço de terceiro — antes de
  implementar a hipótese mais elegante.
- **Meça o resultado em vez de acertar a conta.** Em layout, convergir (medir,
  corrigir pela diferença, repetir com teto) vence calcular: a conta fechada
  exige um inventário que ninguém mantém.
- **Compare agregado com detalhe.** Divergência entre o campo do pai e a soma
  dos filhos só aparece comparando os dois. E meça as **duas direções**: valor
  sem cobrança, e dinheiro recebido em registro cancelado.
- **Aplique a mudança antes de medir.** Medida tirada antes de uma troca de
  layout descreve o layout que deixou de existir.

## 5. O rastro

- **Script que corrige dado ABORTA se não conseguir gravar a auditoria.** Seguir
  com um aviso produz o pior dos dois mundos: a correção acontece e o registro
  não. (A coluna `action` costuma ter `CHECK` com lista fechada.)
- **Operação em lote precisa de teto de conservação** e de rastro em tabela
  auditável — não em coluna `notes`. Um ajuste em lote sem auditoria cancelou 25
  parcelas e abriu R$ X.XXX sem cobrança.
- **Modo prévia é obrigatório** em script que aplica decisão em lote. É na
  prévia que aparece o caso onde a ação pedida não cabe.
- **Alerta que repete sem parar treina o humano a ignorar.** Corrija o design do
  alerta junto com a causa: throttle, diagnóstico da causa real, auto-silêncio
  com instrução de reativação.

## 6. Trava que funciona

- **Avisar vence bloquear quando o caso legítimo existe.** Trava que impede
  trabalho real é contornada por fora do sistema, não obedecida. Devolva 409 com
  **quem** está no caminho e deixe a pessoa decidir.
- **Falhe fechado.** Fallback derivado de constante do próprio código não é
  segredo — é ofuscação. Sem a variável, recuse.
- **Cache volátil que decide se um evento é processado** perde dados no primeiro
  restart. Semeie de fonte durável no boot.
- **Ferramenta que grava fica atrás de portão** (`CLIENTE_EXEMPLO_TESTE_ESCRITA=1`) ou de
  modo prévia, e **não** solta na pasta de verificadores.

---

## Antes de dizer "está funcionando"

1. O verificador já reprovou este defeito alguma vez? Se não, ele não prova nada.
2. O que rodou foi o **código entregue** ou o arquivo em disco?
3. A busca rodou no **repositório** ou no arquivo aberto?
4. Se falhasse, este comando **diria**? (pipe, `;`, `catch` que engole)
5. O estado ficou como estava, ou o teste deixou lixo?