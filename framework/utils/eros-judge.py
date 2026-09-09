#!/usr/bin/env python3
"""
eros-judge.py — LLM-as-judge para o EROS (absorção #5 do gstack, 26-Jun-2026).

O EROS Veredito hoje é auto-avaliação do próprio agente (viés de quem fez).
Este juiz é INDEPENDENTE e barato: pontua a entrega em 3 eixos (clareza,
completude, acionabilidade), escala 1-5, com gate. Cruza com eros-quality.md
(Portão 4 — Revisão).

Juiz:
  default      → claude -p --model claude-haiku-4-5  (rápido, barato)
  --independent → codex exec (GPT-5.5, cross-provider, menos viés, grátis via ChatGPT)

Uso:
  eros-judge.py <arquivo>                 # julga o conteúdo de um arquivo
  eros-judge.py --text "..."              # julga texto direto
  cat entrega.md | eros-judge.py          # julga stdin
  eros-judge.py <arquivo> --independent   # usa GPT-5.5 como juiz
  eros-judge.py <arquivo> --context "para quem / objetivo"

Gate: completude < 3 → exit 1 (BLOQUEADO). Senão exit 0.
"""
import json
import os
import re
import subprocess
import sys

JUDGE_PROMPT = """Você é um JUIZ de qualidade independente e rigoroso. NÃO escreveu a entrega abaixo.
Avalie-a em 3 eixos, escala 1 a 5 (1=péssimo, 3=adequado, 5=excelente):
- clareza: o destinatário entende sem adivinhar?
- completude: cobre tudo que o objetivo exige, sem lacunas?
- acionabilidade: dá para usar/agir sem retrabalho?

Seja crítico — notas 5 só para o que realmente merece. Para cada eixo abaixo de 4, aponte o porquê.
{context}
Responda APENAS com JSON válido, sem texto fora dele, sem fences:
{{"clareza": N, "completude": N, "acionabilidade": N, "pontos_fracos": ["..."], "veredito": "uma frase"}}

===== ENTREGA A JULGAR =====
{content}
"""


def get_content():
    args = sys.argv[1:]
    if "--text" in args:
        i = args.index("--text")
        return args[i + 1] if i + 1 < len(args) else ""
    positional = [a for a in args if not a.startswith("--")]
    # remove valores de flags conhecidas
    skip = set()
    for flag in ("--context", "--text"):
        if flag in args:
            j = args.index(flag)
            if j + 1 < len(args):
                skip.add(args[j + 1])
    positional = [p for p in positional if p not in skip]
    if positional and os.path.isfile(positional[0]):
        return open(positional[0], errors="ignore").read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def get_context():
    args = sys.argv[1:]
    if "--context" in args:
        i = args.index("--context")
        return f"\nContexto da entrega (destinatário/objetivo): {args[i+1]}\n" if i + 1 < len(args) else ""
    return ""


def call_judge(prompt, independent=False):
    if independent:
        cmd = ["codex", "exec", "--skip-git-repo-check", prompt]
        out = subprocess.run(cmd, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=180)
        return out.stdout
    else:
        cmd = ["claude", "-p", prompt, "--model", "claude-haiku-4-5"]
        out = subprocess.run(cmd, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=180)
        return out.stdout


def extract_json(text):
    # remove fences ```json ... ```
    text = re.sub(r"```(?:json)?", "", text)
    # pega o primeiro objeto {...} balanceado de forma simples
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def main():
    content = get_content().strip()
    if not content:
        print("Nada para julgar. Passe um arquivo, --text ou stdin.", file=sys.stderr)
        sys.exit(2)

    independent = "--independent" in sys.argv
    # trunca entregas gigantes (juiz não precisa de tudo para avaliar qualidade)
    content_for_judge = content[:12000]

    prompt = JUDGE_PROMPT.format(context=get_context(), content=content_for_judge)

    judge_name = "GPT-5.5 (codex, independente)" if independent else "Haiku 4.5 (claude -p)"
    print(f"⚖️  Juiz: {judge_name}\n", file=sys.stderr)

    try:
        raw = call_judge(prompt, independent)
    except subprocess.TimeoutExpired:
        print("Juiz expirou (timeout 180s).", file=sys.stderr)
        sys.exit(3)
    except FileNotFoundError as e:
        print(f"CLI do juiz não encontrado: {e}", file=sys.stderr)
        sys.exit(3)

    data = extract_json(raw)
    if not data:
        print("Não consegui parsear o veredito do juiz. Saída crua:", file=sys.stderr)
        print(raw[:500], file=sys.stderr)
        sys.exit(3)

    c = data.get("clareza", 0)
    comp = data.get("completude", 0)
    act = data.get("acionabilidade", 0)
    media = round((c + comp + act) / 3, 1)

    print("EROS JUDGE (independente)")
    print(f"  Clareza:        {c}/5")
    print(f"  Completude:     {comp}/5")
    print(f"  Acionabilidade: {act}/5")
    print(f"  Média:          {media}/5")
    if data.get("pontos_fracos"):
        print("  Pontos fracos:")
        for pf in data["pontos_fracos"][:5]:
            print(f"    - {pf}")
    if data.get("veredito"):
        print(f"  Veredito: {data['veredito']}")

    # Gate (mesma lógica do gstack: completude < 3 bloqueia)
    if comp < 3 or media < 3:
        print("\n  ⛔ BLOQUEADO — completude/média abaixo do mínimo (3). Refazer.")
        sys.exit(1)
    elif media < 4:
        print("\n  ⚠️  CONDICIONAL — adequado mas abaixo do padrão Alto (4). Documentar ressalva.")
        sys.exit(0)
    else:
        print("\n  ✅ APROVADO — atinge o padrão mínimo Alto do EROS.")
        sys.exit(0)


if __name__ == "__main__":
    main()
