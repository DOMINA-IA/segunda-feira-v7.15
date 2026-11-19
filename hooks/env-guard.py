#!/usr/bin/env python3
"""
env-guard.py — PreToolUse hook que impede o conteúdo de um .env de entrar na conversa.

Origem: 19-Nov-2026, apontado por um aluno. Com `Read(*)` e `Bash(cat *)` liberados,
um agente que abre o .env joga as chaves na conversa: elas seguem para a API e ficam em
texto puro no histórico local (~/.claude/projects/*.jsonl), sem prazo.

Cobre:
- Read  : arquivo .env                              -> deny
- Grep  : .env com output_mode "content"            -> deny
- Bash / PowerShell : comando que IMPRIME um .env   -> deny
  (cat, head, tail, grep sem -c/-l/-q, sed sem -i, awk, Get-Content...)

Não bloqueia o uso legítimo, que não imprime o valor:
- `VAR=$(grep '^NOME=' .env | cut -d= -f2-)`   captura sem imprimir
- `source .env`, `set -a; . .env`               carrega no ambiente
- `cut -d= -f1 .env`                            só os nomes
- `grep -c` / `grep -q` / `grep -l`             só existência
- `cat .env | wc -l`, `... | shasum`, `... > arquivo`, `sed -i`, `>> .env`
- arquivos de exemplo (.env.example, .env.template, .env.sample)

É uma guarda contra leitura ACIDENTAL, não uma jaula: `echo $CHAVE` depois de um
`source`, ou um script que abre o arquivo e imprime, passam. Fail-open: qualquer erro
interno libera o comando (um hook quebrado não pode parar o trabalho).

Desligar conscientemente: variável de ambiente ENV_GUARD=off.
Saída: JSON com permissionDecision "deny" no stdout; exit sempre 0.
"""
import json
import os
import re
import sys

EXEMPLO = re.compile(r"(example|sample|template|tpl|dist|defaults)$", re.IGNORECASE)
NOME_ENV = re.compile(r"^(\.env($|[.*_-].*)|\.envrc|.+\.env)$", re.IGNORECASE)

IMPRESSORAS = {
    "cat", "head", "tail", "less", "more", "bat", "nl", "tac", "strings", "xxd", "od",
    "hexdump", "base64", "sort", "uniq", "awk", "gawk", "sed", "grep", "egrep", "fgrep",
    "rg", "ag", "cut", "paste", "diff", "column", "fold", "rev",
    # PowerShell / cmd
    "get-content", "gc", "type", "select-string", "sls",
}
# Comandos que executam outro comando: a impressora pode vir em qualquer posição.
ENVELOPES = {
    "sudo", "ssh", "bash", "sh", "zsh", "docker", "xargs", "env", "time", "nohup",
    "timeout", "command", "exec", "eval", "watch", "powershell", "pwsh", "cmd",
}
# Estágio posterior do pipe que não deixa o valor chegar à tela.
SANEADORES = {"wc", "md5", "md5sum", "shasum", "sha1sum", "sha256sum", "pbcopy", "measure-object"}


def eh_env(caminho: str) -> bool:
    """True se o caminho aponta para um arquivo de segredos (.env e variações)."""
    c = (caminho or "").strip().strip("'\"`;,)(")
    if not c:
        return False
    base = re.split(r"[/\\]", c)[-1]
    if not base or not NOME_ENV.match(base):
        return False
    return not EXEMPLO.search(base)


def _flags(tokens):
    """Letras de flags curtas agrupadas (-rin -> r,i,n) e flags longas inteiras."""
    curtas, longas = set(), set()
    for t in tokens:
        if t.startswith("--"):
            longas.add(t.split("=")[0])
        elif t.startswith("-") and len(t) > 1 and not t[1].isdigit():
            curtas.update(t[1:])
    return curtas, longas


def _estagio_seguro(cmd: str, tokens) -> bool:
    """O próprio comando lê o .env mas não imprime valor."""
    curtas, longas = _flags(tokens)
    if cmd in ("grep", "egrep", "fgrep", "rg", "ag"):
        if curtas & {"q", "l", "L", "c"}:
            return True
        if longas & {"--quiet", "--silent", "--count", "--files-with-matches",
                     "--files-without-match"}:
            return True
    if cmd == "cut":
        junto = " ".join(tokens)
        if re.search(r"-f\s*1(\s|$)", junto) and "-d" in junto:
            return True
    if cmd == "sed" and any(t.startswith("-i") or t == "--in-place" for t in tokens):
        return True
    if cmd in ("select-string", "sls") and "-quiet" in [t.lower() for t in tokens]:
        return True
    return False


def _le_env(tokens) -> str:
    """Devolve o .env que o estágio LÊ (ignora destino de `>` / `>>`), ou ''."""
    pular = False
    for t in tokens:
        if pular:                                  # destino de `>` / `>>` separado
            pular = False
            continue
        if t in (">", ">>"):
            pular = True
            continue
        if t.startswith(">"):                      # >arquivo colado: é escrita
            continue
        alvo = t.lstrip("<")                       # <arquivo: é leitura
        if eh_env(alvo):
            return alvo
    return ""


def _redireciona_para_arquivo(tokens) -> bool:
    for i, t in enumerate(tokens):
        if t in (">", ">>") and i + 1 < len(tokens) and tokens[i + 1] not in ("/dev/stdout", "/dev/tty"):
            return True
        if re.match(r"^>>?[^&>]", t) and not t.lstrip(">").startswith("/dev/std"):
            return True
    return False


def _comando_do_estagio(tokens):
    """(comando, tokens_relevantes). Pula `VAR=valor` e reconhece envelopes."""
    i = 0
    while i < len(tokens) and (tokens[i] in ("{", "then", "do", "else", "!")
                               or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i])):
        i += 1
    if i >= len(tokens):
        return "", []
    primeiro = re.split(r"[/\\]", tokens[i])[-1].lower()
    if primeiro.endswith(".exe"):
        primeiro = primeiro[:-4]
    if primeiro in IMPRESSORAS:
        return primeiro, tokens[i:]
    if primeiro in ENVELOPES:
        for j in range(i + 1, len(tokens)):
            nome = re.split(r"[/\\]", tokens[j])[-1].lower()
            if nome in IMPRESSORAS:
                return nome, tokens[j:]
    return "", []


SHELLS = {"ssh", "bash", "sh", "zsh", "sudo", "docker", "powershell", "pwsh"}


def _sem_heredoc_de_dados(comando: str) -> str:
    """Remove o corpo de heredocs que NÃO alimentam um shell.

    `python3 - <<'EOF' ... EOF` e `cat > nota.md <<EOF ... EOF` carregam texto/dados:
    uma linha do corpo que cite um comando não é executada. Já `ssh host bash <<EOF`
    executa o corpo, então ele continua sendo analisado.
    """
    linhas = comando.split("\n")
    saida, i = [], 0
    while i < len(linhas):
        linha = linhas[i]
        saida.append(linha)
        m = re.search(r"<<-?\s*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?", linha)
        if not m:
            i += 1
            continue
        marcador = m.group(1)
        antes = re.split(r"&&|\|\||;|\|", linha[:m.start()])[-1].split()
        j = 0
        while j < len(antes) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", antes[j]):
            j += 1
        dono = re.split(r"[/\\]", antes[j])[-1].lower() if j < len(antes) else ""
        k = i + 1
        corpo = []
        while k < len(linhas) and linhas[k].strip() != marcador:
            corpo.append(linhas[k])
            k += 1
        if dono in SHELLS:
            saida.extend(corpo)
        i = k + 1
    return "\n".join(saida)


def _desembrulhar_aspas(c: str) -> str:
    """Trata cada trecho entre aspas conforme quem o recebe.

    - recebido por um shell (ssh, bash -c, sudo, docker...) ou contendo `$(`/crase: é
      comando que será executado, então o conteúdo continua sendo analisado;
    - palavra única (nome de arquivo, padrão): fica como argumento;
    - texto com espaços dado a outro programa (python -c, git commit -m, echo): é dado,
      não comando, e sai da análise.
    """
    out, i = [], 0
    while i < len(c):
        ch = c[i]
        if ch not in "'\"":
            out.append(ch)
            i += 1
            continue
        j = i + 1
        while j < len(c) and c[j] != ch:
            if ch == '"' and c[j] == "\\":
                j += 1
            j += 1
        if j >= len(c):                      # aspa sem par: segue como estava
            out.append(" ")
            i += 1
            continue
        dentro = c[i + 1:j]
        estagio = re.split(r"&&|\|\||;|\n|\|", "".join(out))[-1].split()
        k = 0
        while k < len(estagio) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", estagio[k]):
            k += 1
        dono = re.split(r"[/\\]", estagio[k])[-1].lower() if k < len(estagio) else ""
        if dono in ENVELOPES or "$(" in dentro or "`" in dentro:
            out.append(" " + dentro + " ")
        elif not re.search(r"\s", dentro):
            out.append(dentro)
        else:
            out.append(" ")
        i = j + 1
    return "".join(out)


def analisar_comando(comando: str) -> str:
    """Devolve o caminho do .env que seria impresso, ou '' se o comando é seguro."""
    c = _sem_heredoc_de_dados(comando or "")
    c = re.sub(r"<<-?\s*[\"']?[A-Za-z_][A-Za-z0-9_]*[\"']?", " ", c)
    # Captura em variável não imprime: VAR=$(...)  /  VAR="$(...)"  /  VAR=`...`
    c = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*=\"?\$\((?:[^()]|\([^()]*\))*\)\"?", " ", c)
    c = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*=`[^`]*`", " ", c)
    c = c.replace("2>&1", " ").replace("&>", ">")
    c = re.sub(r"\d>\s*/dev/null", " ", c)
    # `ssh host 'cat .env'` e `bash -c "cat .env"` imprimem; `python -c "... 'cat .env'"` não.
    c = _desembrulhar_aspas(c)
    c = re.sub(r"[\"'`]", " ", c)
    c = c.replace("$(", " ; ").replace("(", " ; ").replace(")", " ; ")

    for pipeline in re.split(r"&&|\|\||;|\n|&", c):
        estagios = [e.split() for e in pipeline.split("|")]
        for i, tokens in enumerate(estagios):
            cmd, rel = _comando_do_estagio(tokens)
            if not cmd:
                continue
            alvo = _le_env(rel[1:])
            if not alvo:
                continue
            if _estagio_seguro(cmd, rel) or _redireciona_para_arquivo(rel):
                continue
            # Algum estágio adiante impede o valor de chegar à tela?
            salvo = False
            for depois in estagios[i + 1:]:
                dcmd_tokens = depois
                if not dcmd_tokens:
                    continue
                nome = re.split(r"[/\\]", dcmd_tokens[0])[-1].lower()
                if nome in SANEADORES or _redireciona_para_arquivo(dcmd_tokens):
                    salvo = True
                    break
                if nome in IMPRESSORAS and _estagio_seguro(nome, dcmd_tokens):
                    salvo = True
                    break
            if not salvo:
                return alvo
    return ""


def motivo(alvo: str) -> str:
    return (
        f"🔒 Leitura de segredo bloqueada: {alvo}\n"
        "   O conteúdo entraria na conversa e ficaria em texto puro no histórico local.\n"
        "   Use sem imprimir o valor:\n"
        "   • nomes das variáveis:  cut -d= -f1 <arquivo>\n"
        "   • a variável existe?    grep -c '^NOME=' <arquivo>\n"
        "   • usar o valor:         VAR=$(grep '^NOME=' <arquivo> | cut -d= -f2-)\n"
        "                           ou  set -a; source <arquivo>; set +a\n"
        "   • alterar:              sed -i / echo 'NOME=valor' >> <arquivo>\n"
        "   Liberar conscientemente (decisão humana): ENV_GUARD=off."
    )


def decidir(payload: dict) -> str:
    """Devolve o .env que seria exposto, ou ''."""
    ferramenta = payload.get("tool_name", "")
    entrada = payload.get("tool_input") or {}
    if not isinstance(entrada, dict):
        return ""
    if ferramenta == "Read":
        caminho = entrada.get("file_path", "")
        return caminho if eh_env(caminho) else ""
    if ferramenta == "Grep":
        if entrada.get("output_mode") != "content":
            return ""
        for chave in ("path", "glob"):
            valor = entrada.get(chave, "") or ""
            if eh_env(valor):
                return valor
        return ""
    if ferramenta in ("Bash", "PowerShell"):
        return analisar_comando(entrada.get("command", "") or "")
    return ""


def main():
    if os.environ.get("ENV_GUARD", "on").lower() == "off":
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
        alvo = decidir(payload)
    except Exception:
        sys.exit(0)  # fail-open
    if alvo:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": motivo(alvo),
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
