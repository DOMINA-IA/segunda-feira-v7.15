#!/usr/bin/env python3
"""
run-routing-battery — Smoke test determinístico das descriptions de skills/agentes.

IMPORTANTE — o que este script NÃO é: não simula o modelo real. O Claude Code
escolhe skill/agente com um LLM lendo a description inteira (semântica, sinônimos,
contexto da conversa). Este script faz matching HEURÍSTICO puramente lexical —
tokeniza o pedido e a description de cada candidato, pontua pela sobreposição de
termos (interseção de conjuntos) e verifica se algum dos "esperado" está no top-3
do ranking. Serve para pegar descriptions fracas (sem os termos que o CEO usaria)
antes que isso vire um miss de roteamento real — não para prever com precisão o
que o modelo faria.

Uso:  python3 run-routing-battery.py [caminho/para/routing-battery.yaml]
Exit code: 0 sempre (é um smoke test informativo, não um gate rígido — quem decide
           se o score é aceitável é o framework_health_check.py, que chama isto
           via subprocess com timeout).
"""

import re
import sys
import unicodedata
from pathlib import Path

HOME = Path.home()
SKILLS_DIR = HOME / ".claude" / "skills"
AGENTS_DIRS = [HOME / ".claude" / "agents" / "meta", HOME / ".claude" / "agents" / "ops"]
# sm/po não têm canônica em ~/.claude/agents/ (decisão pendente, ver CLAUDE.md) —
# vivem só no wrapper. Lidos aqui só para leitura/matching; NUNCA editar este arquivo.
def _descobre_wrappers():
    """Agentes que existem SÓ na camada wrapper (sem canônica em agents/).

    Era uma lista fixa com 2 nomes (sm, po) enquanto 27 agentes viviam só aqui —
    @sf-master, @devops, @qa, @ux-design-expert e outros 21 nunca entravam como
    candidatos, então nenhum caso podia acertá-los. Mesma classe do glob "*.md"
    que carregava 0 skills: inventário fixo descola da realidade.
    """
    base = HOME / ".claude" / "commands" / "segunda-feira" / "agents"
    canon = HOME / ".claude" / "agents"
    achados = {}
    if not base.is_dir():
        return achados
    for f in sorted(base.glob("*.md")):
        nome = f.stem
        if (canon/"meta"/f"{nome}.md").exists() or (canon/"ops"/f"{nome}.md").exists():
            continue                      # tem canônica; já entra pelo caminho normal
        try:
            if "DERIVADO" in f.read_text(errors="ignore")[:2000]:
                continue                  # camada derivada, não é fonte
        except Exception:
            continue
        achados[nome] = f
    return achados


WRAPPER_AGENTS = _descobre_wrappers()
DEFAULT_BATTERY = Path(__file__).parent / "routing-battery.yaml"

STOPWORDS = {
    # PT-BR comuns
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "um", "uma", "uns", "umas",
    "para", "pra", "pro", "com", "sem", "que", "no", "na", "nos", "nas", "os", "as",
    "por", "ou", "se", "é", "isso", "essa", "esse", "essas", "esses", "esta", "este",
    "estas", "estes", "já", "não", "sim", "mais", "menos", "muito", "vai", "vou",
    "vamos", "quero", "preciso", "precisa", "vou", "tá", "ta", "vou", "meu", "minha",
    "seu", "sua", "dele", "dela", "ao", "aos", "à", "às", "num", "numa", "quando",
    "onde", "como", "porque", "então", "aí", "lá", "aqui", "só", "ainda", "também",
    "até", "sobre", "entre", "depois", "antes", "hoje", "agora", "todo", "toda",
    "todos", "todas", "cada", "esse", "isso", "aquilo", "algo", "alguma", "algum",
    # EN comuns (descriptions misturam termos técnicos em inglês)
    "the", "a", "for", "and", "or", "of", "to", "in", "on", "is", "use", "not",
    "this", "that", "with", "from", "via",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
DESCRIPTION_KV_RE = re.compile(r'^description:\s*"?(.*?)"?\s*$', re.M)
WHEN_TO_USE_RE = re.compile(r"whenToUse:\s*(\|)?[ \t]*\n?(.*?)\n(?=\s{0,2}\S+:)", re.S)


def strip_accents(s):
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def tokenize(text):
    """Tokeniza: minúsculas, sem acento, só \\w+, remove stopwords e tokens curtos."""
    text = strip_accents(text.lower())
    raw = re.findall(r"[a-z0-9]+", text)
    return {t for t in raw if t not in STOPWORDS and len(t) > 2}


def extract_frontmatter_description(text):
    """Extrai o campo `description:` do frontmatter YAML (parser leve, sem libs)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return ""
    fm = m.group(1)
    dm = DESCRIPTION_KV_RE.search(fm)
    if dm and dm.group(1).strip():
        return dm.group(1).strip()
    # description em bloco `description: |` (multi-linha, raro nos arquivos atuais)
    bm = re.search(r"description:\s*\|[ \t]*\n((?:[ \t]+.+\n?)+)", fm)
    if bm:
        return " ".join(l.strip() for l in bm.group(1).splitlines() if l.strip())
    return ""


def extract_when_to_use(text):
    """Fallback para agentes estilo BMAD (sm/po) sem `description` no frontmatter."""
    m = WHEN_TO_USE_RE.search(text)
    if not m:
        return ""
    block = m.group(2)
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    return " ".join(lines)


def load_candidates():
    """Retorna dict {id: description} — skills sem prefixo, agentes com @."""
    candidates = {}

    # Formato obrigatório do Claude Code é <nome>/SKILL.md — .md solto na raiz
    # não é carregado (descoberto no /doctor de 01-Ago-2026). Este glob ainda
    # procurava "*.md" e carregava ZERO skills, então a bateria vinha roteando
    # só entre agentes e reprovava todo caso cuja resposta é uma skill.
    if SKILLS_DIR.is_dir():
        for f in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            if f.parent.name.startswith("_"):   # _inativas, _archived, _reference
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            candidates[f.parent.name] = extract_frontmatter_description(text)

    for d in AGENTS_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            text = f.read_text(encoding="utf-8", errors="ignore")
            desc = extract_frontmatter_description(text)
            candidates[f"@{f.stem}"] = desc

    for name, path in WRAPPER_AGENTS.items():
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
            desc = extract_when_to_use(text)
            candidates[f"@{name}"] = desc

    return candidates


def rank(pedido_tokens, candidates_tokens):
    """Ordena candidatos por sobreposição de termos (desc), desempate por id (asc)."""
    scored = []
    for cid, ctoks in candidates_tokens.items():
        score = len(pedido_tokens & ctoks)
        scored.append((score, cid))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored


def load_battery(path):
    """Parser YAML leve pra evitar dependência de PyYAML (só suporta o formato
    usado em routing-battery.yaml: lista de mapas com pedido/esperado/motivo)."""
    try:
        import yaml
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except ImportError:
        return _load_battery_fallback(path)


def _load_battery_fallback(path):
    cases = []
    current = None
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("- pedido:"):
            if current:
                cases.append(current)
            current = {"pedido": line.split(":", 1)[1].strip().strip('"')}
        elif line.strip().startswith("esperado:"):
            raw = line.split(":", 1)[1].strip()
            items = re.findall(r'"([^"]+)"', raw)
            current["esperado"] = items
        elif line.strip().startswith("motivo:"):
            current["motivo"] = line.split(":", 1)[1].strip().strip('"')
    if current:
        cases.append(current)
    return cases


def main():
    battery_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BATTERY
    cases = load_battery(battery_path)
    candidates = load_candidates()
    candidates_tokens = {cid: tokenize(desc) for cid, desc in candidates.items()}

    total = len(cases)
    hits = 0
    misses = []

    for case in cases:
        pedido = case["pedido"]
        esperado = case["esperado"]
        pedido_tokens = tokenize(pedido)
        ranking = rank(pedido_tokens, candidates_tokens)
        top3 = [cid for _, cid in ranking[:3]]
        if esperado == ["-"]:            # controle negativo: pedido conversacional não deve cair em skill
            # 1 token em comum não é rota (qualquer "linha", "arquivo" casa alguma skill);
            # só conta como miss se uma skill entrou no top-3 com score >= 2.
            top3_scored = ranking[:3]
            hit = not any((not cid.startswith("@")) and score >= 2 for score, cid in top3_scored)
        else:
            hit = any(e in top3 for e in esperado)
        if hit:
            hits += 1
        else:
            misses.append({
                "pedido": pedido,
                "esperado": esperado,
                "top3": [(cid, score) for score, cid in ranking[:3]],
                "motivo": case.get("motivo", ""),
            })

    print("═══ ROTEAMENTO BATTERY — smoke test de descriptions (heurístico, não é o modelo real) ═══")
    n_skills = len([c for c in candidates if not c.startswith("@")])
    print(f"Candidatos carregados: {len(candidates)} ({n_skills} skills + {len(candidates) - n_skills} agentes)")
    print(f"\nScore: {hits}/{total}\n")

    if misses:
        print(f"─── {len(misses)} MISS(ES) ───")
        for m in misses:
            print(f"\n✗ pedido: \"{m['pedido']}\"")
            print(f"  esperado: {m['esperado']}  ({m['motivo']})")
            print(f"  top-3 real: {m['top3']}")
    else:
        print("Nenhum miss — todos os casos acertaram o top-3.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
