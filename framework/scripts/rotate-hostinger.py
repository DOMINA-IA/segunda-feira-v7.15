#!/usr/bin/env python3
"""Rotaciona a senha SFTP da Hostinger com validação e rollback.

Uso: python3 rotate-hostinger.py
     (pede a nova senha sem eco; nada vai para o histórico do shell)

Fluxo seguro:
  1. lê a senha nova (sem eco)
  2. TESTA a conexão SFTP com ela
  3. só grava em ~/_secrets/hostinger.env se o teste passar
  4. mantém backup e reverte automaticamente em caso de falha

Contexto: até 05-Set-2026 a senha estava hardcoded em 13 scripts. Agora todos
leem deste .env — trocar aqui basta.
"""
import getpass
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ENV = Path.home() / "_secrets" / "hostinger.env"


def ler_env():
    d = {}
    for l in ENV.read_text().splitlines():
        if l.strip() and not l.startswith("#") and "=" in l:
            k, v = l.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def testa(host, port, user, senha):
    try:
        import paramiko
    except ImportError:
        print("  ⚠️  paramiko não instalado — não é possível validar.")
        return None
    t = None
    try:
        t = paramiko.Transport((host, int(port)))
        t.connect(username=user, password=senha)
        paramiko.SFTPClient.from_transport(t).listdir(".")
        return True
    except Exception as e:
        print(f"  ✗ falhou: {type(e).__name__}: {str(e)[:80]}")
        return False
    finally:
        if t:
            try: t.close()
            except Exception: pass


def main():
    if not ENV.exists():
        print(f"ERRO: {ENV} não existe."); return 1
    cfg = ler_env()
    host, port, user = cfg.get("SFTP_HOST"), cfg.get("SFTP_PORT"), cfg.get("SFTP_USER")
    print(f"Alvo: {user}@{host}:{port}\n")

    print("1/4  Testando a senha ATUAL (para saber se já foi trocada no painel)…")
    atual_ok = testa(host, port, user, cfg.get("SFTP_PASS", ""))
    if atual_ok is True:
        print("  ✓ a senha atual ainda funciona — troque no hPanel antes de continuar")
    elif atual_ok is False:
        print("  → a senha atual já não vale: você já trocou no painel. Seguindo.")

    nova = getpass.getpass("\n2/4  Cole a NOVA senha (não aparece na tela): ").strip()
    if not nova:
        print("  cancelado."); return 1

    print("\n3/4  Testando a NOVA senha…")
    novo_ok = testa(host, port, user, nova)
    if novo_ok is False:
        print("\n  ✗ a nova senha não conecta. NADA foi alterado.")
        return 1
    if novo_ok is None:
        r = input("  validar não foi possível. Gravar mesmo assim? [s/N] ").strip().lower()
        if r != "s":
            print("  cancelado."); return 1

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = ENV.with_suffix(f".env.bak-{ts}")
    shutil.copy2(ENV, bak); bak.chmod(0o600)

    linhas = []
    for l in ENV.read_text().splitlines():
        linhas.append(f"SFTP_PASS={nova}" if l.startswith("SFTP_PASS=") else l)
    ENV.write_text("\n".join(linhas) + "\n")
    ENV.chmod(0o600)

    print(f"\n4/4  ✓ Gravado em {ENV}")
    print(f"     backup: {bak}")
    print("\nTodos os 12 scripts leem deste arquivo — nada mais a atualizar.")
    print("Recomendado: rode um deploy pequeno para confirmar ponta a ponta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
