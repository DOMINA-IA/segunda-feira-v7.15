---
name: karpathy-wiki
description: "Cria um 'segundo cérebro' no estilo Karpathy — transforma pasta de arquivos brutos em wiki organizada com índice navegável. Zero infra, 95% menos tokens. Use para bases de conhecimento pessoais ou de clientes."
---

# Segundo Cérebro com IA — Método Karpathy Wiki

Transforma uma pasta caótica de arquivos em uma wiki organizada, navegável e otimizada para consumo por LLMs.

> Baseado no gist do Andrej Karpathy: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

---

## Estrutura Final

```
projeto/
├── raw/          # Conteúdo bruto (jogar tudo aqui)
│   ├── screenshot_001.png
│   ├── transcricao_call.txt
│   ├── artigo_interessante.md
│   └── ...
├── wiki/         # Páginas organizadas (1 tema = 1 arquivo)
│   ├── automação-n8n.md
│   ├── precificação-saas.md
│   ├── copywriting-frameworks.md
│   └── ...
├── index.md      # Índice master com links e descrições
├── log.md        # Registro cronológico de adições
└── CLAUDE.md     # Regras para o LLM manter a wiki
```

## Passo 1: Criar Estrutura

```bash
# Criar estrutura base
mkdir -p meu-cerebro/{raw,wiki}

# Criar CLAUDE.md com regras
cat > meu-cerebro/CLAUDE.md << 'RULES'
# Wiki Pessoal — Regras de Manutenção

## Ao receber comando "processar raw/"
1. Ler cada arquivo em raw/ que ainda não foi processado
2. Para cada arquivo:
   a. Identificar o tema principal
   b. Se tema já existe em wiki/: ATUALIZAR a página existente
   c. Se tema é novo: criar nova página em wiki/
3. Atualizar index.md com novas páginas
4. Registrar em log.md: data + arquivo processado + ação tomada
5. NÃO deletar arquivos de raw/ (manter como backup)

## Formato de página wiki/
```
# [Título do Tema]
> Atualizado: [DATA] | Fontes: [lista de arquivos raw]

## Resumo
[3-5 frases densas — sem fluff]

## Pontos-Chave
- [ponto 1]
- [ponto 2]
- ...

## Ações Práticas
- [o que fazer com esta informação]

## Relacionados
- [[link para página relacionada]]
```

## Regras Gerais
- Máximo 500 palavras por página
- Linguagem densa: cada frase carrega informação
- Sem repetição entre páginas (referenciar ao invés de duplicar)
- Acentuação perfeita em português
- Se informação conflita com página existente: atualizar com a mais recente, marcar [ATUALIZADO]
RULES

# Criar index.md inicial
echo "# Índice da Wiki\n\n_Nenhuma página criada ainda._" > meu-cerebro/index.md

# Criar log.md inicial
echo "# Log de Processamento\n" > meu-cerebro/log.md
```

## Passo 2: Jogar Conteúdo em raw/

```bash
# Copiar arquivos de qualquer fonte
cp ~/Downloads/artigo.pdf meu-cerebro/raw/
cp ~/Desktop/screenshot.png meu-cerebro/raw/
cp ~/notas/transcricao.txt meu-cerebro/raw/

# Ou usar Obsidian Web Clipper para salvar direto de Chrome
# Extension: https://obsidian.md/clipper
```

## Passo 3: Processar com LLM

No Claude Code (ou qualquer LLM com acesso a arquivos):

```
Processe todos os arquivos em raw/ que ainda não foram processados.
Siga as regras do CLAUDE.md.
```

O LLM vai:
1. Ler cada arquivo em `raw/`
2. Extrair tema e informação densa
3. Criar/atualizar páginas em `wiki/`
4. Atualizar `index.md`
5. Registrar em `log.md`

## Passo 4: Consultar

```
Consulte a wiki sobre [tema].
```

O LLM lê `index.md` → encontra página relevante → lê → responde com contexto completo.

**Resultado**: Resposta fundamentada com ~95% menos tokens do que se tivesse que ler todos os arquivos brutos.

---

## Templates de index.md

### Pessoal
```markdown
# Meu Segundo Cérebro

## Por Categoria
### Negócios
- [Precificação SaaS](wiki/precificação-saas.md) — modelos, benchmarks, erros comuns
- [Copywriting](wiki/copywriting-frameworks.md) — AIDA, PAS, frameworks testados

### Tecnologia
- [Automação N8N](wiki/automação-n8n.md) — workflows validados, gotchas
- [Claude Code](wiki/claude-code-dicas.md) — otimização, skills, atalhos

### Mercado
- [Concorrentes](wiki/análise-concorrentes.md) — quem faz o quê, diferenciação
```

### Empresarial
```markdown
# Knowledge Base [Empresa]

## Processos
- [Onboarding Cliente](wiki/onboarding.md) — checklist, templates, SLA

## Produtos
- [Produto A](wiki/produto-a.md) — features, pricing, objeções comuns

## Clientes
- [Perfil ICP](wiki/icp.md) — avatar, dores, objeções, canais
```

---

## Dicas Avançadas

1. **Obsidian como editor**: Instalar Obsidian, apontar vault para a pasta da wiki. Navegação por links instantânea.

2. **Web Clipper**: Extensão Chrome do Obsidian salva qualquer página direto em `raw/`.

3. **Batch processing**: Acumular 10-20 arquivos em `raw/` antes de processar (mais eficiente).

4. **Versionamento**: `git init` na pasta. Cada processamento = 1 commit. Histórico completo.

5. **Escalar**: Se wiki passar de 200 páginas, considerar migrar para CORTEX-Lite (FTS5) ou RAG completo (consultar @rag-architect).

## Resultado Real (INEMA)

Um membro do INEMA transformou:
- **Input**: 383 arquivos + 130 transcrições de reuniões
- **Output**: Wiki compacta com páginas temáticas
- **Economia**: ~95% menos tokens por consulta
- **Tempo de setup**: ~2 horas
