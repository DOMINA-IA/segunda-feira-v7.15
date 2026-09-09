#!/usr/bin/env python3
"""
Validador bloqueante de acentuação PT-BR para scripts de geração de conteúdo.

Uso:
    python3 validate-pt-accents.py <arquivo1.py> [arquivo2.py ...]
    python3 validate-pt-accents.py --dir /tmp/posts/

Saídas:
    exit 0  — passou (zero ocorrências)
    exit 1  — falhou (lista ocorrências e bloqueia)

Regra: scripts de renderização PIL/Pillow para Instagram NÃO podem ter palavras
sem acento ou cedilha em strings que serão renderizadas. Pillow renderiza UTF-8
corretamente — o erro é HUMANO ao digitar.

Origem: incidente 09-Mai-2026 (3 sessões consecutivas com mesmo erro).
"""
import re
import sys
import os
from pathlib import Path

WORDS_FORBIDDEN = {
    "voce": "você",
    "nao": "não",
    "acoes": "ações",
    "acao": "ação",
    "autonoma": "autônoma",
    "autonomas": "autônomas",
    "autonomo": "autônomo",
    "autonomos": "autônomos",
    "automacao": "automação",
    "automatico": "automático",
    "automatica": "automática",
    "anomala": "anômala",
    "anomalo": "anômalo",
    "relatorio": "relatório",
    "relatorios": "relatórios",
    "negocio": "negócio",
    "negocios": "negócios",
    "empresario": "empresário",
    "empresarios": "empresários",
    "empresaria": "empresária",
    "estrategia": "estratégia",
    "estrategias": "estratégias",
    "estrategico": "estratégico",
    "estrategica": "estratégica",
    "produtividade": "produtividade",  # ok, mas alguns escrevem produtivvidade — keep watch
    "ferias": "férias",
    "geracao": "geração",
    "opcao": "opção",
    "opiniao": "opinião",
    "decisao": "decisão",
    "decisoes": "decisões",
    "informacao": "informação",
    "informacoes": "informações",
    "producao": "produção",
    "salario": "salário",
    "salarios": "salários",
    "unica": "única",
    "unico": "único",
    "aplicacao": "aplicação",
    "operacao": "operação",
    "operacoes": "operações",
    # "operacional" — palavra correta SEM acento; removida do dicionário
    "conciliacao": "conciliação",
    "conexao": "conexão",
    "conexoes": "conexões",
    "rescisao": "rescisão",
    "graca": "graça",
    "gracas": "graças",
    "construido": "construído",
    "construida": "construída",
    "excecao": "exceção",
    "excecoes": "exceções",
    "transicao": "transição",
    "transicoes": "transições",
    "atencao": "atenção",
    "convencao": "convenção",
    "questao": "questão",
    "questoes": "questões",
    "razao": "razão",
    "razoes": "razões",
    "patriao": "patrão",
    "padroes": "padrões",
    "evolucao": "evolução",
    "comunicacao": "comunicação",
    "instrucao": "instrução",
    "instrucoes": "instruções",
    "infraestrutura": "infraestrutura",  # ok
    "equilibrio": "equilíbrio",
    "comecar": "começar",
    "comeca": "começa",
    "comecou": "começou",
    "gestao": "gestão",
    "gestoes": "gestões",
    "metrica": "métrica",
    "metricas": "métricas",
    "metodo": "método",
    "metodos": "métodos",
    "padrao": "padrão",
    "padroes": "padrões",
    "proximo": "próximo",
    "proxima": "próxima",
    "ultimo": "último",
    "ultima": "última",
    "noticia": "notícia",
    "noticias": "notícias",
    "diagnostico": "diagnóstico",
    "diagnosticos": "diagnósticos",
    "transicao": "transição",
    "atencao": "atenção",
    "intencao": "intenção",
    "tendencia": "tendência",
    "tendencias": "tendências",
    "frequencia": "frequência",
    "experiencia": "experiência",
    "experiencias": "experiências",
    "diferenca": "diferença",
    "diferencas": "diferenças",
    "consequencia": "consequência",
    "consequencias": "consequências",
    "audiencia": "audiência",
    "essencia": "essência",
    "comerciais": "comerciais",  # ok
    "porem": "porém",
    "alem": "além",
    "tambem": "também",
    "aqui_esta": "aqui está",
    "voces": "vocês",
    "ja": "já",  # difícil — só sinaliza se "já" puder ser palavra sozinha
    "so": "só",  # difícil
    "ate": "até",  # difícil
    "esta": "está",  # difícil
    "estao": "estão",
    "vao": "vão",
    "sao": "são",
    "milhoes": "milhões",
    "milhao": "milhão",
    "amanha": "amanhã",
    "manha": "manhã",
    "manhas": "manhãs",
    "atras": "atrás",
    "atraves": "através",
    "depois_de_amanha": "depois de amanhã",
    "ontem": "ontem",  # ok
    "magico": "mágico",
    "magica": "mágica",
    "logico": "lógico",
    "logica": "lógica",
    "tecnico": "técnico",
    "tecnica": "técnica",
    "tecnologia": "tecnologia",  # ok
    "publico": "público",
    "publica": "pública",
    "basico": "básico",
    "basica": "básica",
    "rapido": "rápido",
    "rapida": "rápida",
    "ambito": "âmbito",
    "video": "vídeo",
    "videos": "vídeos",
    "audio": "áudio",
    "ate_la": "até lá",
    "agora_e_quando": "agora é quando",
    "lider": "líder",
    "lideres": "líderes",
    "lideranca": "liderança",
    "criterio": "critério",
    "criterios": "critérios",
    "principio": "princípio",
    "principios": "princípios",
    "perimetro": "perímetro",
    "imovel": "imóvel",
    "imoveis": "imóveis",
    "movel": "móvel",
    "moveis": "móveis",
    "facil": "fácil",
    "dificil": "difícil",
    "util": "útil",
    "futil": "fútil",
    "agil": "ágil",
    "frigil": "frágil",
    "fragil": "frágil",
    "estavel": "estável",
    "instavel": "instável",
    "movel": "móvel",
    "agil": "ágil",
    "decimal": "decimal",  # ok
    "fenomeno": "fenômeno",
    "fenomenos": "fenômenos",
    "exito": "êxito",
    "Le": "Lê",  # contexto: "Le briefing"
}

# Strings literais Python — onde achamos texto que vira PNG
STRING_RE = re.compile(r'''(?P<quote>["'])(?P<text>[^"'\n]*?)(?P=quote)''')

# Caracteres Unicode complexos que fontes Montserrat/Bebas/Georgia NÃO renderizam
# (resultam em quadrado X ou tofu □ na imagem)
UNICODE_FORBIDDEN = {
    "☒": "use seta → ou texto",
    "☑": "use seta → ou ✓ texto",
    "☐": "use texto",
    "⚠": "use 'AVISO:' ou 'ATENÇÃO:'",
    "⚡": "use texto 'RÁPIDO' ou número",
    "🔒": "use 'SEGURO' ou 'PROTEGIDO'",
    "📊": "use texto 'DADOS' ou tipografia",
    "⭐": "use ★ (asterisk fonts) ou texto",
    "✅": "use ✓ ou 'OK' texto",
    "❌": "use ✗ ou 'NÃO' texto",
    "⚙️": "use 'CONFIG' texto",
    "💎": "use 'PREMIUM' texto",
    "🚀": "use 'ESCALAR' texto",
    "🎯": "use 'FOCO' texto",
    "🔥": "use 'HOT' ou cor visual",
    "💰": "use 'R$' texto",
    "📈": "use linha visual ou texto",
    "📉": "use linha visual ou texto",
    "🤖": "use 'AGENTE' ou 'IA' texto",
}

# Nomes próprios PROIBIDOS para agentes em conteúdo DOMINA.IA
# (Origem: sessão 09-Mai-2026 — agentes são sistemas funcionais, não personagens)
NOMES_AGENTE_PROIBIDOS = {
    'Sobral': 'use AGENTE DE TRÁFEGO ou descrição funcional',
    'Atlas': 'use AGENTE DE PROGRAMAÇÃO ou descrição funcional',
    'Aurora': 'use AGENTE COMERCIAL ou descrição funcional',
    'Íris': 'use AGENTE DE FOLLOW-UP ou descrição funcional',
    'Iris': 'use AGENTE DE FOLLOW-UP ou descrição funcional',
    'Sentinela': 'use AGENTE DE TRACKING ou descrição funcional',
    'Alfa': 'use AGENTE COMERCIAL ou descrição funcional',
    'Íon': 'use AGENTE TÉCNICO ou descrição funcional',
    'Ion': 'use AGENTE TÉCNICO ou descrição funcional',
    'Mestre': 'use AGENTE PRINCIPAL ou descrição funcional',
}



def find_violations(filepath: str) -> list[tuple[int, str, str, str]]:
    """Retorna lista de (linha, palavra_errada, sugestao, contexto)."""
    violations = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, start=1):
                # Ignorar linhas marcadas com # noqa ou # noqa-unicode
                if "# noqa" in raw:
                    continue
                # Ignorar linhas que são prints de debug/erro do próprio validador
                # (strings com \n no início ou que contenham BLOQUEADO/corrija)
                if "BLOQUEADO" in raw or "corrija acentos" in raw:
                    continue
                # Procurar dentro de strings Python (delimitadas por aspas)
                for match in STRING_RE.finditer(raw):
                    text = match.group("text")
                    # Skip strings curtas (< 3 chars), comentários óbvios, code
                    if len(text) < 3:
                        continue
                    if text.startswith(("http", "/", ".py", "@")):
                        continue
                    # 1. Tokenize por palavras (delimitadores: espaço, pontuação)
                    tokens = re.findall(r"[A-Za-zÀ-ÿ]+", text)
                    for tok in tokens:
                        tok_lower = tok.lower()
                        if tok_lower in WORDS_FORBIDDEN:
                            sug = WORDS_FORBIDDEN[tok_lower]
                            violations.append((lineno, tok, sug, text.strip()))
                    # 2. Caracteres Unicode complexos (só em strings de conteúdo visual)
                    # Skip se a linha é claramente mensagem de debug/erro do framework
                    if "file=_sys.stderr" in raw or "file=sys.stderr" in raw:
                        continue
                    for char in text:
                        if char in UNICODE_FORBIDDEN:
                            sug = UNICODE_FORBIDDEN[char]
                            violations.append((lineno, char, sug, text.strip()))
                    # 3. Nomes próprios proibidos para agentes IA (DOMINA.IA)
                    for nome, sug in NOMES_AGENTE_PROIBIDOS.items():
                        if re.search(r"\b" + re.escape(nome) + r"\b", text):
                            violations.append((lineno, nome, sug, text.strip()))
    except Exception as e:
        print(f"[ERRO] Falha ao ler {filepath}: {e}", file=sys.stderr)
    return violations


def main():
    if len(sys.argv) < 2:
        print("Uso: validate-pt-accents.py <arquivo.py> [arquivos...] | --dir <pasta>")
        sys.exit(2)

    files = []
    if sys.argv[1] == "--dir":
        base = sys.argv[2]
        for root, _, names in os.walk(base):
            for n in names:
                if n.endswith((".py", ".md")):
                    files.append(os.path.join(root, n))
    else:
        files = sys.argv[1:]

    total_violations = 0
    by_file: dict[str, list] = {}
    for f in files:
        viols = find_violations(f)
        if viols:
            by_file[f] = viols
            total_violations += len(viols)

    if total_violations == 0:
        print(f"✓ OK — {len(files)} arquivo(s) verificado(s), zero palavras sem acento.")
        sys.exit(0)

    print(f"✗ FALHOU — {total_violations} palavra(s) sem acento em {len(by_file)} arquivo(s):\n")
    for f, viols in by_file.items():
        print(f"  📄 {f}")
        for lineno, wrong, sug, ctx in viols:
            ctx_short = (ctx[:60] + "…") if len(ctx) > 60 else ctx
            print(f"     L{lineno}: '{wrong}' → '{sug}'  [contexto: {ctx_short}]")
        print()

    print(f"Total: {total_violations} ocorrência(s). BLOQUEIE a renderização e CORRIJA antes de prosseguir.")
    sys.exit(1)


if __name__ == "__main__":
    main()
