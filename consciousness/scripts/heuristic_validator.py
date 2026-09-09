#!/usr/bin/env python3
"""Validação de heurísticas por evidência discriminativa.

Substitui o contador de coocorrência que vigorou até 15-Jul-2026 e que inflou
89,5% do pool para confidence >=0.9. O mecanismo antigo pegava as 5 primeiras
palavras >4 chars da heurística e contava substring no JSON inteiro do episódio;
como "quando" e "sempre" têm 6 caracteres e abrem quase toda heurística em
português, praticamente qualquer episódio do mesmo agente validava qualquer
heurística daquele agente.

O que muda aqui:
  1. Stopwords PT removidas — "quando"/"sempre" deixam de ser sinal.
  2. IDF calculado sobre o corpus real — termo que aparece em todo episódio
     vale ~0; termo raro carrega a evidência.
  3. Só campos semânticos entram (summary, lessons, valence.reason) — não o
     JSON inteiro, que contém agent/id/timestamp e casava por acidente.
  4. Word boundary — "test" deixa de casar com "contest".
  5. Threshold por massa de IDF, não por contagem de palavras.
  6. Teto por procedência: evidência declarada pelo agente chega a 0.95;
     evidência inferida por texto para em 0.85. Sem declaração não há dogma.
"""
import json
import math
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
EPISODIC_DIR = HOME / "consciousness" / "memory" / "episodic"
HEURISTICS_PATH = HOME / "consciousness" / "memory" / "procedural" / "heuristics.jsonl"
# Cemitério auditável: o que foi refutado e por quê. Sem isto, o agente recria
# amanhã a heurística que o sistema acabou de derrubar.
RETIRED_PATH = HOME / "consciousness" / "memory" / "procedural" / "heuristics-retired.jsonl"

# Palavras funcionais do português com >4 chars: passavam pelo filtro antigo e
# apareciam em quase todo texto, produzindo match sem significado.
STOPWORDS_PT = {
    "quando", "sempre", "porque", "antes", "depois", "entao", "então", "assim",
    "fazer", "feito", "estar", "sendo", "ainda", "apenas", "todos", "todas",
    "cada", "outro", "outra", "mesmo", "mesma", "muito", "muita", "pouco",
    "sobre", "entre", "contra", "durante", "atraves", "através", "usar",
    "usando", "deve", "devem", "pode", "podem", "precisa", "precisam",
    "verificar", "checar", "conferir", "garantir", "evitar", "nunca", "jamais",
    "porem", "porém", "contudo", "todavia", "tambem", "também", "melhor",
    "pior", "maior", "menor", "primeiro", "ultimo", "último", "novo", "nova",
    "antigo", "antiga", "isso", "isto", "aquilo", "esse", "essa", "este",
    "esta", "aquele", "aquela", "qualquer", "algum", "alguma", "nenhum",
    "nenhuma", "porque", "pois", "logo", "portanto", "seja", "sejam", "fica",
    "ficar", "ficam", "vai", "vao", "vão", "tem", "tenha", "tenham", "havia",
    "houve", "sera", "será", "seria", "foram", "forem", "estava", "estao",
    "estão", "aplicar", "aplicando", "rodar", "rodando", "executar", "criar",
    "criando", "gerar", "gerando", "salvar", "abrir", "fechar", "trabalho",
    "tarefa", "tarefas", "processo", "sistema", "arquivo", "arquivos",
}

# Procedência da evidência. Declarada é o agente afirmando que aplicou a
# heurística; inferida é o texto do episódio parecendo com o texto dela.
CEILING_DECLARED = 0.95
CEILING_INFERRED = 0.85
STEP_DECLARED = 0.08
STEP_INFERRED = 0.03
PENALTY_FAILURE = 0.12
FLOOR = 0.1

# Fração da massa de IDF da heurística que precisa aparecer no episódio.
# Calibrado em 15-Jul contra 1936 episódios / 554 heurísticas: ver
# --calibrate para o histograma que sustenta este valor.
MIN_IDF_COVERAGE = 0.45
MIN_MATCHED_TERMS = 2


def strip_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def tokenize(text):
    """Termos discriminativos: sem acento, sem stopword, >=4 chars."""
    text = strip_accents((text or "").lower())
    raw = re.findall(r"[a-z0-9_\-\.]{4,}", text)
    return [
        t for t in raw
        if t not in STOPWORDS_PT and strip_accents(t) not in STOPWORDS_PT
    ]


def subfield(ep, parent, child):
    """Lê ep[parent][child] tolerando schema variável.

    O corpus tem episódios em que `valence` é dict e outros em que é float
    (score solto). Assumir o formato quebra a varredura inteira no primeiro
    episódio legado.
    """
    node = ep.get(parent)
    if isinstance(node, dict):
        value = node.get(child, "")
        return value if isinstance(value, str) else ""
    return ""


def episode_text(ep):
    """Só o que o agente de fato escreveu — não o envelope do JSON.

    O validador antigo usava json.dumps(ep), então agent/id/timestamp/status
    entravam no corpo pesquisável e casavam sozinhos.
    """
    lessons = ep.get("lessons") if isinstance(ep.get("lessons"), dict) else {}
    parts = [
        ep.get("summary", "") if isinstance(ep.get("summary"), str) else "",
        lessons.get("what_worked", ""),
        lessons.get("what_failed", ""),
        lessons.get("heuristic", ""),
        subfield(ep, "valence", "reason"),
        subfield(ep, "context", "task"),
    ]
    return " ".join(p for p in parts if isinstance(p, str) and p)


def load_episodes():
    episodes = []
    for path in sorted(EPISODIC_DIR.glob("*.jsonl")):
        # Arquivos de teste poluem o corpus de produção (achado da auditoria 15-Jul).
        if path.stem.startswith("test-"):
            continue
        for line in path.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                episodes.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # 3,1% do corpus tem escape inválido; ignorar é melhor que abortar
    return episodes


def build_idf(episodes):
    """IDF sobre o corpus real: termo comum vale ~0, termo raro carrega evidência."""
    n_docs = len(episodes) or 1
    doc_freq = defaultdict(int)
    for ep in episodes:
        for term in set(tokenize(episode_text(ep))):
            doc_freq[term] += 1
    return {t: math.log(n_docs / (1 + df)) for t, df in doc_freq.items()}, n_docs


def score_match(heur_terms, ep_terms_set, idf, default_idf):
    """Cobertura da massa de IDF da heurística presente no episódio.

    Contagem simples de palavras tratava "quando" e "crm_activities" como
    evidência equivalente. Aqui o peso é a raridade do termo.
    """
    if not heur_terms:
        return 0.0, []
    total = sum(idf.get(t, default_idf) for t in heur_terms)
    if total <= 0:
        return 0.0, []
    matched = [t for t in heur_terms if t in ep_terms_set]
    got = sum(idf.get(t, default_idf) for t in matched)
    return got / total, matched


def is_source_episode(ep, heuristic):
    """O episódio que PARIU a heurística não pode confirmá-la.

    `record-episode.sh --heuristic "texto"` grava o texto em lessons.heuristic
    e cria a heurística a partir dali. O episódio-fonte contém portanto o texto
    literal da heurística e casa com cobertura 1.0 — foi o que produziu 537/554
    heurísticas com match perfeito na primeira calibração. Confirmar-se pelo
    próprio nascimento é circular: evidência tem de vir de um episódio POSTERIOR
    e DISTINTO, onde a heurística se mostrou verdadeira de novo.
    """
    if heuristic.get("source_episode") and ep.get("id") == heuristic["source_episode"]:
        return True
    # Fallback: episódios antigos podem não ter source_episode preenchido.
    ep_heur = subfield(ep, "lessons", "heuristic").strip()
    return bool(ep_heur) and ep_heur == (heuristic.get("heuristic", "") or "").strip()



def _cita(campo, heur_id):
    """True se o campo (id completo, '#handle', lista ou string com vários) cita heur_id."""
    if not campo:
        return False
    itens = campo if isinstance(campo, list) else re.split(r"[,\s]+", str(campo))
    hid = heur_id.strip()
    for it in itens:
        it = str(it).strip().lstrip("#")
        if not it:
            continue
        if it == hid or (len(it) >= 8 and hid.endswith(it)):
            return True
    return False


def find_evidence(heuristic, episodes_by_agent, idf, default_idf, since=None):
    """Procura evidência para uma heurística. Declarada tem precedência."""
    agent = heuristic.get("agent", "")
    heur_terms = list(dict.fromkeys(tokenize(heuristic.get("heuristic", ""))))
    heur_id = heuristic.get("id", "")

    declared, inferred = [], []
    for ep in episodes_by_agent.get(agent, []):
        if is_source_episode(ep, heuristic):
            continue
        if since:
            ts = ep.get("timestamp", "")
            try:
                if datetime.fromisoformat(ts.replace("Z", "+00:00")) < since:
                    continue
            except (ValueError, AttributeError):
                continue

        result = subfield(ep, "outcome", "result")

        # Evidência declarada: o agente afirma qual heurística aplicou.
        # Declarada: o agente cita o id completo OU o #handle curto (8 hex finais) que o
        # router injeta — 07-Set: 11 de 13 citações eram handles e nenhuma era reconhecida.
        applied = ep.get("heuristic_applied") or subfield(ep, "lessons", "heuristic_applied")
        failed_h = ep.get("heuristic_failed") or subfield(ep, "lessons", "heuristic_failed")
        if heur_id and _cita(applied, heur_id):
            declared.append((ep, "success", 1.0, heur_terms))
            continue
        if heur_id and _cita(failed_h, heur_id):
            declared.append((ep, "failure", 1.0, heur_terms))
            continue

        if len(heur_terms) < MIN_MATCHED_TERMS:
            continue
        ep_terms = set(tokenize(episode_text(ep)))
        coverage, matched = score_match(heur_terms, ep_terms, idf, default_idf)
        if coverage >= MIN_IDF_COVERAGE and len(matched) >= MIN_MATCHED_TERMS:
            inferred.append((ep, result, coverage, matched))

    return declared, inferred


def apply_evidence(heuristic, declared, inferred, now_iso):
    """Aplica evidência à confidence. Retorna (mudou, método, delta)."""
    conf = heuristic.get("confidence", 0.5)
    original = conf
    method = None

    successes_d = [d for d in declared if d[1] == "success"]
    failures_d = [d for d in declared if d[1] == "failure"]
    successes_i = [i for i in inferred if i[1] == "success"]
    failures_i = [i for i in inferred if i[1] == "failure"]

    # Contra-evidência primeiro: uma heurística contradita não deve subir no
    # mesmo ciclo por ter casado com outro episódio bem-sucedido.
    if failures_d or failures_i:
        conf = max(conf - PENALTY_FAILURE, FLOOR)
        heuristic["times_failed"] = heuristic.get("times_failed", 0) + len(failures_d) + len(failures_i)
        method = "declared_failure" if failures_d else "inferred_failure"
    elif successes_d:
        conf = min(conf + STEP_DECLARED, CEILING_DECLARED)
        heuristic["times_validated"] = heuristic.get("times_validated", 1) + 1
        method = "declared"
    elif successes_i:
        conf = min(conf + STEP_INFERRED, CEILING_INFERRED)
        heuristic["times_validated"] = heuristic.get("times_validated", 1) + 1
        method = "inferred"
    else:
        return False, None, 0.0

    heuristic["confidence"] = round(conf, 4)
    heuristic["last_validated"] = now_iso
    heuristic["validation_method"] = method
    return True, method, round(conf - original, 4)


def recalibrate(heuristics, episodes, verbose=False):
    """Recalcula do zero a confidence merecida, varrendo todo o histórico.

    As confidences atuais foram produzidas pelo contador de palavras: são um
    passivo, não uma medição. Reconstruir contra o corpus real é a única forma
    de saber quanto cada heurística de fato merece.
    """
    idf, n_docs = build_idf(episodes)
    default_idf = math.log(n_docs / 1)

    by_agent = defaultdict(list)
    for ep in episodes:
        by_agent[ep.get("agent", "")].append(ep)

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = []

    for h in heuristics:
        before = h.get("confidence", 0.5)
        declared, inferred = find_evidence(h, by_agent, idf, default_idf)

        n_ok = len([d for d in declared if d[1] == "success"]) + len([i for i in inferred if i[1] == "success"])
        n_fail = len([d for d in declared if d[1] == "failure"]) + len([i for i in inferred if i[1] == "failure"])
        n_declared = len(declared)

        # Base 0.5 = heurística registrada, ainda não corroborada.
        # Sem evidência alguma, PRESERVA a confidence atual (que carrega o decay
        # por tempo). Reconstruir de 0.5 apagava o decay a cada ciclo — 05-Set-2026:
        # 242 heurísticas decaídas voltaram a 0.50 em uma execução.
        earned = 0.5 if (n_ok or n_fail) else min(float(before), 0.5)
        ceiling = CEILING_DECLARED if n_declared else CEILING_INFERRED
        step = STEP_DECLARED if n_declared else STEP_INFERRED
        earned = min(earned + step * n_ok, ceiling)
        earned = max(earned - PENALTY_FAILURE * n_fail, FLOOR)

        report.append({
            "id": h.get("id", ""),
            "agent": h.get("agent", ""),
            "text": (h.get("heuristic", "") or "")[:70],
            "before": before,
            "after": round(earned, 4),
            "delta": round(earned - before, 4),
            "evidence_ok": n_ok,
            "evidence_fail": n_fail,
            "declared": n_declared,
            "old_times_validated": h.get("times_validated", 1),
        })

        h["confidence"] = round(earned, 4)
        h["times_validated"] = max(n_ok, 1)
        h["times_failed"] = n_fail
        h["validation_method"] = "declared" if n_declared else ("inferred" if n_ok else "unvalidated")
        h["recalibrated_at"] = now_iso

    return report


def consolidate_incremental(days=7, dry_run=False):
    """Passo de validação do consolidate.sh noturno.

    Olha só a janela recente e ajusta confidence de quem tem evidência nova.
    Imprime "<validadas> <depreciadas>" — contrato que o consolidate.sh consome.
    """
    from datetime import timedelta

    episodes = load_episodes()
    heuristics = [
        json.loads(l) for l in HEURISTICS_PATH.read_text().splitlines() if l.strip()
    ]
    idf, n_docs = build_idf(episodes)
    default_idf = math.log(n_docs / 1)

    by_agent = defaultdict(list)
    for ep in episodes:
        by_agent[ep.get("agent", "")].append(ep)

    since = datetime.now(timezone.utc) - timedelta(days=days)
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    validated = 0
    for h in heuristics:
        declared, inferred = find_evidence(h, by_agent, idf, default_idf, since=since)
        if not declared and not inferred:
            continue
        changed, _method, _delta = apply_evidence(h, declared, inferred, now_iso)
        if changed:
            validated += 1

    # Depreciar só quem foi REFUTADO com massa de evidência — não quem apenas
    # nunca se repetiu. Não-corroborada (0.5) é o estado natural da maioria.
    kept, retired = [], []
    for h in heuristics:
        if h.get("confidence", 0.5) < 0.3 and h.get("times_failed", 0) >= 3:
            h["retired_at"] = now_iso
            h["retired_reason"] = f"refutada por {h.get('times_failed', 0)} episódios de falha"
            retired.append(h)
            continue
        kept.append(h)

    if not dry_run:
        with HEURISTICS_PATH.open("w") as f:
            for h in kept:
                f.write(json.dumps(h, ensure_ascii=False) + "\n")
        # Heurística refutada é aprendizado ("isto não funciona"), não lixo:
        # deletar apaga a lição e deixa o agente livre para recriá-la amanhã.
        if retired:
            with RETIRED_PATH.open("a") as f:
                for h in retired:
                    f.write(json.dumps(h, ensure_ascii=False) + "\n")

    print(f"{validated} {len(retired)}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Validação de heurísticas por evidência discriminativa")
    p.add_argument("--calibrate", action="store_true", help="histograma de cobertura IDF, sem escrever")
    p.add_argument("--dry-run", action="store_true", help="mostra a recalibração sem gravar")
    p.add_argument("--apply", action="store_true", help="grava a recalibração em heuristics.jsonl")
    p.add_argument("--consolidate", type=int, metavar="DAYS",
                   help="passo incremental do consolidate.sh; imprime '<validadas> <depreciadas>'")
    args = p.parse_args()

    if args.consolidate:
        consolidate_incremental(days=args.consolidate, dry_run=args.dry_run)
        return

    episodes = load_episodes()
    heuristics = [
        json.loads(l) for l in HEURISTICS_PATH.read_text().splitlines() if l.strip()
    ]

    if args.calibrate:
        idf, n_docs = build_idf(episodes)
        default_idf = math.log(n_docs / 1)
        by_agent = defaultdict(list)
        for ep in episodes:
            by_agent[ep.get("agent", "")].append(ep)

        print(f"corpus: {n_docs} episódios | {len(heuristics)} heurísticas | vocab {len(idf)}")
        print(f"\nIDF dos termos que o mecanismo antigo tratava como evidência:")
        for t in ["quando", "sempre", "teste", "deletar", "crm_activities", "traefik", "sqlite"]:
            v = idf.get(t)
            print(f"  {t:16s} idf={v:.3f}" if v is not None else f"  {t:16s} (fora do corpus)")

        buckets = defaultdict(int)
        for h in heuristics:
            terms = list(dict.fromkeys(tokenize(h.get("heuristic", ""))))
            best = 0.0
            for ep in by_agent.get(h.get("agent", ""), []):
                if is_source_episode(ep, h):
                    continue  # circular: ver is_source_episode
                cov, _ = score_match(terms, set(tokenize(episode_text(ep))), idf, default_idf)
                best = max(best, cov)
            buckets[round(best, 1)] += 1
        print("\ncobertura IDF máxima por heurística, EXCLUÍDO o episódio-fonte (histograma):")
        for k in sorted(buckets):
            print(f"  {k:.1f}: {'█' * min(buckets[k], 60)} {buckets[k]}")
        return

    if args.dry_run or args.apply:
        report = recalibrate(heuristics, episodes)
        subiu = [r for r in report if r["delta"] > 0.01]
        desceu = [r for r in report if r["delta"] < -0.01]
        igual = [r for r in report if abs(r["delta"]) <= 0.01]
        sem_ev = [r for r in report if r["evidence_ok"] == 0 and r["evidence_fail"] == 0]

        print(f"RECALIBRAÇÃO {'(dry-run)' if args.dry_run else '(APLICADA)'}")
        print(f"  total: {len(report)} | subiu: {len(subiu)} | desceu: {len(desceu)} | estável: {len(igual)}")
        print(f"  sem evidência alguma no corpus: {len(sem_ev)} ({100*len(sem_ev)/len(report):.1f}%)")
        antes_alta = len([r for r in report if r["before"] >= 0.9])
        depois_alta = len([r for r in report if r["after"] >= 0.9])
        print(f"  confidence >=0.9: {antes_alta} → {depois_alta}")
        print(f"\n  maiores quedas (confidence inflada pelo contador de palavras):")
        for r in sorted(report, key=lambda x: x["delta"])[:8]:
            print(f"    {r['before']:.2f}→{r['after']:.2f} ({r['delta']:+.2f}) tv_antigo={r['old_times_validated']:>3} ev_real={r['evidence_ok']:>2} | {r['agent']:14s} {r['text'][:52]}")

        if args.apply:
            with HEURISTICS_PATH.open("w") as f:
                for h in heuristics:
                    f.write(json.dumps(h, ensure_ascii=False) + "\n")
            print(f"\n  gravado em {HEURISTICS_PATH}")
        return

    p.print_help()


if __name__ == "__main__":
    main()
