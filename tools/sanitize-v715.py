#!/usr/bin/env python3
"""
sanitize-v715.py — Sanitizador deterministico para o pacote publico do framework.

Filosofia: entrega a ARQUITETURA, nao os DADOS.
O aluno recebe o motor funcionando; a memoria (vault, episodios, heuristicas,
resultados de campanha) e dele, nao do autor.

Ordem importa: regras mais especificas primeiro. Trocar um handle antes do
dominio que o contem produziria "${HANDLE}.com.br". Por isso a lista e
ORDENADA e aplicada em sequencia, nunca por dict — e as regras LOCAIS
(literais do usuario) entram antes das genericas.

Uso:
  python3 sanitize-v715.py <dir> --dry-run   # so relata
  python3 sanitize-v715.py <dir> --apply     # escreve
"""
import os
import re
import sys
import collections

TEXT_EXT = {".md", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml",
            ".txt", ".cfg", ".ini", ".toml", ".html"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "tools"}

# ---------------------------------------------------------------------------
# SUBSTITUICOES — ordem = precedencia. Especifico antes de generico.
# (nome, regex, substituto)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# REGRAS GENERICAS — valem para qualquer pessoa, podem ser publicadas.
# Os literais especificos (seus hostnames, clientes, senhas) vem de
# identificadores.local.json, que NAO e versionado. Ver validate-publish.py
# para o porque desta separacao.
# ---------------------------------------------------------------------------
RULES = [
    # Documentos e dados pessoais
    ("cpf",          re.compile(r"\b(?!000\.000\.000)\d{3}\.\d{3}\.\d{3}-\d{2}\b"), "000.000.000-00"),
    ("cnpj",         re.compile(r"\b(?!00\.000\.000)\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"), "00.000.000/0000-00"),
    ("telefone-fmt", re.compile(r"\((?!00\))\d{2}\)\s?9?\d{4}[-\s]?\d{4}"), "(00) 00000-0000"),
    ("telefone-ddi", re.compile(r"\b55\d{2}9?\d{8}\b"), "${PHONE}"),
    ("whatsapp-jid", re.compile(r"\b\d{10,13}@s\.whatsapp\.net\b"), "${WHATSAPP_JID}"),

    # Caminhos
    ("path-home",    re.compile(r"/(?:Users|home)/(?!\$|\{|<|usuario|user\b|seu)[a-z][a-z0-9._-]{2,}"), "$HOME"),
    ("path-hifen",   re.compile(r"-(?:Users|home)-[a-z][a-z0-9-]{2,}"), "-HOME-"),
    ("path-py-macos",re.compile(r":?/Library/Frameworks/Python\.framework/Versions/[\d.]+/bin"), ""),

    # Identificadores de plataforma
    ("google-ads",   re.compile(r"\bAW-\d{9,}(?:/[A-Za-z0-9_-]{8,})?"), "AW-${GADS_CONVERSION_ID}"),
    ("ga4",          re.compile(r"\bG-[A-Z0-9]{8,}\b"), "G-${GA4_ID}"),
    ("gtm",          re.compile(r"\bGTM-[A-Z0-9]{5,}\b"), "GTM-${GTM_ID}"),
    ("ua",           re.compile(r"\bUA-\d{6,}-\d+\b"), "UA-${UA_ID}"),
    ("ad-account",   re.compile(r"act_\d{10,}"), "act_${AD_ACCOUNT_ID}"),
    ("id-longo",     re.compile(r"(?<![\d.])\d{15,17}(?![\d.])"), "${PLATFORM_ID}"),

    # Tokens (prefixos publicos)
    ("token-api",    re.compile(r"(?:sk-ant-|sk-|gh[pousr]_|AIza|xox[baprs]-|AKIA|EAA)[A-Za-z0-9_\-]{20,}"), "${API_TOKEN}"),

    # Infra generica
    ("hostname-srv", re.compile(r"\bsrv\d{6,}\b", re.I), "${VPS_HOSTNAME}"),
    ("user-hosped",  re.compile(r"\bu\d{9}\b"), "${HOSTING_USER}"),
    ("porta-ssh",    re.compile(r"(-p\s*)(?:65002|2222)\b"), r"\1${SSH_PORT}"),

    # Valores de negocio
    ("valor-real",   re.compile(r"R\$\s?\d{1,3}(?:\.\d{3}){1,}(?:,\d{2})?"), "R$ X.XXX"),

    # URL de post/perfil social: o post devolve o handle real do autor
    ("url-post-ig",   re.compile(r"instagram\.com/(?:p|reel|stories)/[A-Za-z0-9_-]{5,}/?"), "instagram.com/p/${POST_ID}/"),
    ("url-perfil-ig", re.compile(r"instagram\.com/(?!p/|reel/|stories/|explore|accounts)[a-z0-9_.]{3,30}/?(?![a-z0-9_./-])"), "instagram.com/${HANDLE}/"),
    ("url-tiktok",    re.compile(r"tiktok\.com/@[A-Za-z0-9_.]{3,}"), "tiktok.com/@${HANDLE}"),
    ("url-linkedin",  re.compile(r"linkedin\.com/in/[A-Za-z0-9-]{5,}"), "linkedin.com/in/${HANDLE}"),
    # Referencia nomeada a cofre (op://Vault/Item) revela a estrutura do 1Password
    ("op-ref",        re.compile(r"op://[^\s'\"]+"), "op://${VAULT}/${ITEM}/password"),

    # E-mail de terceiro (por ultimo: mais generico)
    ("email",        re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.|exemplo\.|test\.|seudominio|meudominio|s\.whatsapp)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "usuario@example.com"),
]


def _variantes(termo):
    """Gera as formas em que um mesmo nome aparece no mundo real.

    Procurar so o literal cadastrado deixa passar o obvio:
      "Joana"     no cadastro  !=  "Joâna"     no texto   (acento)
      "Acme Corp" no cadastro  !=  "acme-corp" no texto   (slug)
      "Beta Holding"           !=  "betaholding"          (colado)

    E a propria rule data-lookup-safety do framework: fuzzy ANTES de
    concluir que nao existe. Aqui quem precisa ser fuzzy e o sanitizador.
    """
    import unicodedata
    formas = {termo}
    # sem acento (NFD + descarta os diacriticos)
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", termo)
                         if unicodedata.category(c) != "Mn")
    formas.add(sem_acento)
    for base in list(formas):
        if " " in base:
            formas.add(base.replace(" ", "-"))   # slug com hifen
            formas.add(base.replace(" ", "_"))   # snake_case
            formas.add(base.replace(" ", ""))    # colado
    return {f for f in formas if len(f) >= 3}


def _regras_locais():
    """Literais especificos do usuario, de identificadores.local.json."""
    import json as _json
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "identificadores.local.json")
    if not os.path.exists(caminho):
        return []
    try:
        dados = _json.load(open(caminho, encoding="utf-8"))
    except Exception:
        return []
    destino = {
        "senhas_conhecidas": "${SENHA}", "hosts": "${VPS_HOST}",
        "hostnames": "${VPS_HOSTNAME}", "usuarios": "${USER}",
        "dominios": "seudominio.com.br", "emails": "usuario@example.com",
        "handles": "${HANDLE}", "nome_legal": "${CEO_NAME}",
        "telefones": "${PHONE}", "clientes": "CLIENTE_EXEMPLO",
        "pessoas": "${PESSOA}", "ids_plataforma": "${PLATFORM_ID}",
        "outros": "${REDIGIDO}",
    }
    regras = []
    for chave, repl in destino.items():
        termos = [t for t in dados.get(chave, []) if isinstance(t, str) and t.strip()]
        if not termos:
            continue
        # expande cada termo nas suas variantes reais (acento, slug, colado)
        expandidos = set()
        for t in termos:
            expandidos |= _variantes(t)
        # fronteira: (?![A-Za-z0-9]) e mais estrita que \b, que NAO existe
        # antes de "_" — por isso "acmecorp_raw" escapava de \bAcmeCorp\b
        alt = "|".join(re.escape(t) for t in sorted(expandidos, key=len, reverse=True))
        regras.append((f"local:{chave}",
                       re.compile(rf"(?<![A-Za-z0-9])(?:{alt})(?![A-Za-z0-9])", re.I),
                       repl))
    return regras


# Locais PRIMEIRO: sao os mais especificos e devem casar antes dos genericos.
RULES = _regras_locais() + RULES


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1] in TEXT_EXT:
                yield os.path.join(dirpath, fn)


def main():
    if len(sys.argv) < 2:
        print("uso: sanitize-v715.py <dir> [--apply|--dry-run]", file=sys.stderr)
        sys.exit(2)
    root = sys.argv[1]
    apply = "--apply" in sys.argv

    counts = collections.Counter()
    files_touched = 0

    for path in iter_files(root):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                original = fh.read()
        except OSError:
            continue

        text = original
        for name, rx, repl in RULES:
            text, n = rx.subn(repl, text)
            if n:
                counts[name] += n

        if text != original:
            files_touched += 1
            if apply:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)

    mode = "APLICADO" if apply else "DRY-RUN (nada escrito)"
    print(f"=== SANITIZACAO — {mode} ===\n")
    print(f"{'REGRA':24} SUBSTITUICOES")
    print("-" * 42)
    for name, n in counts.most_common():
        print(f"{name:24} {n:6}")
    print("-" * 42)
    print(f"{'TOTAL':24} {sum(counts.values()):6}  em {files_touched} arquivos")


if __name__ == "__main__":
    main()
