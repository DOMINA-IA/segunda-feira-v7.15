#!/usr/bin/env python3
"""
framework_health_check — Anti-teatro. Valida afirmações VERIFICÁVEIS do framework
contra o estado REAL da máquina.

Motivação (28-Mai-2026): a auditoria descobriu que o CLAUDE.md afirmava
'"model":"sonnet" aplicado em settings.json' — falso. R$ X.XXX em 7 dias rodaram
em Opus por causa dessa divergência entre narrativa e estado. Regra nova:
documentação não é estado; é narrativa sobre o estado. Este script audita o estado.

Zero dependências. Exit code: 0 = tudo OK/WARN, 1 = há FAIL crítico.
Uso:  python3 framework_health_check.py [--json]
Cron sugerido (semanal):  0 8 * * 1
"""

import json
import os
import re
import subprocess
import time
import sys
from pathlib import Path

HOME = Path.home()
ON_VPS = Path("/opt/segunda-feira").exists() and not Path.home() / "Library".exists()  # runtime (VPS) vs dev (Mac)
CHECKS = []  # (nível, nome, detalhe)  nível ∈ {OK, WARN, FAIL, SKIP}

# ── Instalacao nova vs operacao em regime ────────────────────────────────────
# Varios checks medem INFRA que so existe depois que a pessoa monta (VPS com
# systemd, crons agendados, daemon do dashboard). Numa instalacao recem-feita a
# ausencia disso e o estado ESPERADO, nao uma falha — reportar FAIL ali ensina
# a pessoa a ignorar o proprio verificador, que e o oposto do objetivo.
# Criterio: sem historico episodico ainda = ninguem operou este ambiente.
def _instalacao_nova():
    ep = HOME / "consciousness" / "memory" / "episodic"
    try:
        linhas = sum(sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
                     for f in ep.glob("*.jsonl"))
    except Exception:
        return True
    return linhas < 20


FRESH = _instalacao_nova()


def add(level, name, detail):
    # Numa instalacao nova, falha de INFRA nao configurada vira SKIP informativo.
    # A logica do framework (model, heuristicas, contadores, segredos) continua
    # sendo cobrada normalmente — o que degrada e so o que depende de servidor.
    if FRESH and level in ("FAIL", "WARN") and name in _CHECKS_DE_INFRA:
        level = "SKIP"
        detail = f"não configurado ainda (normal em instalação nova) — {detail}"
    CHECKS.append((level, name, detail))


_CHECKS_DE_INFRA = {
    "crons", "crons-exec", "vps-timers", "daemons",
    "daemon:autonomous-dashboard", "daemon:heartbeat",
    "skill-usage", "heuristic-feedback", "wrapper-sync",
}


# ── 1. Model default presente (a mentira da v7.10) ───────────────────────────
def check_model_default():
    settings = HOME / ".claude" / "settings.json"
    try:
        data = json.loads(settings.read_text())
    except Exception as e:
        return add("FAIL", "model-default", f"settings.json ilegível: {e}")
    model = data.get("model")
    if not model:
        add("FAIL", "model-default",
            "settings.json NÃO declara 'model' → CLI usa Opus por padrão (caro). "
            "Adicione \"model\": \"sonnet\".")
    else:
        add("OK", "model-default", f"model default = '{model}'")


# ── 2. Heurísticas: o loop write→read está fechado? ──────────────────────────
def check_heuristics_loop():
    p = HOME / "consciousness" / "memory" / "procedural" / "heuristics.jsonl"
    if not p.exists():
        return add("WARN", "heuristics-loop", "heuristics.jsonl ausente")
    total = triggered = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            h = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        if h.get("triggered_count", 0) > 0:
            triggered += 1
    if total == 0:
        return add("WARN", "heuristics-loop", "nenhuma heurística")
    pct = 100 * triggered // total
    if triggered == 0:
        add("FAIL", "heuristics-loop",
            f"0/{total} heurísticas recuperadas em runtime — write-only. "
            "Verifique heuristics_inject.py no thalamus router.")
    elif pct < 10:
        add("WARN", "heuristics-loop",
            f"{triggered}/{total} ({pct}%) recuperadas — loop ativo mas baixa cobertura")
    else:
        add("OK", "heuristics-loop", f"{triggered}/{total} ({pct}%) recuperadas em runtime")


# ── 3. Sinais acumulados não-consumidos ──────────────────────────────────────
def check_signals():
    p = HOME / "broadcast" / "signals.json"
    if not p.exists():
        return add("OK", "signals", "signals.json ausente (nada acumulado)")
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        return add("WARN", "signals", f"ilegível: {e}")
    sigs = data if isinstance(data, list) else data.get("signals", [])
    n = len(sigs)
    if n > 30:
        add("FAIL", "signals", f"{n} sinais acumulados (>30) — router de sinais provavelmente parado")
    elif n > 15:
        add("WARN", "signals", f"{n} sinais ativos — monitorar acúmulo")
    else:
        add("OK", "signals", f"{n} sinais ativos")


# ── 4. Daemons vivos ─────────────────────────────────────────────────────────
def check_daemons():
    try:
        ps = subprocess.run(["ps", "ax"], capture_output=True, text=True, timeout=10).stdout
    except Exception as e:
        return add("WARN", "daemons", f"ps falhou: {e}")
    # Heartbeat roda na VPS desde 05-Set-2026 (schedule.yaml). No Mac, vivo = ERRADO (colide
    # com o consolidate da VPS às 23:30); o check da VPS é o vps-timers.
    alvos = [("heartbeat", "heartbeat.py --daemon")] if ON_VPS else [("autonomous-dashboard", "autonomous/dashboard/serve.py")]
    for label, needle in alvos:
        if needle in ps:
            add("OK", f"daemon:{label}", "vivo")
        else:
            add("WARN", f"daemon:{label}", "não está rodando")
    if not ON_VPS and "heartbeat.py --daemon" in ps:
        add("WARN", "daemon:heartbeat", "rodando no MAC — deveria estar só na VPS (crontab antigo?)")


# ── 5. Contadores reais (drift vs documentação) ──────────────────────────────
def _count(path, pattern="*.md"):
    d = HOME / path
    return len(list(d.rglob(pattern))) if d.exists() else 0

def check_counters():
    agents_meta = _count(".claude/agents/meta")
    agents_ops = _count(".claude/agents/ops")

    # Agentes que existem SÓ na camada wrapper (sem canônica). Eram invisíveis
    # nos contadores, embora sejam 27 — incluindo @sf-master, @devops e @qa.
    wrap_dir = HOME / ".claude" / "commands" / "segunda-feira" / "agents"
    canon = HOME / ".claude" / "agents"
    agents_wrap = 0
    if wrap_dir.is_dir():
        for f in wrap_dir.glob("*.md"):
            if (canon/"meta"/f.name).exists() or (canon/"ops"/f.name).exists():
                continue
            try:
                if "DERIVADO" in f.read_text(errors="ignore")[:2000]:
                    continue
            except Exception:
                continue
            agents_wrap += 1

    # Skill é <nome>/SKILL.md — contar "*.md" recursivo dava 160 porque somava
    # _inativas, _archived e qualquer .md avulso. O número que importa é o de
    # skills ATIVAS: são elas que custam description em toda sessão.
    sk = HOME / ".claude" / "skills"
    def _skills(base):
        return len(list(base.glob("*/SKILL.md"))) if base.is_dir() else 0
    skills_ativas = _skills(sk)
    skills_inativas = _skills(sk/"_inativas")
    skills_arquiv = _skills(sk/"_archived")

    rules_always = _count(".claude/rules")
    rules_demand = _count("cortex/vault/rules")
    # Só hook REGISTRADO em settings.json roda; contar arquivos do diretório
    # inflava (README.md e 2 hooks órfãos entravam na conta de 12).
    try:
        _s = json.loads((HOME / ".claude" / "settings.json").read_text())
        hooks = sum(len(h.get("hooks", [])) for evs in _s.get("hooks", {}).values() for h in evs)
    except Exception:
        hooks = 0
    # Drift documental: o CLAUDE.md afirma contadores; se divergem do medido, é WARN
    # (antes este check devolvia OK sempre — Codex 07-Set: "não é detector de drift").
    try:
        cm = (HOME / ".claude" / "CLAUDE.md").read_text(errors="ignore")
        doc_rules = re.search(r"(\d+)\s+on-demand", cm)
        doc_skills = re.search(r"(\d+)\s+ativas", cm)
        drift = []
        if doc_rules and int(doc_rules.group(1)) != rules_demand:
            drift.append(f"rules on-demand doc={doc_rules.group(1)} real={rules_demand}")
        if doc_skills and int(doc_skills.group(1)) != skills_ativas:
            drift.append(f"skills ativas doc={doc_skills.group(1)} real={skills_ativas}")
        if drift:
            add("WARN", "counters-doc", "CLAUDE.md desatualizado: " + "; ".join(drift))
    except Exception:
        pass
    add("OK", "counters",
        f"agentes={agents_meta + agents_ops + agents_wrap} "
        f"(meta {agents_meta} + ops {agents_ops} + wrapper {agents_wrap}) | "
        f"skills ativas={skills_ativas} (inativas {skills_inativas}, arquivadas {skills_arquiv}) | "
        f"rules={rules_always} always + {rules_demand} on-demand | hooks={hooks}  "
        "← sincronize o footer do CLAUDE.md com estes números")


# ── 6. Sync canônica→wrapper (dupla camada) ──────────────────────────────────
def check_wrapper_sync():
    script = HOME / "framework" / "scripts" / "sync-agent-wrappers.sh"
    if not script.exists():
        return add("WARN", "wrapper-sync", "sync-agent-wrappers.sh ausente")
    try:
        result = subprocess.run(["bash", str(script), "--check"],
                                 capture_output=True, text=True, timeout=30)
    except Exception as e:
        return add("WARN", "wrapper-sync", f"script falhou ao rodar: {e}")
    lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    summary = lines[-1] if lines else "(sem output)"
    if result.returncode == 0:
        add("OK", "wrapper-sync", summary)
    else:
        add("WARN", "wrapper-sync",
            f"{summary} — rode sync-agent-wrappers.sh --sync <agente>")


# ── 7. Crons quebrados/desativados ───────────────────────────────────────────
def check_crons():
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return add("WARN", "crons", "crontab inacessível")
    disabled = len(re.findall(r"DESATIVADO|DISABLED|quebrad|crash", out, re.I))
    active = len([l for l in out.splitlines() if l.strip() and not l.strip().startswith("#") and "*" in l])
    if disabled > 5:
        add("WARN", "crons", f"{active} ativos, {disabled} marcados desativados/quebrados — considerar limpar para DISABLED-CRONS.md")
    else:
        add("OK", "crons", f"{active} crons ativos, {disabled} desativados documentados")


# ── 8. Bateria de roteamento (assertividade skill/agente vira número) ────────
def check_routing_battery():
    script = HOME / "framework" / "tests" / "run-routing-battery.py"
    if not script.exists():
        return add("WARN", "routing-battery", "run-routing-battery.py ausente")
    try:
        result = subprocess.run(["python3", str(script)],
                                 capture_output=True, text=True, timeout=30)
    except Exception as e:
        return add("WARN", "routing-battery", f"script falhou ao rodar: {e}")
    m = re.search(r"Score:\s*(\d+)/(\d+)", result.stdout)
    if not m:
        return add("WARN", "routing-battery", "score não encontrado no output do script")
    hits, total = int(m.group(1)), int(m.group(2))
    if hits >= total - 2:
        add("OK", "routing-battery", f"{hits}/{total} — descriptions guiam o roteamento corretamente")
    else:
        add("WARN", "routing-battery",
            f"{hits}/{total} (<total-2) — descriptions fracas causando misses, ver detalhe do script")



# ── 7b. Crons EXECUTARAM? (não só configurados) ──────────────────────────────
def _tolerancia_dias(schedule):
    """Quanto tempo sem escrever no log é aceitável, derivado do schedule.

    Generoso de propósito: o alvo é job MORTO (semanas parado), não atraso de
    horas. Alerta apertado vira ruído, e ruído esconde sinal — foi o que fez os
    1.760 health-warn de 04-Set serem ignorados.
    """
    campos = schedule.split()
    if len(campos) < 5:
        return None
    minuto, hora, dia_mes, mes, dia_sem = campos[:5]
    if minuto.startswith("*") or "/" in minuto:
        return 0.25
    if hora.startswith("*") or "/" in hora:
        return 0.5
    if dia_sem != "*":
        return 9
    if dia_mes != "*":
        return 35
    return 2


def check_crons_executaram():
    """'N crons ativos' mede INTENÇÃO. Este mede EXECUÇÃO.

    Origem (05-Set-2026): o check reportava 24 crons ativos e nenhum problema
    enquanto 10 logs estavam parados há semanas — incluindo o log DESTE script,
    26 dias sem escrita. Verde dizia que a configuração estava certa, não que
    algo tinha rodado.
    """
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return add("WARN", "crons-exec", "crontab inacessível")

    agora = time.time()
    sem_log, atrasados, ok = [], [], 0
    for l in out.splitlines():
        l = l.strip()
        if not l or l.startswith("#") or l.startswith("@") or "*" not in l:
            continue
        m = re.search(r">>\s*(\S+\.log)", l)
        tol = _tolerancia_dias(l)
        if tol is None:
            continue
        # Job de alta frequência (minuto/hora) costuma logar SÓ quando tem trabalho:
        # o dispatcher roda a cada minuto e fica horas sem escrever quando não há
        # notificação pendente. mtime não mede execução nesse caso — só mede
        # atividade. Avaliar apenas o que é diário ou mais espaçado.
        if tol < 1:
            continue
        if not m:
            # Sem redirect não significa sem log: script pode escrever internamente
            # (heuristic-lifecycle-guard.sh e transcript-retention.sh fazem isso).
            # Procurar em ~/logs/ um log com o nome do script antes de acusar.
            script = re.search(r"/([A-Za-z0-9._-]+?)(?:\.sh|\.py)\b", l)
            achou = None
            if script:
                for cand in (HOME/"logs").glob(f"{script.group(1)}*.log"):
                    achou = cand; break
            if achou is None:
                sem_log.append(script.group(1) if script else l[:26])
                continue
            log = achou
        else:
            log = Path(m.group(1).replace("$HOME", str(HOME)).replace("~", str(HOME), 1))  # crontab usa ~ e $HOME
        if not log.exists():
            # Log inexistente: se o DIRETÓRIO do log não existe, o shell falha no
            # redirect e o job nunca roda (05-Set-2026: sessions_db, user_model e
            # skill_auto_proposer gravavam em ~/.claude/logs/, apagado em julho —
            # 3 crons mortos por meses, classificados aqui como "não avaliados").
            if not log.parent.exists():
                atrasados.append((f"{log.name} (dir do log não existe)", 999, tol))
                continue
            # Diretório existe mas arquivo não: job novo (sem histórico) ou nunca
            # rodou. Só acusa se o crontab é mais velho que 2× a tolerância.
            try:
                idade_crontab = (agora - os.path.getmtime("/var/at/tabs/" + os.environ.get("USER", ""))) / 86400
            except OSError:
                idade_crontab = 0
            if idade_crontab > 2 * tol:
                atrasados.append((f"{log.name} (nunca escreveu)", int(idade_crontab), tol))
            else:
                sem_log.append(log.name)
            continue
        # Log VAZIO não prova nada: o ">>" cria o arquivo na primeira execução e,
        # se o script é silencioso (exit 0 sem output), o mtime congela naquela
        # data para sempre — mesmo rodando todo dia. log-rotate.log tem 0 bytes
        # desde 12/08 e roda diariamente. mtime mede ESCRITA, não execução.
        if log.stat().st_size == 0:
            sem_log.append(f"{log.name} (silencioso)")
            continue
        dias = (agora - log.stat().st_mtime) / 86400
        if dias > tol:
            atrasados.append((log.name, int(dias), tol))
        else:
            ok += 1

    total = ok + len(atrasados) + len(sem_log)
    if total == 0:
        return add("OK", "crons-exec", "nenhum cron com log para verificar")

    piores = sorted(atrasados, key=lambda x: -x[1])[:3]
    detalhe = " · ".join(f"{n} {d}d/tol {t}d" for n, d, t in piores)
    # A severidade sai SÓ dos atrasados — job com log parado além da tolerância é
    # evidência de que parou. "Sem log" é ambíguo (script pode logar internamente,
    # ou o job ser novo demais para ter histórico) e entra como nota informativa.
    # Misturar os dois faria o check gritar por classificação ruim, não por falha —
    # e check que grita à toa é ignorado, como os 1.760 health-warn de 04-Set.
    nota = f" | {len(sem_log)} sem log rastreável (não avaliados)" if sem_log else ""
    verificaveis = ok + len(atrasados)
    if atrasados:
        sev = "FAIL" if len(atrasados) > verificaveis // 2 else "WARN"
        add(sev, "crons-exec",
            f"{ok}/{verificaveis} rodaram no prazo | {len(atrasados)} parado(s)"
            + (f" — piores: {detalhe}" if piores else "") + nota)
    else:
        add("OK", "crons-exec", f"{ok}/{verificaveis} crons rodaram no prazo{nota}")


# ── 9. Segredos em texto plano (rule credentials-handling) ───────────────────
def check_secret_scan():
    script = HOME / "framework" / "scripts" / "secret-scan.py"
    if not script.exists():
        return add("WARN", "secret-scan", "secret-scan.py ausente")
    try:
        r = subprocess.run(["python3", str(script), "--json"], capture_output=True, text=True, timeout=120)
        if not r.stdout.strip():
            return add("WARN", "secret-scan", f"scanner sem saída (rc={r.returncode}) — não medido")
        hits = json.loads(r.stdout)
    except Exception as e:
        return add("WARN", "secret-scan", f"falhou: {e}")
    if hits:
        areas = sorted({h["area"] for h in hits})
        add("FAIL", "secret-scan", f"{len(hits)} credencial(is) em texto plano em {', '.join(areas)} — rode secret-scan.py")
    else:
        add("OK", "secret-scan", "0 credenciais em texto plano nas áreas proibidas")


# ── 10. Permissões de .env (600) ─────────────────────────────────────────────
def check_env_perms():
    abertos = []
    for base in (HOME / "projetos", HOME / "_secrets"):
        if not base.exists():
            continue
        for p in list(base.rglob(".env*")) + list(base.rglob("*.env")):
            if not p.is_file() or any(s in p.parts for s in ("node_modules", ".git")) or p.name.endswith(".example"):
                continue
            try:
                if p.stat().st_mode & 0o077:  # qualquer bit de grupo/outros (Codex 07-Set: 622 passava)
                    abertos.append(str(p.relative_to(HOME)))
            except PermissionError:
                continue                      # de outro usuário: não é nosso para medir
    if abertos:
        add("WARN", "env-perms", f"{len(abertos)} .env legíveis por outros: {', '.join(abertos[:3])}{'…' if len(abertos) > 3 else ''} — chmod 600")
    else:
        add("OK", "env-perms", "todos os .env*/*.env sem bits de grupo/outros")


# ── 11. Skills do framework são USADAS? (tráfego real, não bateria lexical) ──
def check_skill_usage(days=30):
    """A bateria mede se a description casa com o pedido; isto mede se alguém
    (modelo ou CEO) invocou a skill de verdade. 05-Set-2026: 443 transcripts,
    27 chamadas do Skill tool, 0 do framework."""
    proj = HOME / ".claude" / "projects"
    if ON_VPS:
        return add("OK", "skill-usage", "medido no Mac (transcripts não sincronizam)")
    if not proj.exists():
        return add("WARN", "skill-usage", "sem transcripts")
    fw = {p.parent.name for p in (HOME / ".claude" / "skills").glob("*/SKILL.md")} - {"impeccable", "frontend-design", "web-design-guidelines"}  # vendidas pela Anthropic, não do framework
    cut = time.time() - days * 86400
    total = fw_calls = 0
    for f in proj.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < cut:
                continue
            for line in f.open(errors="ignore"):
                if '"Skill"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                try:   # janela pelo timestamp do EVENTO (mtime do arquivo inflava 21→29, Codex 07-Set)
                    ets = time.mktime(time.strptime(str(d.get("timestamp", ""))[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
                    if ets < cut:
                        continue
                except (ValueError, TypeError):
                    continue
                c = d.get("message", {}).get("content")
                if not isinstance(c, list):
                    continue
                for x in c:
                    if isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") == "Skill":
                        total += 1
                        sk = str((x.get("input") or {}).get("skill", "")).split(":")[-1]
                        if sk in fw:
                            fw_calls += 1
        except OSError:
            continue
    if fw_calls == 0:
        add("WARN", "skill-usage", f"0 invocações de skill do framework em {days}d ({total} do Skill tool no total) — as 32 descriptions custam contexto sem retorno")
    else:
        add("OK", "skill-usage", f"{fw_calls} invocações de skill do framework em {days}d ({total} total)")


# ── 12. Loop de heurística fecha? (episódios que citam #handle) ──────────────
def check_heuristic_feedback(days=7):
    ep = HOME / "consciousness" / "memory" / "episodic"
    if not ep.exists():
        return add("WARN", "heuristic-feedback", "sem episódios")
    cut = time.time() - days * 86400
    n = com = 0
    for f in ep.glob("*.jsonl"):
        for line in f.open(errors="ignore"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = d.get("timestamp", "")
            try:
                t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
            except (ValueError, TypeError):
                continue
            if t < cut:
                continue
            n += 1
            les = d.get("lessons", {}) or {}
            if les.get("heuristic_applied") or les.get("heuristic_failed") or d.get("heuristics_applied"):
                com += 1
    if n == 0:
        add("WARN", "heuristic-feedback", f"0 episódios em {days}d")
    elif com == 0:
        add("WARN", "heuristic-feedback", f"0/{n} episódios em {days}d citam #handle — pool cresce sem lastro (rule operating-protocol)")
    else:
        add("OK", "heuristic-feedback", f"{com}/{n} episódios em {days}d citam #handle")


# ── 13. Timers na VPS (runtime 24/7 — decisão CEO 05-Set-2026) ───────────────
def check_vps_timers():
    cmd = "systemctl list-units --all --plain --no-legend 'sf-*.service' 2>/dev/null | awk '{print $1, $3, $4}'"
    try:
        if ON_VPS:
            r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=20)
        else:
            r = subprocess.run(["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", "CLIENTE_EXEMPLO", cmd],
                               capture_output=True, text=True, timeout=20)
    except Exception as e:
        return add("WARN", "vps-timers", f"ssh falhou: {e}")
    units = [l.split() for l in r.stdout.splitlines() if l.strip() and not l.startswith("sf-alert@")]
    if not units:
        return add("WARN", "vps-timers", "nenhuma unit sf-* na VPS (runtime ainda não migrado)")
    # jobs esperados = schedule.yaml; unit ausente também é falha (não só "failed")
    esperados = set()
    try:
        for m in re.finditer(r"^\s*-\s*id:\s*([a-z0-9-]+)", (HOME / "framework" / "runtime" / "schedule.yaml").read_text(), re.M):
            esperados.add(f"sf-{m.group(1)}.service")
    except Exception:
        pass
    presentes = {u[0] for u in units}
    ausentes = sorted(esperados - presentes)
    # o próprio framework-health sai 1 quando há FAIL (é o que dispara o alerta); contá-lo aqui
    # seria o instrumento se acusando em dobro
    failed = [u[0] for u in units if len(u) > 2 and u[2] == "failed" and u[0] != "sf-framework-health.service"]
    if failed or ausentes:
        add("FAIL", "vps-timers", f"{len(failed)} failed: {', '.join(failed) or '-'} | {len(ausentes)} do schedule sem unit: {', '.join(ausentes) or '-'}")
    else:
        add("OK", "vps-timers", f"{len(units)} units (todos os {len(esperados)} jobs do schedule presentes, 0 failed)")


def main():
    for fn in (check_model_default, check_heuristics_loop, check_signals,
               check_daemons, check_counters, check_wrapper_sync, check_crons, check_crons_executaram,
               check_routing_battery, check_secret_scan, check_env_perms, check_skill_usage,
               check_heuristic_feedback, check_vps_timers):
        try:
            fn()
        except Exception as e:
            add("WARN", fn.__name__, f"check falhou: {e}")

    as_json = "--json" in sys.argv
    if as_json:
        print(json.dumps([{"level": l, "check": n, "detail": d} for l, n, d in CHECKS],
                         ensure_ascii=False, indent=2))
    else:
        icon = {"OK": "✅", "WARN": "⚠️ ", "FAIL": "❌", "SKIP": "○"}
        print("═══ FRAMEWORK HEALTH CHECK ═══")
        if FRESH:
            print("   (instalação nova: checks de infra ainda não configurada aparecem como ○)")
        for level, name, detail in CHECKS:
            print(f"{icon[level]} {name}: {detail}")
        fails = sum(1 for l, _, _ in CHECKS if l == "FAIL")
        warns = sum(1 for l, _, _ in CHECKS if l == "WARN")
        skips = sum(1 for l, _, _ in CHECKS if l == "SKIP")
        resumo = f"\n{len(CHECKS)} checks | {fails} FAIL | {warns} WARN"
        if skips:
            resumo += f" | {skips} não aplicável"
        print(resumo)
        if FRESH and not fails:
            print("\nInstalação saudável. Os ○ viram ✅ conforme você monta a infra\n"
                  "(agendamentos, dashboard) e acumula histórico de uso.")

    return 1 if any(l == "FAIL" for l, _, _ in CHECKS) else 0


if __name__ == "__main__":
    sys.exit(main())
