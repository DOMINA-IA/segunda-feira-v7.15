#!/usr/bin/env python3
"""pipeline.py — Ciclo de Evolução: observar → diagnosticar → propor → testar → publicar → adotar.

Uso:
  pipeline.py ciclo [--data AAAA-MM-DD] [--max N] [--sem-replay] [--dias 7]
  pipeline.py status
  pipeline.py aprovar <data> <id>          # Mac: aplica a proposta no arquivo-alvo e commita
  pipeline.py rejeitar <data> <id> [motivo]
  pipeline.py aplicar-aprovados            # Mac (chamado pelo sf-sync): adota o que já pode

Papéis (evolucao.yaml): ADVERSÁRIO (codex; fallback claude) diagnostica e julga; CONSTRUTOR
(claude) propõe. Quem escreve nunca julga. Tudo que sai fica em
framework/observations/evolucao/<data>/ (sincronizado VPS → Mac). Adoção só no Mac, em git.
Falha de qualquer chamada a modelo = proposta descartada, ciclo continua; nunca exceção solta.
"""
import argparse
import difflib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
AQUI = Path(__file__).resolve().parent
CFG = AQUI / "evolucao.yaml"
BASE = HOME / "framework" / "observations" / "evolucao"
ESTADO = BASE / "estado.json"
ON_VPS = Path("/opt/segunda-feira").exists() and not (HOME / "Library").exists()
# claude -p disparado de dentro de uma sessão Claude Code herda CLAUDECODE=1 e recusa; limpar
ENV_LIMPO = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
ENV_LIMPO["SF_AUTOMATED"] = "1"


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def cfg():
    import yaml
    return yaml.safe_load(CFG.read_text())


def estado():
    try:
        return json.loads(ESTADO.read_text())
    except Exception:
        return {"ciclos_concluidos": 0, "ciclos_aprovados_humano": 0, "adotadas": [], "rejeitadas": []}


def salvar_estado(e):
    BASE.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1))


# ── modelos ──────────────────────────────────────────────────────────────────
def codex_ok():
    if not shutil.which("codex"):
        return False
    try:
        r = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, timeout=20)
        return "Logged in" in (r.stdout + r.stderr)
    except Exception:
        return False


def chamar(papel, prompt, c, timeout=900):
    """Retorna texto da resposta ou '' em falha. Registra qual modelo respondeu."""
    p = c["papeis"][papel]
    usa_codex = p.get("preferido") == "codex" and codex_ok()
    def _claude(modelo_nome):
        r = subprocess.run(["claude", "-p", "--model", modelo_nome, "--output-format", "text", "--max-turns", "3"],
                           input=prompt, capture_output=True, text=True, timeout=timeout, env=ENV_LIMPO)
        return r, f"claude:{modelo_nome}"
    try:
        if usa_codex:
            # --skip-git-repo-check: HOME não é repo; stdin fechado: codex exec lê stdin se houver
            r = subprocess.run(["codex", "exec", "-m", p["modelo"], "--sandbox", "read-only", "--skip-git-repo-check", "-C", str(HOME), prompt],
                               stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
            modelo = f"codex:{p['modelo']}"
            if r.returncode != 0 or not extrair_json(r.stdout):
                log(f"  {papel} ({modelo}) falhou (rc={r.returncode}, cota/erro: {(r.stderr or r.stdout)[-160:].strip()!r}) → fallback claude")
                r, modelo = _claude(p.get("fallback_modelo", "opus"))
        else:
            r, modelo = _claude(p["modelo"] if p.get("preferido") == "claude" else p.get("fallback_modelo", "sonnet"))
        out = r.stdout
        if r.returncode != 0 and not out.strip():
            log(f"  {papel} ({modelo}) rc={r.returncode}: {r.stderr[:200]}")
            return "", modelo
        return out, modelo
    except Exception as e:
        log(f"  {papel} falhou: {e}")
        return "", "erro"


def extrair_json(txt):
    """Último bloco ```json``` ou o maior objeto {…} balanceado."""
    blocos = re.findall(r"```json\s*(\{.*?\})\s*```", txt, re.S)
    cands = blocos[::-1] if blocos else []
    if not cands:
        # tenta objeto balanceado a partir da última '{'
        i = txt.rfind("{\n"); i = i if i >= 0 else txt.find("{")
        while i >= 0:
            prof = 0
            for j, ch in enumerate(txt[i:], start=i):
                if ch == "{": prof += 1
                elif ch == "}":
                    prof -= 1
                    if prof == 0:
                        cands.append(txt[i:j + 1]); break
            i = txt.rfind("{", 0, i)
            if len(cands) >= 3: break
    for cnd in cands:
        try:
            return json.loads(cnd)
        except Exception:
            continue
    return None


# ── freios ───────────────────────────────────────────────────────────────────
def alvo_permitido(rel, c):
    rel = rel.lstrip("/").replace(str(HOME) + "/", "")
    f = c["freios"]
    if any(rel.startswith(p) or p.rstrip("/") in rel for p in f["caminhos_proibidos"]):
        return False
    return any(rel.startswith(p) for p in f["caminhos_permitidos"]) and (HOME / rel).is_file()


def linhas_alteradas(antigo, novo):
    d = list(difflib.unified_diff(antigo.splitlines(), novo.splitlines(), lineterm="", n=0))
    return sum(1 for l in d if (l.startswith("+") or l.startswith("-")) and not l.startswith(("+++", "---")))


def frontmatter_ok(txt):
    if not txt.startswith("---"):
        return True
    try:
        import yaml
        fm = txt.split("---", 2)[1]
        yaml.safe_load(fm)
        return True
    except Exception:
        return False


# ── testes ───────────────────────────────────────────────────────────────────
def bateria():
    try:
        r = subprocess.run(["python3", str(HOME / "framework/tests/run-routing-battery.py")], capture_output=True, text=True, timeout=120)
        m = re.search(r"Score:\s*(\d+)/(\d+)", r.stdout)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    except Exception:
        return (0, 0)


def bateria_com(alvo, novo):
    """Roda a bateria com o arquivo trocado por segundos e restaura SEMPRE."""
    p = HOME / alvo
    bak = p.read_text()
    try:
        p.write_text(novo)
        return bateria()
    finally:
        p.write_text(bak)


def executar_replay(system, prompt, c):
    p = c["papeis"]["replay_executor"]
    try:
        # --tools "": replay é só texto; com ferramentas o agente tenta executar e estoura os turnos
        # (teste4: 5 empates por "Reached max turns")
        r = subprocess.run(["claude", "-p", "--model", p["modelo"], "--output-format", "text", "--max-turns", "2",
                            "--tools", "", "--system-prompt", system + "\n\nResponda diretamente em texto; não há ferramentas disponíveis nesta execução.",
                            prompt], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300, env=ENV_LIMPO)
        out = r.stdout.strip()
        return out[:6000] if out else f"(sem resposta: {r.stderr.strip()[:200]})"
    except Exception as e:
        return f"(falha ao executar replay: {e})"


def julgar(prompt, criterio, resp_antigo, resp_novo, c):
    tpl = (AQUI / "prompts/juiz.md").read_text()
    inverte = random.random() < 0.5                 # juiz cego: A/B embaralhados
    A, B = (resp_novo, resp_antigo) if inverte else (resp_antigo, resp_novo)
    txt, modelo = chamar("adversario", tpl.replace("{{CRITERIO}}", criterio).replace("{{PROMPT}}", prompt).replace("{{A}}", A).replace("{{B}}", B), c, timeout=300)
    j = extrair_json(txt) or {}
    v = str(j.get("vencedor", "empate")).upper()
    if v == "EMPATE" or v not in ("A", "B"):
        return "empate", j.get("motivo", ""), modelo
    novo_venceu = (v == "A") if inverte else (v == "B")
    return ("novo" if novo_venceu else "antigo"), j.get("motivo", ""), modelo



def replay_e_julgar(hid, d, atual, novo, replays, c):
    placar = {"novo": 0, "antigo": 0, "empate": 0}; detalhes = []
    for rp in replays:
        ra = executar_replay(atual, rp["prompt"], c); rn = executar_replay(novo, rp["prompt"], c)
        venc, motivo, mj = julgar(rp["prompt"], rp.get("criterio", ""), ra, rn, c)
        placar[venc] += 1
        detalhes.append({"prompt": rp["prompt"], "criterio": rp.get("criterio", ""), "vencedor": venc, "motivo": motivo, "juiz": mj,
                         "resposta_antigo": ra[:1500], "resposta_novo": rn[:1500]})
        log(f"  {hid} replay: {venc} — {motivo[:80]}")
    (d / "replays.json").write_text(json.dumps(detalhes, ensure_ascii=False, indent=1))
    return placar


def rejulgar(args):
    """Refaz replay + juiz de uma proposta já gerada (ex.: após corrigir o executor)."""
    c = cfg(); f = c["freios"]; d = BASE / args.data / args.id
    prop = json.loads((d / "proposta.json").read_text()); alvo = prop["alvo"]
    atual = (d / "antes.md").read_text() if (d / "antes.md").exists() else (HOME / alvo).read_text()
    novo = (d / "novo.md").read_text()
    placar = replay_e_julgar(args.id, d, atual, novo, [r for r in prop.get("replays", []) if r.get("prompt")][:f["min_replays_por_proposta"]], c)
    v = json.loads((BASE / args.data / "veredito.json").read_text())
    for r in v["propostas"]:
        if r["id"] == args.id:
            r["placar"] = placar
            r["status"] = "aprovada_para_adocao" if (placar["novo"] >= f["min_vitorias_para_adotar"] and placar["antigo"] <= f["max_derrotas_para_adotar"]) else "rejeitada_no_replay"
            r["rejulgado_em"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            print(f"{args.id}: {r['status']} · placar {placar}")
    (BASE / args.data / "veredito.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    return 0


# ── ciclo ────────────────────────────────────────────────────────────────────
def ciclo(args):
    c = cfg(); f = c["freios"]
    data = args.data or time.strftime("%Y-%m-%d")
    out = BASE / data; out.mkdir(parents=True, exist_ok=True)
    log(f"ciclo {data} → {out}  (host {'VPS' if ON_VPS else 'Mac'})")

    # 1. observar
    obs_p = out / "observacao.md"
    subprocess.run(["python3", str(AQUI / "observe.py"), "--dias", str(args.dias), "--saida", str(obs_p)], timeout=600)
    obs = obs_p.read_text() if obs_p.exists() else ""
    log(f"observação: {len(obs)} chars")

    # 2. diagnosticar (adversário)
    maxn = args.max or f["max_propostas_por_ciclo"]
    tpl = (AQUI / "prompts/diagnostico.md").read_text()
    txt, modelo_d = chamar("adversario", tpl.replace("{{MAX}}", str(maxn)).replace("{{DATA}}", data).replace("{{OBSERVACAO}}", obs), c)
    (out / "diagnostico.raw.txt").write_text(txt)
    diag = extrair_json(txt) or {"hipoteses": [], "qualidade_da_evidencia": "vazia"}
    hip = [h for h in diag.get("hipoteses", []) if isinstance(h, dict) and h.get("alvo")]
    validas = [h for h in hip if alvo_permitido(h["alvo"], c)]
    log(f"diagnóstico ({modelo_d}): evidência {diag.get('qualidade_da_evidencia')} · {len(hip)} hipóteses · {len(validas)} em alvo permitido")
    diag["modelo"] = modelo_d; diag["hipoteses_validas"] = [h["id"] for h in validas]
    (out / "diagnostico.json").write_text(json.dumps(diag, ensure_ascii=False, indent=1))

    # 3-4. propor e testar
    resultados = []
    base_score = bateria()
    for h in validas[:maxn]:
        hid = h.get("id", f"H{len(resultados)+1}"); d = out / hid; d.mkdir(exist_ok=True)
        alvo = h["alvo"].lstrip("/").replace(str(HOME) + "/", "")
        atual = (HOME / alvo).read_text()
        tpl = (AQUI / "prompts/proposta.md").read_text()
        ptxt, modelo_p = chamar("construtor", tpl.replace("{{MAX_LINHAS}}", str(f["max_linhas_alteradas"])).replace("{{ALVO}}", alvo)
                                .replace("{{CONTEUDO}}", atual).replace("{{HIPOTESE}}", json.dumps(h, ensure_ascii=False, indent=1)).replace("{{ID}}", hid), c)
        (d / "proposta.raw.txt").write_text(ptxt)
        prop = extrair_json(ptxt)
        res = {"id": hid, "alvo": alvo, "hipotese": h, "modelo_construtor": modelo_p, "status": "descartada", "motivos": []}
        if not prop or not prop.get("novo_conteudo"):
            res["motivos"].append("construtor não devolveu proposta válida"); resultados.append(res); continue
        novo = prop["novo_conteudo"]
        if not novo.endswith("\n"): novo += "\n"
        n_lin = linhas_alteradas(atual, novo)
        replays = [r for r in prop.get("replays", []) if isinstance(r, dict) and r.get("prompt")]
        res.update({"resumo": prop.get("resumo", ""), "metrica": prop.get("metrica", h.get("metrica")), "risco": prop.get("risco", h.get("risco", "medio")), "linhas_alteradas": n_lin, "n_replays": len(replays)})
        if n_lin == 0: res["motivos"].append("nenhuma linha alterada")
        if n_lin > f["max_linhas_alteradas"]: res["motivos"].append(f"{n_lin} linhas > limite {f['max_linhas_alteradas']}")
        if not frontmatter_ok(novo): res["motivos"].append("frontmatter YAML inválido")
        if len(replays) < f["min_replays_por_proposta"]: res["motivos"].append(f"{len(replays)} replays < mínimo {f['min_replays_por_proposta']}")
        if res["motivos"]:
            resultados.append(res); continue
        (d / "novo.md").write_text(novo)
        (d / f"{hid}.patch").write_text("".join(difflib.unified_diff(atual.splitlines(True), novo.splitlines(True), fromfile=f"a/{alvo}", tofile=f"b/{alvo}")))
        (d / "proposta.json").write_text(json.dumps(prop, ensure_ascii=False, indent=1))
        # bateria com o arquivo novo
        sc = bateria_com(alvo, novo); res["bateria"] = {"antes": base_score, "depois": sc}
        if sc[0] < base_score[0]:
            res["motivos"].append(f"bateria piorou {base_score[0]}→{sc[0]}"); resultados.append(res); continue
        # replay com juiz cego
        placar = {"novo": 0, "antigo": 0, "empate": 0}
        if not args.sem_replay:
            placar = replay_e_julgar(hid, d, atual, novo, replays[:f["min_replays_por_proposta"]], c)
        res["placar"] = placar
        aprovada = (args.sem_replay or (placar["novo"] >= f["min_vitorias_para_adotar"] and placar["antigo"] <= f["max_derrotas_para_adotar"]))
        res["status"] = "aprovada_para_adocao" if aprovada else "rejeitada_no_replay"
        resultados.append(res)

    # 5. publicar
    e = estado(); e["ciclos_concluidos"] += 1; e["ultimo_ciclo_ts"] = int(time.time()); salvar_estado(e)
    (out / "veredito.json").write_text(json.dumps({"data": data, "host": "VPS" if ON_VPS else "Mac", "modelo_diagnostico": modelo_d, "bateria_base": base_score, "propostas": resultados}, ensure_ascii=False, indent=1))
    aprov = [r for r in resultados if r["status"] == "aprovada_para_adocao"]
    modo = "adoção automática (risco baixo)" if e["ciclos_aprovados_humano"] >= f["ciclos_com_aprovacao_humana"] else f"aguarda sua aprovação ({e['ciclos_aprovados_humano']}/{f['ciclos_com_aprovacao_humana']} ciclos humanos)"
    L = [f"Ciclo de Evolução {data} · diagnóstico por {modelo_d} · evidência {diag.get('qualidade_da_evidencia')}",
         f"{len(hip)} hipóteses, {len(validas)} válidas, {len(aprov)} aprovadas no replay · {modo}"]
    for r in resultados:
        pl = r.get("placar", {}); L.append(f"• {r['id']} {r['alvo']} → {r['status']} · novo {pl.get('novo','-')}/antigo {pl.get('antigo','-')}/empate {pl.get('empate','-')} · {r.get('resumo','')[:90]}" + (f" · {'; '.join(r['motivos'])}" if r["motivos"] else ""))
    if aprov:
        L.append(f"Para adotar (Mac): python3 ~/framework/runtime/evolucao/pipeline.py aprovar {data} <id>")
    digest = "\n".join(L); (out / "digest.md").write_text(digest + "\n"); print(digest)
    try:
        subprocess.run(["bash", "-c", f'. "$HOME/autonomous/lib/common.sh"; notify info "Ciclo de Evolução {data}" "$(cat "{out}/digest.md")"'], timeout=30)
    except Exception:
        pass
    return 0


# ── adoção (Mac) ─────────────────────────────────────────────────────────────
def _repo_de(alvo):
    if alvo.startswith(".claude/"): return HOME / ".claude"
    if alvo.startswith("cortex/"): return HOME / "cortex"
    return None


def aplicar(data, hid, motivo="aprovada pelo CEO"):
    d = BASE / data / hid
    prop = json.loads((d / "proposta.json").read_text()); alvo = prop["alvo"]; novo = (d / "novo.md").read_text()
    p = HOME / alvo
    bak = d / "antes.md"; bak.write_text(p.read_text())
    p.write_text(novo)
    repo = _repo_de(alvo)
    if repo and (repo / ".git").exists():
        subprocess.run(["git", "-C", str(repo), "add", str(p)], capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", f"evolucao({data}/{hid}): {prop.get('resumo','')[:70]}\n\n{motivo}. Reverter: git revert; original em {bak}"], capture_output=True)
    (d / "adotado.json").write_text(json.dumps({"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "motivo": motivo, "reverter": f"cp {bak} {p}"}, ensure_ascii=False))
    # resincroniza a wrapper derivada, se houver
    subprocess.run(["bash", str(HOME / "framework/scripts/sync-agent-wrappers.sh"), "--sync", Path(alvo).stem], capture_output=True)
    log(f"adotada {data}/{hid} em {alvo} ({motivo})")


def aprovar(args):
    e = estado(); aplicar(args.data, args.id); e["adotadas"].append(f"{args.data}/{args.id}"); e["ciclos_aprovados_humano"] += 1; salvar_estado(e)
    subprocess.run(["bash", str(HOME / "framework/runtime/sync/sf-sync.sh"), "push"], capture_output=True)
    print("adotada e enviada à VPS")


def rejeitar(args):
    e = estado(); d = BASE / args.data / args.id
    (d / "rejeitado.json").write_text(json.dumps({"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "motivo": args.motivo or ""}, ensure_ascii=False))
    e["rejeitadas"].append(f"{args.data}/{args.id}"); salvar_estado(e); print("rejeitada (o adversário verá isso na próxima observação)")


def aplicar_aprovados(args):
    """Mac, pelo sf-sync: adota sozinho o que já pode (após N ciclos humanos, só risco baixo)."""
    if ON_VPS: return 0
    c = cfg(); e = estado()
    if e["ciclos_aprovados_humano"] < c["freios"]["ciclos_com_aprovacao_humana"]:
        return 0
    n = 0
    for v in sorted(BASE.glob("*/veredito.json")):
        data = v.parent.name
        for r in json.loads(v.read_text()).get("propostas", []):
            d = v.parent / r["id"]
            if r["status"] == "aprovada_para_adocao" and r.get("risco") == "baixo" and not (d / "adotado.json").exists() and not (d / "rejeitado.json").exists():
                aplicar(data, r["id"], "adoção automática: 4+ ciclos aprovados, risco baixo, replay favorável"); e["adotadas"].append(f"{data}/{r['id']}"); n += 1
    salvar_estado(e)
    if n: print(f"{n} proposta(s) adotada(s) automaticamente")
    return 0


def status(args):
    e = estado(); print(json.dumps(e, ensure_ascii=False, indent=1))
    for v in sorted(BASE.glob("*/veredito.json"))[-3:]:
        j = json.loads(v.read_text()); print(f"\n{j['data']} ({j['host']}, {j['modelo_diagnostico']}):")
        for r in j["propostas"]: print(f"  {r['id']} {r['alvo']} → {r['status']} {r.get('placar','')}")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("ciclo"); s.add_argument("--data"); s.add_argument("--max", type=int); s.add_argument("--dias", type=int, default=7); s.add_argument("--sem-replay", action="store_true")
    sub.add_parser("status")
    s = sub.add_parser("aprovar"); s.add_argument("data"); s.add_argument("id")
    s = sub.add_parser("rejeitar"); s.add_argument("data"); s.add_argument("id"); s.add_argument("motivo", nargs="?")
    sub.add_parser("aplicar-aprovados")
    s = sub.add_parser("rejulgar"); s.add_argument("data"); s.add_argument("id")
    a = ap.parse_args()
    return {"ciclo": ciclo, "status": status, "aprovar": aprovar, "rejeitar": rejeitar, "aplicar-aprovados": aplicar_aprovados, "rejulgar": rejulgar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
