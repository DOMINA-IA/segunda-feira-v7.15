#!/usr/bin/env python3
"""
extract-seed-memory.py — Extrai o SEED de memoria para o pacote publico.

Objetivo: o aluno comeca com o loop de aprendizado ja alimentado por licoes
de ENGENHARIA, sem receber nenhum dado de negocio.

Principio do corte — o teste e o GRAU DE ACOPLAMENTO, nao o assunto:

  ENTRA   licao que continua verdadeira depois de trocar todo nome proprio
          por um placeholder. Ex.: "monitor que repete o mesmo alerta por
          semanas: conferir se o recurso ainda existe antes de mexer no
          threshold" — vale em qualquer stack.

  SAI     licao que SO existe por causa de um sistema nomeado. Ex.: "no
          <cliente>, upload de ficha usa POST /api/x/:id/upload com multer
          memoryStorage 20MB" — sanitizar deixa uma frase oca, e o endpoint
          e informacao de terceiro.

  SAI     qualquer coisa com dado: valor financeiro, metrica de negocio,
          nome de pessoa/cliente, credencial, IP, host, id de plataforma.

Na duvida, CORTA. Um seed menor e util; um seed que vaza e um incidente.

Uso:
  python3 extract-seed-memory.py --heuristics <arquivo.jsonl> --out <dir> [--dry-run]
"""
import argparse
import importlib.util
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# 0. SEGUNDA FONTE — o gate de publicacao, carregado como modulo.
#
# Os criterios deste arquivo e os do gate falham de formas DIFERENTES: o filtro
# aqui raciocina por dominio ("isso e licao de engenharia?"), o gate por padrao
# literal ("isso parece nome de cliente?"). Rodar so um deixa passar o que o
# outro pegaria — na primeira execucao real o gate pegou uma entrada com nome
# de perfil de referencia que o filtro de dominio aprovou.
# Toda entrada precisa passar nos DOIS.
# ---------------------------------------------------------------------------
def _carrega_gate():
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "validate-publish.py")
    try:
        spec = importlib.util.spec_from_file_location("gate", caminho)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f"ERRO: nao consegui carregar o gate ({e}).", file=sys.stderr)
        print("O seed NAO sera gerado sem a segunda fonte de validacao.", file=sys.stderr)
        sys.exit(2)


GATE = _carrega_gate()


def passa_no_gate(texto):
    """True se nenhuma regra CRITICO/ALTO do gate casar com o texto.

    NOTA: o gate usa fronteira (?<![A-Za-z0-9])/(?![A-Za-z0-9]), que e mais
    estrita que \b. Isso importa: em regex "_" e word character, entao
    \bAcmeCorp\b NAO casa em "acmecorp_raw" — um nome de cliente escondido
    dentro de um identificador de tabela passa despercebido.
    """
    # ALLOW isenta so os checks GENERICOS. Identificador privado (local:*)
    # nunca e isento: um "<slug>" na frase nao apaga a sigla do cliente ao
    # lado. Uma heuristica com "/opt/<produto-real>/.env" passou por isso.
    isenta_genericos = bool(GATE.ALLOW_LINE.search(texto))
    for cat, sev, rx, _fix in GATE.CHECKS:
        if isenta_genericos and not cat.startswith("local:"):
            continue
        if sev in ("CRITICO", "ALTO") and rx.search(texto):
            return False, cat
    return True, None

# ---------------------------------------------------------------------------
# 1. EXCLUSAO POR DADO — qualquer match descarta a entrada inteira.
# ---------------------------------------------------------------------------
DADO = [
    ("valor-financeiro",  re.compile(r"R\$\s?[\d.,]+|\b\d+\s?(mil|k)\b", re.I)),
    ("metrica-negocio",   re.compile(r"\b(CPL|CPA|ROAS|ROI|MRR|LTV|CAC|ticket\s*medio|"
                                     r"taxa\s+de\s+(conversao|convers[aã]o)|faturamento|receita)\b", re.I)),
    ("percentual-negocio",re.compile(r"\b\d{1,3}([.,]\d+)?%")),
    # Nomes de cliente e de pessoa NAO ficam listados aqui: sao literais
    # privados e este arquivo e distribuido. Vem de identificadores.local.json
    # atraves do gate (funcao passa_no_gate abaixo), que carrega esse arquivo.
    # Sem o local.json, o gate ainda barra por classe (e-mail, telefone, CPF),
    # mas a cobertura de nomes proprios depende de voce preencher o arquivo.
    ("credencial",        re.compile(r"(senha|password|token|api[_-]?key|secret|credencial)\s*[:=]", re.I)),
    ("host-ip",           re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b|\bsrv\d+|\bu\d{9}\b")),
    ("dominio-privado",   re.compile(r"[a-z0-9-]+\.(com\.br|com)\b", re.I)),
    ("id-plataforma",     re.compile(r"\b\d{12,}\b|act_\d+")),
    ("path-pessoal",      re.compile(r"/Users/|/home/[a-z]+/|~/(projetos|clientes)/", re.I)),
    ("canal-privado",     re.compile(r"\bINEMA\b|@[a-z0-9_.]+\b(?!\s*(agent|squad))", re.I)),
]

# ---------------------------------------------------------------------------
# 2. ACOPLAMENTO — a licao so existe por causa de um sistema especifico?
#    Sinais: endpoint concreto, nome de arquivo/tabela do projeto, componente
#    proprietario. Sanitizar isso deixaria uma frase sem conteudo.
# ---------------------------------------------------------------------------
ACOPLADA = [
    ("endpoint-concreto", re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/\S+")),
    # prefixo de tabela do projeto do usuario: declare os seus em
    # identificadores.local.json (chave "outros"). Nao listar aqui:
    # este arquivo e distribuido.
    ("arquivo-projeto",   re.compile(r"\b(sites-enabled|ds-components|admin\.php|server\.js)\b", re.I)),
    ("componente-proprio",re.compile(r"\bds(Confirm|Prompt|Alert)\b")),
    ("porta-servico",     re.compile(r":\d{4}\b")),
]

# ---------------------------------------------------------------------------
# 3. INCLUSAO — sinais de licao de engenharia transferivel.
# ---------------------------------------------------------------------------
GENERICA = re.compile(
    r"\b(sempre|nunca|antes de|depois de|quando|ao\s+\w+ar|verificar|conferir|validar|"
    r"testar|deploy|cache|regex|template|timezone|UTC|encoding|transa[cç][aã]o|"
    r"idempot|race|concorr|rollback|backup|migra[cç][aã]o|schema|indice|query|"
    r"escape|sanitiz|permiss[aã]o|autentica|smoke|lint|typecheck|log|alerta|"
    r"monitor|threshold|retry|timeout|webhook|api|json|yaml|git|commit|branch)\b", re.I)

# ---------------------------------------------------------------------------
# 4. DOMINIO — separa licao de SISTEMA de metodo COMERCIAL.
#    Nenhum dos dois e "dado", mas o segundo e ativo de negocio do autor
#    (como prospectar, como analisar concorrente, como montar oferta).
#    Sai em arquivo proprio para o autor decidir se distribui.
# ---------------------------------------------------------------------------
COMERCIAL = re.compile(
    r"\b(concorrente|e-?commerce|oferta|copy|criativo|an[uú]ncio|campanha|"
    r"lan[cç]amento|funil|lead(s)?\b|prospec|outreach|nutri[cç][aã]o|"
    r"carrossel|reel|thumbnail|headline|hook\b|persona|p[uú]blico[- ]alvo|"
    r"name\s*tent|feed\b|engajamento|alcance|seguidores|checkout|upsell)\b", re.I)

MIN_CHARS = 60          # frase curta demais nao carrega licao
MAX_CHARS = 400


def classificar(texto):
    """Retorna (entra: bool, motivo: str, dominio: 'engenharia'|'comercial')."""
    t = (texto or "").strip()
    if not (MIN_CHARS <= len(t) <= MAX_CHARS):
        return False, "tamanho", None
    for nome, rx in DADO:
        if rx.search(t):
            return False, f"dado:{nome}", None
    for nome, rx in ACOPLADA:
        if rx.search(t):
            return False, f"acoplada:{nome}", None
    if not GENERICA.search(t):
        return False, "sem-sinal-tecnico", None
    # segunda fonte: o gate de publicacao, com criterio independente
    ok_gate, cat = passa_no_gate(t)
    if not ok_gate:
        return False, f"gate:{cat}", None
    dominio = "comercial" if COMERCIAL.search(t) else "engenharia"
    return True, f"ok:{dominio}", dominio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heuristics", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    buckets = {"engenharia": [], "comercial": []}
    motivos = {}
    total = 0
    vistos = set()
    for linha in open(a.heuristics, encoding="utf-8"):
        try:
            r = json.loads(linha)
        except json.JSONDecodeError:
            continue
        total += 1
        texto = (r.get("heuristic") or "").strip()
        ok, motivo, dominio = classificar(texto)
        motivos[motivo] = motivos.get(motivo, 0) + 1
        if not ok:
            continue
        # deduplica por prefixo normalizado (o pool tem variantes da mesma licao)
        chave = re.sub(r"\W+", "", texto.lower())[:90]
        if chave in vistos:
            motivos["duplicada"] = motivos.get("duplicada", 0) + 1
            continue
        vistos.add(chave)
        buckets[dominio].append({
            # id novo: o do autor referencia episodio dele, que nao vai junto
            "id": f"seed_{dominio[:3]}_{len(buckets[dominio]):04d}",
            "agent": r.get("agent", "@dev"),
            "heuristic": texto,
            # confianca reiniciada: no ambiente do aluno ainda nao foi validada
            "confidence": 0.5,
            "times_validated": 0,
            "times_failed": 0,
            "triggered_count": 0,
            "origin": "seed-v7.15",
        })
    entradas = buckets["engenharia"]

    print(f"=== EXTRACAO DE SEED ===\n")
    print(f"{'MOTIVO':28} QTD")
    print("-" * 40)
    for m, n in sorted(motivos.items(), key=lambda x: -x[1]):
        print(f"{m:28} {n:5}")
    print("-" * 40)
    print(f"{'ENGENHARIA (vai no pacote)':28} {len(buckets['engenharia']):5}")
    print(f"{'COMERCIAL (decisao do autor)':28} {len(buckets['comercial']):5}")
    print(f"{'de um total de':28} {total:5}")

    if a.dry_run:
        print("\n(dry-run: nada escrito)")
        return

    os.makedirs(a.out, exist_ok=True)
    for dominio, itens in buckets.items():
        nome = ("heuristics-seed.jsonl" if dominio == "engenharia"
                else "heuristics-comercial-NAO-DISTRIBUIR.jsonl")
        destino = os.path.join(a.out, nome)
        with open(destino, "w", encoding="utf-8") as fh:
            for e in itens:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"\nescrito: {destino}  ({len(itens)} entradas)")


if __name__ == "__main__":
    main()
