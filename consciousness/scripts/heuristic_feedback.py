#!/usr/bin/env python3
"""Aplica feedback de uso a uma heurística: confirmação ou contra-evidência.

Fecha o loop que ficou aberto até 05-Set-2026. Até então:
  --heuristic-failed  → implementado (baixava confidence, subia times_failed)
  --heuristic-applied → gravado no episódio, mas NUNCA tocava a heurística

Consequência medida: em 1.034 heurísticas, times_failed era 0 em todas e
times_validated estava travado em 1 para 1.029 delas. O gate de promoção
dependia justamente de times_validated e nunca aprovava nada.

Uso:
  heuristic_feedback.py <arquivo.jsonl> <needle> success|failure <timestamp>

<needle> é o id da heurística ou um fragmento do texto (case-insensitive).
Saída em uma linha, consumida pelo record-episode.sh:
  OK:<id>:<conf_antiga>:<conf_nova>:<campo>=<valor>
  NOT_FOUND | AMBIGUOUS:<id1>,<id2> | ERROR:<motivo>
"""
import json
import sys
from pathlib import Path

# Assimetria deliberada: uma falha observada informa mais que uma confirmação.
# Confirmar é barato (a heurística foi lembrada); falhar exige que alguém note
# o erro. Por isso a punição é maior que o prêmio — e o teto por confirmação
# fica abaixo de 0.85, o corte de promoção por evidência: uso repetido sozinho
# não deve promover, senão a heurística vira rule sem ninguém ter revisado.
DELTA_SUCCESS = +0.05
DELTA_FAILURE = -0.15
TETO_SUCCESS = 0.80
PISO_FAILURE = 0.10


def main():
    if len(sys.argv) < 5:
        print("ERROR:argumentos insuficientes")
        return 0
    path, needle, outcome, ts = sys.argv[1:5]
    if outcome not in ("success", "failure"):
        print(f"ERROR:outcome invalido '{outcome}'")
        return 0

    p = Path(path)
    if not p.exists():
        print("ERROR:arquivo nao encontrado")
        return 0

    linhas = [l.rstrip("\n") for l in p.read_text().splitlines() if l.strip()]
    regs = []
    for l in linhas:
        try:
            regs.append(json.loads(l))
        except Exception:
            regs.append(None)   # preserva a linha bruta se já vier inválida

    # Ordem de resolução, da mais precisa para a mais frouxa:
    #   1. id exato
    #   2. SUFIXO do id — é o "handle" curto (#7185a957) que o router mostra no
    #      prompt; sem este passo o agente cita o handle e recebe NOT_FOUND
    #   3. substring no texto da heurística
    alvo = needle.lstrip("#").lower()
    exato = [i for i, r in enumerate(regs) if r and (r.get("id") or "").lower() == alvo]
    if not exato:
        exato = [i for i, r in enumerate(regs)
                 if r and (r.get("id") or "").lower().endswith(alvo) and len(alvo) >= 6]
    if exato:
        matches = exato
    else:
        matches = [i for i, r in enumerate(regs)
                   if r and alvo in (r.get("heuristic") or "").lower()]

    if not matches:
        print("NOT_FOUND")
        return 0
    if not exato and len(matches) > 1:
        print("AMBIGUOUS:" + ",".join(regs[i].get("id", "?") for i in matches[:5]))
        return 0

    idx = matches[0]
    r = regs[idx]
    try:
        conf_antiga = float(r.get("confidence", 0.5))
    except Exception:
        conf_antiga = 0.5

    if outcome == "success":
        conf_nova = min(round(conf_antiga + DELTA_SUCCESS, 4), TETO_SUCCESS)
        r["times_validated"] = (r.get("times_validated") or 0) + 1
        r["last_validated"] = ts
        r["validation_method"] = "declared"   # o agente declarou; vale mais que inferido
        campo = f"times_validated={r['times_validated']}"
    else:
        conf_nova = max(round(conf_antiga + DELTA_FAILURE, 4), PISO_FAILURE)
        r["times_failed"] = (r.get("times_failed") or 0) + 1
        r["last_failed"] = ts
        campo = f"times_failed={r['times_failed']}"

    r["confidence"] = conf_nova

    # Escrita atômica: temp no mesmo diretório + replace, para não corromper o
    # arquivo se outro processo estiver lendo em paralelo.
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w") as f:
        for i, l in enumerate(linhas):
            f.write((json.dumps(regs[i], ensure_ascii=False) if i == idx else l) + "\n")
    tmp.replace(p)

    print(f"OK:{r.get('id')}:{conf_antiga}:{conf_nova}:{campo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
