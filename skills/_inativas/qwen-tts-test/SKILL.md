---
name: qwen-tts-test
description: "Testa Qwen3-TTS em português brasileiro — benchmark de qualidade, clonagem de voz, comparação com ElevenLabs/ChatterBox. Use para avaliar se Qwen3-TTS é viável como substituto gratuito."
---

# Teste Qwen3-TTS em Português Brasileiro

Skill para avaliar a qualidade do Qwen3-TTS (Alibaba, open-source) em PT-BR e comparar com alternativas.

---

## Pré-requisitos

```bash
# Instalar dependências
pip install torch transformers soundfile numpy

# Verificar GPU (opcional mas recomendado)
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'MPS: {torch.backends.mps.is_available()}')"
```

## Setup Rápido

```python
# qwen_tts_test.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import soundfile as sf
import time

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"

print("Carregando modelo Qwen3-TTS...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Frases de teste em PT-BR (variedade de cenários)
TEST_PHRASES = [
    # Frase simples
    "Olá, eu sou a Segunda-feira, sua assistente de inteligência artificial.",
    # Frase com números e siglas
    "O CPL da campanha caiu para R$8,50 nos últimos 7 dias.",
    # Frase emocional/persuasiva
    "Imagina automatizar todo o seu negócio com IA em menos de uma semana.",
    # Frase técnica
    "O pipeline de automação conecta o webhook do N8N ao banco PostgreSQL via API REST.",
    # Frase longa
    "Nos últimos trinta dias, geramos mais de duzentos leads qualificados usando apenas três campanhas no Meta Ads, com um investimento total de dois mil reais.",
]

results = []
for i, phrase in enumerate(TEST_PHRASES):
    print(f"\n--- Teste {i+1}/{len(TEST_PHRASES)} ---")
    print(f"Texto: {phrase}")

    start = time.time()
    # Gerar áudio (adaptar conforme API do modelo)
    inputs = tokenizer(phrase, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=2048)

    elapsed = time.time() - start
    print(f"Tempo: {elapsed:.2f}s")

    # Salvar áudio
    # NOTA: O formato de output pode variar — verificar documentação do modelo
    output_file = f"qwen_tts_test_{i+1}.wav"
    # sf.write(output_file, audio_array, sample_rate)
    print(f"Salvo: {output_file}")

    results.append({
        "phrase": phrase,
        "time_seconds": round(elapsed, 2),
        "output_file": output_file
    })

print("\n=== RESULTADOS ===")
for r in results:
    print(f"  {r['time_seconds']}s — {r['phrase'][:50]}...")
```

## Critérios de Avaliação

Após gerar os áudios, avaliar manualmente:

| Critério | Score 1-5 | Peso |
|----------|-----------|------|
| **Naturalidade PT-BR** | ? | 30% |
| **Pronúncia de acentos** (ç, ã, é, ó) | ? | 25% |
| **Entonação/prosódia** | ? | 20% |
| **Velocidade adequada** | ? | 10% |
| **Qualidade de áudio** (ruído, artefatos) | ? | 15% |

### Score mínimo para adoção:
- **≥ 3.5/5**: ADOTAR como alternativa ao ElevenLabs para uso geral
- **3.0-3.4**: ADOTAR apenas para uso interno (não para conteúdo público)
- **< 3.0**: DESCARTAR — manter ChatterBox/ElevenLabs

## Teste de Clonagem de Voz

```python
# Clone com apenas 3s de áudio (diferencial do Qwen3-TTS)
REFERENCE_AUDIO = "voz_rudnei_3s.wav"  # Gravar 3s de amostra

# Comparar com ChatterBox (que precisa de 20s+)
# Se qualidade de clone com 3s ≥ 80% da qualidade com 20s → game changer
```

## Comparação Head-to-Head

| Aspecto | Qwen3-TTS | ChatterBox | ElevenLabs | macOS say |
|---------|-----------|------------|------------|-----------|
| Custo | Grátis | Grátis | $$ | Grátis |
| Clone mínimo | 3s | 20s | 30s | N/A |
| PT-BR | TESTAR | Bom | Excelente | OK |
| Latência | TESTAR | Média | Baixa (API) | Baixa |
| Emoção | Sim | Limitado | Sim | Não |
| GPU necessária | Recomendado | Recomendado | Não (API) | Não |

## Resultado Final

Após os testes, atualizar:
1. `@voice-ai-specialist` — confirmar ou remover Qwen3-TTS do stack
2. `@tool-curator` — emitir veredicto oficial (ADOTAR/TESTAR/DESCARTAR)
3. `@cost-optimizer` — calcular economia mensal se substituir ElevenLabs
4. SEGUNDA-FEIRA (`server.py`) — adicionar como opção de TTS se aprovado

## Links

- HuggingFace: https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base
- Demo: https://huggingface.co/spaces/Qwen/Qwen3-TTS
- Coleção: https://huggingface.co/collections/Qwen/qwen3-tts
