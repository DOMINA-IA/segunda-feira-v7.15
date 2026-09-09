#!/usr/bin/env python3
"""Redige credenciais em texto plano nos transcripts do Claude Code.

Origem: auditoria de segurança de 05-Set-2026 — 93 ocorrências de credencial em
14 de 465 transcripts. Permissões já eram 700/600, então o risco não é acesso
local de terceiro; é o segredo existir em disco e viajar em backup ou sync.

Preserva o histórico (opção A da auditoria) em vez de apagar sessões: substitui
apenas o VALOR, mantendo o rótulo e a estrutura da linha.

Salvaguardas:
  - sessões ativas são puladas (append concorrente perderia linhas)
  - toda linha alterada é revalidada como JSON; se quebrar, fica a original
  - backup completo antes, em ~/logs/transcripts-bak-<data>/ com chmod 600

Uso:
  python3 redact-transcripts.py --dry-run     # mostra o que faria
  python3 redact-transcripts.py --apply       # executa com backup
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
RAIZ = HOME / ".claude" / "projects"
HOJE = datetime.now().strftime("%Y%m%d")
BK = HOME / "logs" / f"transcripts-bak-{HOJE}"
MARCA = f"[REDACTED-{datetime.now().strftime('%Y-%m-%d')}]"
MIN_INATIVO = 30 * 60   # segundos sem escrita para considerar a sessão encerrada

PADROES = [
    re.compile(r'(?i)\b(senha|password|passwd|pwd|pass)\s*[:=]\s*\\?[\'"`]?([^\s\'"`,;\\\n]{8,})'),
    re.compile(r'(?i)\b(token|api[_-]?key|secret|bearer)\s*[:=]\s*\\?[\'"`]?([A-Za-z0-9_\-\.]{16,})'),
    # Tokens SOLTOS (auditoria 05-Set-2026: 24 tokens Meta sobreviveram à 1ª redação
    # porque só o formato "rótulo=valor" era coberto). Grupo 1 = prefixo que fica,
    # grupo 2 = valor que vira MARCA.
    re.compile(r'(\bEAA)([A-Za-z0-9]{40,})'),                      # Meta access token
    re.compile(r'(\bsk-(?:ant-|proj-)?)([A-Za-z0-9_\-]{20,})'),      # OpenAI / Anthropic
    re.compile(r'(\bgh[pousr]_)([A-Za-z0-9]{30,})'),                 # GitHub
    re.compile(r'(\bxox[baprs]-)([A-Za-z0-9\-]{10,})'),              # Slack
    re.compile(r'(\b\d{8,10}:AA)([A-Za-z0-9_\-]{30,})'),            # Telegram bot
    re.compile(r'([a-z][a-z0-9+]*://[A-Za-z0-9._%\-]+:)([^@\s/\'"`\\]{4,})(?=@)'),  # user:pass@host
    re.compile(r'(sshpass\s+-p\s*[\'"]?)([^\s\'"]{4,})'),                                  # sshpass -p SENHA
    re.compile(r'(-----BEGIN [A-Z ]*PRIVATE KEY-----)([\s\S]*?)(?=-----END)'),                 # corpo de chave privada
]
# Placeholder e referência a variável de ambiente não são segredo
FALSO = re.compile(
    r'(?i)(SUA_|YOUR_|<[a-z_]+>|xxx+|\*\*\*|REMOVID|placeholder|exemplo|'
    r'\$\{|\$[A-Z_]+\b|getenv|process\.env|os\.environ)'
)


def redige_linha(linha):
    """Retorna (nova_linha, n_substituicoes). Troca só o valor, mantém o rótulo."""
    # FALSO é avaliado na VIZINHANÇA do match, não na linha inteira: no transcript
    # cada linha é uma mensagem completa, e um "$VAR" ou "exemplo" em qualquer
    # ponto dela bloqueava a redação de um token real 2 KB adiante (05-Set-2026:
    # 4 arquivos "redigidos" continuaram com 17 tokens Meta).
    nova, n = linha, 0
    for p in PADROES:
        def _sub(m):
            nonlocal n
            if FALSO.search(m.string[max(0, m.start() - 40):m.end()]):
                return m.group(0)
            n += 1
            return m.group(0).replace(m.group(2), MARCA)
        nova = p.sub(_sub, nova)
    return nova, n


def sessao_ativa(f, agora):
    return (agora - f.stat().st_mtime) < MIN_INATIVO


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--keep-backup", action="store_true", help="mantém a cópia pré-redação mesmo quando tudo validou")
    args = ap.parse_args()

    if not RAIZ.is_dir():
        print(f"ERRO: {RAIZ} não existe"); return 1

    import time
    agora = time.time()
    alvos, pulados = [], []
    # history.jsonl (histórico de prompts) e file-history ficavam fora — 07-Set: 46 tokens Meta
    # e 4 de Telegram lá. Entram no mesmo passe.
    extras = [HOME / ".claude" / "history.jsonl"]
    for base in (HOME / ".claude" / "_archive",):
        extras += [p for p in base.rglob("*") if p.is_file()] if base.exists() else []
    extras += [p for p in (HOME / ".claude" / "file-history").rglob("*") if p.is_file()] if (HOME / ".claude" / "file-history").exists() else []
    for f in list(RAIZ.rglob("*")) + extras:
        if not f.is_file() or f.suffix not in {".jsonl", ".txt", ".md", ".py", ".js", ".sh", ".json", ""}:
            continue
        try:
            txt = f.read_text(errors="ignore")
        except Exception:
            continue
        n = sum(redige_linha(l)[1] for l in txt.splitlines())
        if not n:
            continue
        if sessao_ativa(f, agora):
            pulados.append((f, n)); continue
        alvos.append((f, n))

    for f, n in pulados:
        print(f"  ⏭  PULADO (sessão ativa): {f.name[:48]} — {n} ocorrência(s)")
    if not alvos:
        print("\nNenhum arquivo a redigir."); return 0

    print(f"\n{'ARQUIVO':52s} {'OCORR':>6s}")
    for f, n in alvos:
        print(f"  {f.name[:50]:52s} {n:6d}")
    print(f"\n{len(alvos)} arquivo(s) · {sum(n for _, n in alvos)} ocorrência(s)")

    if args.dry_run:
        print("\n(dry-run — nada foi alterado)"); return 0

    BK.mkdir(parents=True, exist_ok=True)
    BK.chmod(0o700)
    tot_red = tot_rev = 0
    for f, _ in alvos:
        dest = BK / f.name
        shutil.copy2(f, dest)
        dest.chmod(0o600)

        linhas = f.read_text(errors="ignore").splitlines()
        saida, red, rev = [], 0, 0
        for l in linhas:
            nova, n = redige_linha(l)
            if not n:
                saida.append(l); continue
            # se a linha era JSON válido, a redigida também precisa ser
            era_json = False
            if f.suffix == ".jsonl":
                try:
                    json.loads(l); era_json = True
                except Exception:
                    era_json = False
            if era_json:
                try:
                    json.loads(nova)
                except Exception:
                    saida.append(l); rev += 1; continue
            saida.append(nova); red += 1
        f.write_text("\n".join(saida) + "\n")
        tot_red += red; tot_rev += rev
        # Backup só serve se algo deu errado. Se nenhuma linha foi revertida e o arquivo
        # continua com o mesmo número de linhas, a cópia (COM os segredos) é apagada na hora:
        # 05 e 07-Set ficaram 385 MB e 390 MB de segredos em ~/logs esperando rm manual.
        if not args.keep_backup and rev == 0 and len(saida) == len(linhas):
            dest.unlink(missing_ok=True)
        extra = f"  (revertidas {rev} por quebrar JSON)" if rev else ""
        print(f"  ✓ {f.name[:48]:50s} {red:3d} linha(s){extra}")

    print(f"\nTOTAL: {tot_red} linha(s) redigida(s) · {tot_rev} revertida(s)")
    restantes = list(BK.glob("*")) if BK.exists() else []
    if not restantes and BK.exists():
        BK.rmdir(); print("Backup: removido (redação verificada linha a linha)")
    else:
        print(f"Backup: {BK} — {len(restantes)} arquivo(s) mantido(s) (linha revertida ou --keep-backup); CONTÉM SEGREDOS")
    if pulados:
        print(f"\n⚠️  {len(pulados)} arquivo(s) de sessão ativa não foram tocados.")
        print("    Rode de novo depois de fechar essas sessões.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
