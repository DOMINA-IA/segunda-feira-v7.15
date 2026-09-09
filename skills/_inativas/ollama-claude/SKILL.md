---
name: ollama-claude
description: "Configura Claude Code para rodar com modelos locais via Ollama — custo zero, privacidade total. Instala Ollama, baixa modelo, configura env vars e testa. Use para desenvolvimento sem gastar créditos Anthropic."
---

# Claude Code + Ollama — Modo Custo Zero

Roda a interface do Claude Code com modelos locais gratuitos via Ollama. Ideal para prototipagem, ensino e desenvolvimento sem gastar créditos Anthropic.

---

## Pré-requisitos

- macOS, Linux ou Windows (WSL)
- RAM: mínimo 8GB (16GB+ recomendado para modelos maiores)
- Disco: 10-30GB livres (dependendo do modelo)

## Instalação Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verificar
ollama --version
```

## Escolher Modelo

| Modelo | Tamanho | RAM Necessária | Qualidade | Recomendação |
|--------|---------|---------------|-----------|-------------|
| `gemma4:e2b` | ~4GB | 8GB | Básica | Mínimo viável |
| `gemma4:e4b` | ~8GB | 12GB | Boa | Dev rápido |
| `gemma4:26b` | ~14GB | 20GB | Ótima | Produção local |
| `gemma4:31b` | ~19GB | 24GB | Melhor | Melhor qualidade |
| `qwen3-coder:free` | Via OpenRouter | N/A | Boa para código | Via API free |

```bash
# Baixar modelo (escolher UM)
ollama pull gemma4:e4b      # Recomendado para a maioria
# ou
ollama pull gemma4:31b      # Se tiver RAM suficiente

# Testar
ollama run gemma4:e4b "Olá, funciona em português?"
```

## Configurar Claude Code

### Opção 1: Variáveis de ambiente (sessão atual)

```bash
# Configurar
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_AUTH_TOKEN=ollama
export ANTHROPIC_MODEL=gemma4:e4b

# Iniciar Claude Code com modelo local
claude
```

### Opção 2: Settings.json (permanente)

```bash
# Editar settings
cat > ~/.claude/settings.local.json << 'EOF'
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:11434",
    "ANTHROPIC_AUTH_TOKEN": "ollama",
    "ANTHROPIC_MODEL": "gemma4:e4b"
  }
}
EOF
```

> **IMPORTANTE**: Usar `settings.local.json` (não `settings.json`) para não afetar a configuração principal. Para voltar ao Claude normal, basta remover este arquivo.

### Opção 3: OpenRouter (modelos free na nuvem)

```bash
# Sem Ollama — usa modelos gratuitos via OpenRouter
export ANTHROPIC_BASE_URL=https://openrouter.ai/api/v1
export ANTHROPIC_AUTH_TOKEN=sua_chave_openrouter
export ANTHROPIC_MODEL=qwen/qwen3-coder:free

claude
```

Limite free: ~50 interações/dia.

## Qwen Code (Alternativa ao Claude Code)

Agente de terminal otimizado para modelos Qwen:

```bash
# Instalar
npm install -g @qwen-code/qwen-code@latest

# Usar
qwen-code

# Modelo Qwen3.6-Plus:
# - 1M context window
# - Raciocínio contínuo entre etapas
# - FREE no OpenRouter via KiloCode
```

## Servidor GPU Dedicado (Avançado)

Para equipes ou uso intenso, rodar Ollama em servidor com GPU:

```bash
# No servidor (Docker + GPU NVIDIA)
docker run -d --gpus all \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# + Open WebUI para interface visual
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main

# Do seu Mac, apontar para o servidor
export ANTHROPIC_BASE_URL=http://IP_DO_SERVIDOR:11434
```

## Voltar ao Claude Normal

```bash
# Remover overrides
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
unset ANTHROPIC_MODEL

# Ou remover settings local
rm ~/.claude/settings.local.json

# Claude Code volta a usar a API Anthropic normalmente
claude
```

## Limitações vs Claude API

| Aspecto | Ollama Local | Claude API |
|---------|-------------|------------|
| Qualidade | Boa (depende do modelo) | Superior |
| Velocidade | Depende do hardware | Rápida |
| Context window | ~8K-32K (modelo dependente) | 200K (Sonnet) / 1M (Opus) |
| Tools/MCP | Suporte limitado | Completo |
| Custo | Zero | Por token |
| Privacidade | Total (local) | Cloud |

**Recomendação**: Usar Ollama para prototipagem e tarefas simples. Claude API para produção e tarefas complexas.

## Troubleshooting

| Problema | Solução |
|----------|---------|
| "connection refused" | Verificar se Ollama está rodando: `ollama serve` |
| Muito lento | Usar modelo menor ou verificar se GPU está sendo usada |
| Erro de memória | Fechar outros apps ou usar modelo menor |
| Qualidade ruim | Modelo muito pequeno — tentar 26b ou 31b |
