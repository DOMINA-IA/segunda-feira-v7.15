#!/usr/bin/env python3
"""Testes do env-guard.py. Rodar: python3 ~/framework/tests/test_env_guard.py"""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "env-guard.py"   # dentro do pacote
if not HOOK.exists():
    HOOK = Path.home() / ".claude" / "hooks" / "env-guard.py"            # já instalado
spec = importlib.util.spec_from_file_location("env_guard", HOOK)
eg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eg)

BLOQUEIA = [
    "cat .env",
    "cat ~/.env",
    "cat /opt/servico/.env",
    "head -5 .env.local",
    "tail .env.production",
    "grep META ~/.env",
    "grep -ri asaas ~/.env ~/projetos/utm-manager/.env",
    "grep ^DATABASE_URL .env | cut -d= -f2-",
    "sed -n 1,5p .env",
    "awk -F= '{print $2}' .env",
    "cd /opt/app && cat .env",
    "ssh root@1.2.3.4 'cat /opt/app/.env'",
    "ssh root@1.2.3.4 'cd /opt/app && grep TOKEN .env'",
    "bash -c \"cat .env\"",
    "sudo cat /root/.env",
    "cat < .env",
    "cat config/prod.env",
    "echo $(cat .env)",
    "cat .env 2>/dev/null",
    "cat .env | sed 's/A/B/'",
    "{ cat .env; }",
    "echo \"$(cat .env)\"",
    "grep \"META TOKEN\" .env",
    "docker exec app sh -c 'cat /app/.env'",
    "cat \"$PASTA/.env\"",
    "ssh root@1.2.3.4 bash <<'EOF'\ncat /opt/app/.env\nEOF",
    "if true; then cat .env; fi",
]

LIBERA = [
    "ls -la .env",
    "chmod 600 .env",
    "cp .env .env.bak",
    "source .env",
    "set -a; . ./.env; set +a",
    "cut -d= -f1 .env",
    "grep -c '^META_TOKEN=' ~/.env",
    "grep -q TOKEN .env && echo tem",
    "grep -l asaas ~/.env ~/_secrets/*",
    "TOKEN=$(grep '^TOKEN=' .env | cut -d= -f2-)",
    "U=$(grep ^DATABASE_URL .env | cut -d= -f2-); psql \"$U\" -c 'select 1'",
    "cat .env | wc -l",
    "cat .env | shasum",
    "cat .env > /tmp/copia",
    "cat .env.example",
    "cat .env.template",
    "head -3 README.md",
    "echo 'NOVA=1' >> .env",
    "cat > .env <<EOF",
    "sed -i 's/^A=.*/A=2/' .env",
    "git commit -m 'fix: bloquear cat .env no gate'",
    "echo 'nunca rode cat .env'",
    "grep -rn 'dotenv' src/",
    "cat environment.md",
    "python3 app.py --env-file .env",
    "docker compose --env-file .env up -d",
    "wc -l .env",
    "python3 -c \"print(m.analisar('cat .env'))\"",
    "git commit -m \"fix: cat .env bloqueado; grep TOKEN .env idem\"",
    "echo \"para ver rode cat .env\"",
    "python3 - <<'EOF'\ntexto = 'grep -ri x ~/.env'\ncat .env\nEOF",
    "cat > nota.md <<EOF\ncat .env\nEOF\nls",
]


class Comando(unittest.TestCase):
    def test_bloqueia(self):
        for c in BLOQUEIA:
            with self.subTest(c=c):
                self.assertTrue(eg.analisar_comando(c), f"deveria bloquear: {c}")

    def test_libera(self):
        for c in LIBERA:
            with self.subTest(c=c):
                self.assertEqual(eg.analisar_comando(c), "", f"deveria liberar: {c}")


class Ferramentas(unittest.TestCase):
    def d(self, tool, **inp):
        return eg.decidir({"tool_name": tool, "tool_input": inp})

    def test_read(self):
        self.assertTrue(self.d("Read", file_path="/Users/x/.env"))
        self.assertTrue(self.d("Read", file_path="C:\\Users\\x\\proj\\.env.local"))
        self.assertFalse(self.d("Read", file_path="/Users/x/.env.example"))
        self.assertFalse(self.d("Read", file_path="/Users/x/app.py"))

    def test_grep(self):
        self.assertTrue(self.d("Grep", pattern="KEY", path="/x/.env", output_mode="content"))
        self.assertTrue(self.d("Grep", pattern="KEY", path="/x", glob=".env*", output_mode="content"))
        self.assertFalse(self.d("Grep", pattern="KEY", path="/x/.env"))
        self.assertFalse(self.d("Grep", pattern="KEY", path="/x/.env", output_mode="count"))

    def test_powershell(self):
        self.assertTrue(self.d("PowerShell", command="Get-Content .env"))
        self.assertTrue(self.d("PowerShell", command="type C:\\proj\\.env"))
        self.assertFalse(self.d("PowerShell", command="Test-Path .env"))

    def test_outras_ferramentas(self):
        self.assertFalse(self.d("Write", file_path="/x/.env", content="A=1"))


class Processo(unittest.TestCase):
    def roda(self, payload, env=None):
        import os
        e = dict(os.environ)
        e.pop("ENV_GUARD", None)
        e.update(env or {})
        return subprocess.run([sys.executable, str(HOOK)], input=payload,
                              capture_output=True, text=True, env=e)

    def test_deny_em_json(self):
        r = self.roda(json.dumps({"tool_name": "Bash", "tool_input": {"command": "cat .env"}}))
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_silencioso_quando_seguro(self):
        r = self.roda(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_fail_open(self):
        r = self.roda("isto nao e json")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_desligado(self):
        r = self.roda(json.dumps({"tool_name": "Read", "tool_input": {"file_path": ".env"}}),
                      env={"ENV_GUARD": "off"})
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main(verbosity=1)
