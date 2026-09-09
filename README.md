# Segunda-feira v7.15

> Framework de orquestração de agentes IA para desenvolvimento full-stack e operação de
> negócio. Feito para **Claude Code**, em **português brasileiro**.

Não é uma coleção de prompts. É um sistema operacional para trabalho com agentes:
personas com autoridade delimitada, memória que persiste entre sessões, regras que
carregam por gatilho, e verificadores que confrontam a documentação com a máquina.

---

## O que vem no pacote

| Componente | Qtd | O que é |
|---|---:|---|
| Agentes canônicos | 38 | 19 `meta/` (framework) + 19 `ops/` (negócio) |
| Agentes wrapper | 32 | camada derivada, invocável por slash command |
| Skills ativas | 30 | módulos reutilizáveis que o modelo invoca sozinho |
| Skills inativas | 79 | prontas em `_inativas/` — reative movendo a pasta |
| Regras always-loaded | 5 | segurança, julgamento, protocolo operacional |
| Regras on-demand | 35 | injetadas por gatilho, teto de 3 por prompt |
| Hooks | 16 | router, gates de autonomia, coach de contexto |
| Tasks do SDC | 222 | ciclo de desenvolvimento orientado a story |
| Workflows | 17 | incluindo SPARC-SDC com 5 quality gates |
| Squads | 12 | pacotes especializados (ofertas, design, copy…) |
| Scripts core | 71 | knowledge system, memória episódica, verificadores |

**O vault, os episódios e os patterns vêm vazios.** O framework aprende com os *seus*
dados — não com os de outra pessoa.

---

## O que mudou na v7.15

Esta versão é menos sobre adicionar e mais sobre **o que aprendemos a tirar**.

### Context engineering — o pacote ficou mais barato de rodar

- **Regras always-loaded: 11 → 5** (−39% em palavras). Auditoria mostrou a mesma
  instrução repetida em até 7 arquivos; instrução duplicada compete por atenção em vez
  de somar. As substituídas viraram on-demand com `triggers:`.
- **Skills: formato corrigido.** No Claude Code, uma skill só carrega em
  `skills/<nome>/SKILL.md`. Um `.md` solto **não carrega** — mas sua `description` ainda
  pesa no contexto de toda sessão, usada ou não. Corrigir isso e podar o catálogo cortou
  ~58% do custo de descriptions.

Se você usou uma versão anterior deste framework, essa é a diferença que aparece na fatura.

### Menos fricção para começar

- `settings.template.json` — permissões e hooks já registrados; você para de responder
  "yes" a cada chamada
- **Autonomy gate** — allow/ask/deny por classe de ação, com livro-razão do que foi feito
- **Session bootstrap** — a sessão sobe já com o contexto certo
- Instalador cria o `settings.json` (ou deixa um arquivo para você mesclar)

### O agente cobra contexto de você

Nova regra `context-quality` + hook `context-coach`: quando o pedido chega com menos de
2 dos 5 elementos que tornam uma tarefa executável, o agente **pergunta antes de chutar**.
Prompt ruim vira ida e volta, não vira trabalho errado entregue com confiança.

### Verificadores anti-teatro

`framework_health_check.py` confronta 14 afirmações da constituição contra o estado real
da máquina e falha alto na divergência. Existe porque documentação envelhece e ninguém
percebe: uma versão anterior deste framework alegava por escrito uma configuração de
modelo que nunca havia existido no arquivo.

Princípio adotado: **quem mede não é quem executou**, e verificador não muda no mesmo
commit que a coisa verificada.

---

## Instalação

Requer [Claude Code](https://claude.com/claude-code), Python 3.9+ e Git.

```bash
git clone <url-do-repo> segunda-feira
cd segunda-feira
pip3 install -r requirements.txt
bash install.sh
```

O instalador copia agentes, skills, rules, hooks e commands para `~/.claude/`, cria os
diretórios do CORTEX e do Consciousness, e gera o `settings.json` a partir do template.
Se você já tem um `settings.json`, ele deixa um `.segunda-feira.json` ao lado para você
mesclar — nunca sobrescreve.

Depois:

```bash
cp .env.example .env    # preencha o que for usar
chmod 600 .env
python3 framework/scripts/framework_health_check.py
```

### Já tem uma versão anterior instalada?

Use `upgrade.sh` em vez de `install.sh`:

```bash
git clone <url-do-repo> segunda-feira && cd segunda-feira
bash upgrade.sh
```

A diferença importa. O `install.sh` nunca sobrescreve arquivo seu — o que é
certo numa instalação nova e errado num upgrade: as 14 rules que a v7.15
consolidou continuariam carregando junto com as 5 novas (contexto **maior**
que antes), e o `settings.json` antigo ficaria sem o router registrado — com
o CORTEX e as heurísticas no disco sem nunca chegarem ao modelo.

### Ou: adotar só o que interessa

Se você customizou bastante e prefere escolher, comece pelo diagnóstico:

```bash
bash diagnostico.sh
```

Ele não altera nada — compara a sua instalação com a v7.15 e lista o que
adotar **em ordem de impacto real**, com o número de cada coisa medido no seu
ambiente (quantas palavras você carrega por sessão, quantas skills custam
contexto sem carregar, o que é seu e não pode se perder).

A ordem surpreende: o que muda o funcionamento é o motor, e ele é pequeno.
Dá para copiar todos os agentes novos e continuar sem framework nenhum, se o
`router.py` não estiver registrado no `settings.json` — aí o CORTEX e as
heurísticas ficam no disco sem nunca chegar ao modelo.

O `upgrade.sh` faz backup de tudo, remove só o que virou obsoleto, mescla o
`settings.json` preservando as suas permissões, e **verifica se o motor ficou
ligado** — não apenas se os arquivos foram copiados. Sua memória (vault,
episódios, patterns) não é tocada.

O health check deve rodar limpo. Ele é a sua verificação de que a instalação de fato
existe na máquina, e não apenas na documentação.

---

## Primeiros passos

```
@dev                     ativa o agente de desenvolvimento
*help                    lista os comandos do agente ativo
@sm *draft               cria uma story a partir de um épico
/plan-first              rascunha plano antes de tarefa multi-arquivo
```

Fluxo completo de uma story:

```
@sm *draft → @po *validate → @dev *develop → @qa *qa-gate → @devops *push
```

Comece pequeno: ative `@dev`, peça uma tarefa real, e observe o agente consultar as
regras e registrar o que aprendeu. O valor aparece na terceira ou quarta sessão, quando
a memória começa a devolver o que você ensinou.

---

## Segurança

Este pacote passou por um gate de conteúdo que bloqueia credenciais, PII, IPs de
produção, caminhos absolutos, dados de cliente e IDs de conta:

```bash
python3 tools/validate-publish.py .   # exit 0 = limpo
```

**Rode antes de qualquer push**, inclusive nos seus forks. O `.gitignore` não protege
segredo hardcoded *dentro* de um arquivo de conteúdo — só o gate pega isso.

Uma lição que custou caro e vale repassar: **sanitizar o arquivo não sanitiza o
repositório**. O Git guarda cada versão anterior como objeto imutável, então um clone
entrega o commit contaminado junto. Se você vazar algo, histórico novo é a única correção
real — e rotacione a credencial, porque tornar o repo privado não desfaz a exposição.

---

## Licença

Ver `LICENSE`.
