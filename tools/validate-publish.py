#!/usr/bin/env python3
"""
validate-publish.py — Gate anti-vazamento para publicacao.

Roda ANTES de qualquer push ou release. Escaneia o CONTEUDO dos arquivos (nao
apenas os nomes, como o .gitignore) procurando credenciais, PII, IPs, caminhos
absolutos, documentos e identificadores de conta.

DUAS CAMADAS, de proposito:

  1. GENERICA (neste arquivo) — classes de segredo: "senha atribuida a uma
     variavel", "token com prefixo conhecido", "CPF", "chave privada". Vale
     para qualquer pessoa e pode ser publicada sem risco.

  2. ESPECIFICA (identificadores.local.json, NAO versionado) — os literais de
     quem usa: seus hostnames, seus clientes, o formato das suas senhas.

Por que separado: um gate precisa conhecer o que procura. Se os seus literais
ficarem escritos aqui dentro e este arquivo for distribuido junto do pacote,
voce publica exatamente o dossie que queria proteger. Foi o que quase
aconteceu na v7.15 — o gate carregava 15 nomes de cliente, 2 hostnames, 4
formatos de senha e 5 IDs de conta, em texto plano, dentro da ferramenta que
existia para escondê-los.

Uso:
  python3 validate-publish.py <dir>          # escaneia um diretorio
  python3 validate-publish.py <dir> --json   # saida JSON

Exit: 0 = limpo | 1 = violacoes CRITICAS/ALTAS

Auditoria completa usa TRES lentes que falham diferente:
  a) este gate (regex por classe)
  b) uma ferramenta de mercado (ex.: detect-secrets, que pega alta entropia —
     foi ela que achou um Conversion ID do Google Ads invisivel para o regex)
  c) leitura humana de amostra (pega contexto que nenhuma das duas ve)

PONTOS CEGOS CONHECIDOS (regex por linha nao resolve — precisa de leitura):
  - nome quebrado em duas linhas ("Clinica Santa" / "Helena Ltda")
  - numero solto sem contexto (um ID de video de 9 digitos parece qualquer
    numero; um check de "9 digitos" acusaria o repositorio inteiro)
  - RE-IDENTIFICACAO POR AGREGACAO: nenhum termo aparece, mas ramo + cidade +
    stack + cronologia triangulam o cliente. So uma lente adversarial pega.
  - o que o autor nao sabia que precisava proteger (nome de funcionaria de
    cliente, fornecedor, parceiro) — nao esta na regua porque ninguem listou.
"LIMPO" deste gate significa: nenhum padrao conhecido casou. Nao significa
que o texto deixou de identificar alguem. Seis auditorias em cadeia acharam
dado real num pacote que este gate declarava limpo — cada uma no que a
anterior nao via.

Zero dependencias externas (stdlib only) -> portavel.
"""
import os
import re
import sys
import json

# Extensoes de texto que valem escanear
# ATENCAO: a lista de extensoes E o escopo do gate. O que nao esta aqui NAO
# e escaneado, e o gate nao avisa que nao olhou. Um nome de cliente ficou num
# .jsonl por isso. Ao adicionar um tipo de arquivo ao pacote, adicione aqui.
TEXT_EXT = {".md", ".py", ".sh", ".js", ".mjs", ".ts", ".json", ".jsonl",
            ".yaml", ".yml", ".txt", ".env.example", ".cfg", ".ini", ".toml",
            ".csv", ".hbs", ".sql", ".html", ".css", ".xml", ".env"}

# Diretorios a ignorar no scan
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "dist-v7.14", "dist-v7.15", "_archive", ".pytest_cache"}

# Arquivos que SAO ferramentas de deteccao: contem os PADROES por definicao,
# entao os checks genericos acusariam o detector a si mesmo.
#
# ATENCAO — a excecao e PARCIAL, de proposito. Uma auditoria adversarial
# mostrou que documentar um vazamento corrigido usando o nome real como
# exemplo didatico, dentro justamente destes arquivos, cria um ponto cego
# PERMANENTE: o identificador vai parar no unico lugar que o gate nunca le,
# e ninguem e avisado de novo. Pior que o vazamento original, porque toda
# correcao futura tende a repetir o padrao no mesmo lugar imune.
#
# Por isso: aqui pulam-se apenas os checks GENERICOS. Os literais privados
# (local:*) continuam sendo verificados. Use exemplo ficticio no comentario.
SKIP_FILES = {"redact-transcripts.py", "secret-scan.py", "validate-publish.py",
              "sanitize-v715.py", "extract-seed-memory.py",
              "identificadores.local.json", "identificadores.local.example.json"}

# ---------------------------------------------------------------------------
# CHECKS GENERICOS: (categoria, severidade, regex, dica)
# Severidade: CRITICO (bloqueia) | ALTO (bloqueia) | MEDIO (avisa)
#
# REGRA DE MANUTENCAO: nada de literal privado aqui. Se voce precisa detectar
# "o nome do meu cliente" ou "a minha senha", isso vai em
# identificadores.local.json, que nao e publicado.
# ---------------------------------------------------------------------------
CHECKS = [
    # === CREDENCIAIS (classes, nao valores) ===
    ("senha-atribuida", "CRITICO",
     re.compile(r"""(?:password|senha|passwd|pwd|PGPASSWORD)\s*[:=]\s*['"]?[A-Za-z0-9@!#$%&*._-]{6,}['"]?""", re.I),
     "Senha em texto plano. Usar variavel de ambiente + .env (chmod 600)."),

    ("connection-string-cred", "CRITICO",
     re.compile(r"[a-z][a-z0-9+]*://[^:@/\s'\"]+:[^@/\s'\"]+@", re.I),
     "Connection string com credencial embutida. Parametrizar a senha."),

    ("sshpass-expect", "CRITICO",
     re.compile(r"(sshpass\s+-p|send\s+\"[^\"]*@[^\"]*\\r\")", re.I),
     "Senha passada por linha de comando/expect. Usar chave SSH."),

    ("chave-privada-bloco", "CRITICO",
     re.compile(r"-----BEGIN\s+(?:RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY"),
     "Chave privada no repositorio. Remover o arquivo inteiro e rotacionar."),

    # === TOKENS DE API (prefixos publicos e conhecidos) ===
    ("token-api", "CRITICO",
     re.compile(r"(sk-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|"
                r"gh[pousr]_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_\-]{30,}|"
                r"xox[baprs]-[A-Za-z0-9\-]{10,}|AKIA[0-9A-Z]{16}|"
                r"EAA[A-Za-z0-9]{40,}|\d{8,10}:AA[A-Za-z0-9_\-]{30,})"),
     "Token de API. Remover e ROTACIONAR (publicado = comprometido)."),

    ("key-atribuida", "ALTO",
     re.compile(r"""(?:api[_-]?key|secret|access[_-]?token|bearer)\s*[:=]\s*['"][A-Za-z0-9_\-]{16,}['"]""", re.I),
     "Chave atribuida a variavel. Mover para .env."),

    # === IDENTIFICADORES DE CONTA DE PLATAFORMA ===
    # O regex nao "sabe" que um numero e um pixel: detecta a FORMA.
    ("google-ads-conversion", "ALTO",
     re.compile(r"\bAW-\d{9,}(?:/[A-Za-z0-9_-]{8,})?"),
     "Conversion ID/Label do Google Ads. Substituir por AW-XXXXXXXXX/XXXX."),

    ("google-analytics-id", "ALTO",
     re.compile(r"\bG-[A-Z0-9]{8,}\b|\bUA-\d{6,}-\d+\b|\bGTM-[A-Z0-9]{5,}\b"),
     "ID de GA4/GTM/UA. Substituir por placeholder."),

    ("ad-account", "ALTO",
     re.compile(r"act_\d{10,}"),
     "Ad account ID. Substituir por act_${AD_ACCOUNT_ID}."),

    # Faixa 12-17: a versao anterior exigia 15+ e deixou passar um ID interno
    # do WhatsApp de 14 digitos. Nao existe razao para o corte ser em 15.
    ("id-numerico-longo", "MEDIO",
     re.compile(r"(?<![\d.\w-])\d{12,17}(?![\d.\w-])"),
     "ID numerico longo (pixel/page/conta/JID). Verificar e parametrizar."),

    # Telefone brasileiro SEM DDI: 11 digitos comecando por DDD valido (11-99).
    # O check anterior exigia "55" na frente ou parenteses, e um numero de
    # terceiro anotado "sem DDI" passou ao lado de um que foi sanitizado.
    ("telefone-sem-ddi", "ALTO",
     re.compile(r"(?<![\d\w-])[1-9][1-9]9\d{8}(?![\d\w-])"),
     "Telefone BR sem DDI (11 digitos). Substituir por placeholder."),

    # Identificador opaco de servico (voz, avatar, workspace): hex/base62 longo
    # atribuido a variavel. Nao casa com api_key|secret|token, entao escapava.
    ("id-servico-opaco", "ALTO",
     re.compile(r"""(?:VOICE|AVATAR|WORKSPACE|PROJECT|ASSISTANT|AGENT|MODEL)_ID\s*[:=]\s*['"]?[A-Za-z0-9]{16,}""", re.I),
     "ID opaco de servico externo. Mover para .env."),

    # Variavel batizada com nome proprio: o valor pode ate ser generico, mas o
    # NOME entrega de quem e a conta.
    ("variavel-com-nome-proprio", "MEDIO",
     re.compile(r"\b[A-Z]{4,}_(?:HEYGEN|ELEVEN|OPENAI|META|GOOGLE|AWS|TELEGRAM)_[A-Z_]+\b"),
     "Nome de variavel com prefixo pessoal. Usar nome neutro."),

    # === INFRAESTRUTURA ===
    # Exige ao menos UM octeto de 2-3 digitos. Sem isso, numeracao de secao
    # de documento ("Artigo 6.1.2.1") era lida como IP — 84 falsos positivos
    # na primeira versao. Falso positivo em massa treina a ignorar o gate.
    ("ip-publico", "ALTO",
     re.compile(r"(?<![\d.\w])"
                r"(?!0\.|10\.|127\.|169\.254\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.|"
                r"22[4-9]\.|2[3-5]\d\.|203\.0\.113\.|198\.51\.100\.|192\.0\.2\.)"
                r"(?:\d{2,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                r"|\d{1,3}\.\d{2,3}\.\d{1,3}\.\d{1,3}"
                r"|\d{1,3}\.\d{1,3}\.\d{2,3}\.\d{1,3}"
                r"|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{2,3})"
                r"(?![\d.])"),
     "IP publico. Parametrizar via ${VPS_HOST} ou usar faixa de documentacao (203.0.113.x)."),

    ("hostname-servidor", "ALTO",
     re.compile(r"\bsrv\d{6,}\b", re.I),
     "Hostname de servidor. Parametrizar via ${VPS_HOSTNAME}."),

    ("usuario-hospedagem", "ALTO",
     re.compile(r"\bu\d{9}\b"),
     "Usuario de hospedagem compartilhada. Parametrizar."),

    ("path-home-nomeado", "ALTO",
     re.compile(r"/(?:Users|home)/(?!\$|\{|<|usuario|user\b|seu)[a-z][a-z0-9._-]{2,}/"),
     "Caminho absoluto com nome de usuario. Usar $HOME ou ~."),

    ("path-claude-hifenizado", "ALTO",
     re.compile(r"-(?:Users|home)-[a-z][a-z0-9-]{2,}"),
     "Caminho hifenizado com nome de usuario. Parametrizar."),

    ("certificado-keystore", "ALTO",
     re.compile(r"\.(p12|pfx|jks|keystore)(?![A-Za-z])"),
     "Referencia a certificado. Parametrizar via ${CERT_PATH}."),

    # === IDENTIFICADORES QUE PERMITEM RE-IDENTIFICAR ===
    # Achados da auditoria adversarial: mascarar o NOME nao basta se o texto
    # deixa o que aponta para ele. Um CNPJ virou "00.000.000/0000-00" mas a
    # chave de acesso da nota fiscal ficou ao lado — e a chave devolve o CNPJ
    # real numa consulta publica. O placeholder virou decoracao.
    ("chave-acesso-fiscal", "CRITICO",
     re.compile(r"(?<!\d)\d{44,50}(?!\d)"),
     "Chave de acesso de documento fiscal (NFS-e/NF-e). Consultavel em portal "
     "publico: devolve CNPJ, razao social e valor reais. Remover."),

    # Nenhuma lista de literais cobre "nome de pessoa que voce nunca cadastrou".
    # Este check nao tenta reconhecer antroponimo em geral (impossivel por
    # regex) — pega a forma que quase sempre indica pessoa real num documento
    # tecnico: titulo + nome proprio composto.
    ("pessoa-com-titulo", "ALTO",
     re.compile(r"\b(?:Dr|Dra|Sr|Sra|Prof|Profa)\.?\s+"
                r"(?!CLIENTE|PESSOA|EXEMPLO|Fulano|Beltrano|\$\{)"
                r"[A-ZÀ-Ú][a-zà-ú]{2,}(?:\s+[A-ZÀ-Ú][a-zà-ú]{2,})+"),
     "Titulo + nome proprio composto = pessoa real. Substituir por ${PESSOA}."),

    ("registro-profissional", "ALTO",
     re.compile(r"\b(?:CRO|CRM|OAB|CRC|CREA|COREN|CRP|CRN)[-/ ]?[A-Z]{2}\s?\d{3,}\b"),
     "Registro profissional. Identifica a pessoa em conselho publico. Remover."),

    ("cep", "ALTO",
     re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)"),
     "CEP. Combinado com ramo de atividade identifica o endereco. Remover."),

    ("logradouro", "MEDIO",
     re.compile(r"\b(?:Rua|Av\.?|Avenida|Alameda|Travessa|Rodovia)\s+[A-ZÀ-Ú][\wÀ-ú.]+"
                r"(?:\s+[A-ZÀ-Ú][\wÀ-ú.]+)*,?\s*n?º?\s*\d{1,5}\b"),
     "Endereco com numero. Verificar se e de cliente real."),

    # === IDENTIFICADORES OPACOS E URLs QUE RESOLVEM IDENTIDADE ===
    # Auditoria Fable 5.1: um ID de planilha Google era PUBLICO — curl sem login
    # devolvia o dominio real do autor; o placeholder do dominio virou decoracao.
    # Um hex de 32 (grupo de avatar) e uma URL de post (devolve o handle) idem.
    # Base62 de 40-50 com maiuscula E minuscula E digito e no maximo 2 hifens.
    # Sem essas exigencias, todo slug de nota ("sess-o-evolu-o-04-mai-2026-...")
    # casava: 457 falsos positivos numa rodada. Slug e minusculo e cheio de hifen;
    # ID do Google e caixa mista com hifen raro.
    # Tambem no maximo 2 underscores: nome de arquivo de transcricao
    # ("FS-KLT_-_Modulo_1_-_Aula_3_...") tem dezenas e nao e ID de nada.
    ("google-doc-id", "ALTO",
     re.compile(r"(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]{40,50}(?![A-Za-z0-9_-]))"
                r"(?=[^\s]*[A-Z])(?=[^\s]*[a-z])(?=[^\s]*\d)"
                r"(?![A-Za-z0-9-]*_[A-Za-z0-9-]*_[A-Za-z0-9-]*_)"
                r"(?:[A-Za-z0-9_]*-?){0,3}[A-Za-z0-9_]{20,}[A-Za-z0-9_-]*(?![A-Za-z0-9_-])"),
     "ID de Google Sheets/Docs/Drive (base62 longo). Pode ser publico e resolver identidade. Remover."),

    # Nome proprio escrito como REGEX ("CLIENTE_EXEMPLO_2", "Sa[úu]de[ -]?360"):
    # as variantes da regua nao geram essa forma, e o gate le a linha como
    # codigo inocente. Achado da auditoria Fable 5.1.
    ("nome-em-forma-de-regex", "ALTO",
     re.compile(r"[A-Z][a-zà-ú]{2,}\[[\\\s\-\s ]{2,}\]\??[A-Z0-9][A-Za-z0-9]{1,}"
                r"|[A-Z][a-z]\[[a-zà-ú]{2,4}\][a-z]{2,}"),
     "Nome proprio em forma de regex. O padrao entrega o nome tanto quanto o literal."),

    # Gist publico (gist.github.com/<autor>/<hex>) e isento via ALLOW_LINE:
    # o autor esta na URL e um gist famoso nao identifica ninguem alem dele.
    # (Python nao aceita lookbehind de largura variavel — por isso nao e aqui.)
    ("hex-servico-32", "ALTO",
     re.compile(r"(?<![A-Za-z0-9])[0-9a-f]{32}(?![A-Za-z0-9])"),
     "Hex de 32 (UUID sem hifen, grupo/asset de servico). Parametrizar."),

    ("video-id-plataforma", "MEDIO",
     re.compile(r"vimeo\.com/\d{8,10}\b|youtu(?:\.be/|be\.com/watch\?v=)[A-Za-z0-9_-]{11}\b"),
     "ID de video em plataforma. Se for de curso pago de terceiro, verificar direito autoral."),

    # So URL que resolve para UMA pessoa/conta: post, reel, perfil. Doc publica
    # (developers.facebook.com/tools, /business/help) nao identifica ninguem.
    ("url-post-social", "ALTO",
     re.compile(r"instagram\.com/(?:p|reel|stories)/[A-Za-z0-9_-]{5,}"
                r"|instagram\.com/(?!p/|reel/|explore|accounts|developer)[a-z0-9_.]{3,30}/?(?![a-z0-9_./-])"
                r"|(?<![a-z.])facebook\.com/(?!tools|docs|business|help|policies|ads/|login)[A-Za-z0-9.]{5,}"
                r"|tiktok\.com/@[A-Za-z0-9_.]{3,}"
                r"|linkedin\.com/in/[A-Za-z0-9-]{5,}"),
     "URL de perfil/post: o post devolve o handle real. Substituir por placeholder."),

    ("referencia-cofre-nomeada", "ALTO",
     re.compile(r"op://[^\s'\"]+|1Password[^\n]{0,40}(?:item|sob)\s*[\"'][^\"']+[\"']"),
     "Referencia nomeada a item de cofre: revela a estrutura do 1Password do autor."),

    ("usuario-db-em-connstring", "MEDIO",
     re.compile(r"[a-z]+://(?!postgres:postgres@|user:|usuario:|\$)[a-z][a-z0-9_]{3,}:\$?[A-Z_{}$]+@", re.I),
     "Connection string com USUARIO real (senha parametrizada nao esconde o usuario)."),

    ("titulo-por-extenso", "ALTO",
     re.compile(r"\b(?:Doutor|Doutora|Professor|Professora|Senhor|Senhora)\s+"
                r"(?!CLIENTE|PESSOA|EXEMPLO|Fulano|\$\{)[A-ZÀ-Ú][a-zà-ú]{2,}\b"),
     "Titulo por extenso + nome = pessoa real. Substituir por ${PESSOA}."),

    ("hostname-sandbox-interno", "MEDIO",
     re.compile(r"@[a-z0-9.-]+\.(?:local|internal|lan|corp)\b"),
     "Hostname interno em e-mail/endereco. Revela nomenclatura de rede."),

    # === DOCUMENTOS E DADOS PESSOAIS ===
    ("cpf-formatado", "CRITICO",
     re.compile(r"\b(?!000\.000\.000)\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
     "CPF. Remover (dado pessoal, LGPD)."),

    ("cnpj-formatado", "ALTO",
     re.compile(r"\b(?!00\.000\.000)\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
     "CNPJ. Substituir por 00.000.000/0000-00."),

    ("telefone-br", "ALTO",
     re.compile(r"\b55\d{2}9?\d{8}\b|\((?!00\))\d{2}\)\s?9?\d{4}[-\s]?\d{4}"),
     "Telefone. Substituir por (00) 00000-0000."),

    ("whatsapp-jid", "ALTO",
     re.compile(r"\b\d{10,13}@s\.whatsapp\.net\b"),
     "JID de WhatsApp. Remover."),

    ("email-real", "ALTO",
     re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.|exemplo\.|test\.|"
                r"seudominio|meudominio|dominio\.|localhost|s\.whatsapp)"
                r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "E-mail real. Substituir por usuario@example.com."),

    # === PORTABILIDADE (nao e segredo, mas quebra na maquina do outro) ===
    ("python-framework-macos", "MEDIO",
     re.compile(r"/Library/Frameworks/Python\.framework"),
     "Caminho de Python do macOS. Usar 'python3' do PATH."),

    ("valor-financeiro", "MEDIO",
     re.compile(r"R\$\s?\d{1,3}(?:\.\d{3}){1,}(?:,\d{2})?"),
     "Valor financeiro real. Generalizar se for dado de negocio."),
]


# ---------------------------------------------------------------------------
# CAMADA 2 — identificadores especificos, carregados de arquivo local.
# ---------------------------------------------------------------------------
def _carrega_identificadores_locais():
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "identificadores.local.json")
    if not os.path.exists(caminho):
        return []
    try:
        with open(caminho, encoding="utf-8") as fh:
            dados = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []

    severidade = {
        "senhas_conhecidas": "CRITICO", "hosts": "ALTO", "hostnames": "ALTO",
        "usuarios": "ALTO", "dominios": "ALTO", "emails": "ALTO",
        "handles": "MEDIO", "nome_legal": "ALTO", "telefones": "ALTO",
        "clientes": "ALTO", "pessoas": "ALTO", "ids_plataforma": "ALTO",
        "outros": "ALTO",
    }
    def _variantes(termo):
        """Acento, slug e forma colada — o mesmo nome aparece de varios jeitos."""
        import unicodedata
        formas = {termo}
        formas.add("".join(c for c in unicodedata.normalize("NFD", termo)
                           if unicodedata.category(c) != "Mn"))
        for base in list(formas):
            if " " in base:
                formas.add(base.replace(" ", "-"))
                formas.add(base.replace(" ", "_"))
                formas.add(base.replace(" ", ""))
        return {f for f in formas if len(f) >= 3}

    extras = []
    for chave, sev in severidade.items():
        termos = [t for t in dados.get(chave, []) if isinstance(t, str) and t.strip()]
        if not termos:
            continue
        expandidos = set()
        for t in termos:
            expandidos |= _variantes(t)
        alternativas = "|".join(re.escape(t) for t in sorted(expandidos, key=len, reverse=True))
        extras.append((
            f"local:{chave}", sev,
            re.compile(rf"(?<![A-Za-z0-9])(?:{alternativas})(?![A-Za-z0-9])", re.I),
            f"Identificador privado ({chave}) — declarado em identificadores.local.json.",
        ))
    return extras


LOCAIS = _carrega_identificadores_locais()
CHECKS.extend(LOCAIS)

# ---------------------------------------------------------------------------
# ALLOW — trechos que provam, por si, a ausencia do segredo.
#
# TRES REGRAS, cada uma paga com um vazamento real:
#
# 1. NUNCA isenta identificador privado (local:*). Um nome de cliente e um
#    nome de cliente, nao importa quantos ${PLACEHOLDER} haja na mesma linha.
#    A isencao vale so para os checks GENERICOS (uma senha de exemplo, uma
#    connection string com $VAR no lugar do valor).
#
# 2. Case-sensitive. Com re.I, "<[A-Z_]+>" casava "<modulo>" e "EXEMPLO"
#    casava "exemplo" — qualquer prosa comum virava salvo-conduto.
#
# 3. Em .jsonl a isencao e por REGISTRO, nao por linha — e um registro tem
#    dezenas de tokens. Um "<slug>" no meio de uma heuristica isentava o
#    registro inteiro, inclusive a sigla real do cliente na mesma frase.
#    Por isso: em .jsonl/.json/.csv, ALLOW nao se aplica.
#
# Manter ESTREITO: um ALLOW amplo (ex.: a palavra "pattern") mascararia um
# segredo real na mesma linha.
# ---------------------------------------------------------------------------
ALLOW_LINE = re.compile(
    r"(\$\{[A-Z_]+\}|<[A-Z_]+>|SENHA_EXEMPLO|PLACEHOLDER|act_XXX|"
    r"your[_-]|seu[_-]|example\.com|CHANGE_?ME|changeme|xxxx|"
    # placeholder em colchetes: [PASSWORD], [PROJECT_REF]
    r"\[[A-Z_]{3,}\]|"
    # a linha aponta para o cofre em vez de conter o segredo
    r"nunca\s+texto\s+plano|ver\s+cofre|"
    # variavel de ambiente no lugar do valor
    r"os\.environ|process\.env|PGPASSWORD=\$|\$[A-Z][A-Z0-9_]{4,}|"
    # documento ja zerado
    r"\b0{2,3}[.\d/-]{8,}0{2}\b|"
    # glob de extensao numa lista do que NAO commitar
    r"\*\.(?:p12|pfx|jks|pem|key)\b|"
    # exemplo didatico em checklist de seguranca
    r"sk-live-abc|abc123xyz|sk-your-key|"
    # credencial default publica de servico local
    r"postgres:postgres@localhost|:54322|"
    # gist publico: o hex e o id do gist, o autor esta na propria URL
    r"gist\.github\.com/|"
    # fixture de teste obvia
    r"password: *'test|'test123'|\"test123\")")

# Extensoes onde uma "linha" e um registro inteiro: ALLOW nao se aplica.
NO_ALLOW_EXT = {".jsonl", ".json", ".csv"}


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn == ".env.example" or os.path.splitext(fn)[1] in TEXT_EXT:
                # 2o valor: True = ferramenta de deteccao, so checks local:*
                yield os.path.join(dirpath, fn), fn in SKIP_FILES


def scan(root):
    findings = []

    # ---------------------------------------------------------------------
    # NOMES DE ARQUIVO E DIRETORIO.
    # O docstring antigo dizia "escaneia o CONTEUDO, nao apenas os nomes" —
    # e por isso nome de arquivo nunca foi verificado por nada. Dois arquivos
    # entregavam o cliente so pelo nome, com o conteudo todo sanitizado.
    # O caminho tambem e publicado.
    # ---------------------------------------------------------------------
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for nome in list(dirnames) + filenames:
            if nome in SKIP_FILES:
                continue
            legivel = re.sub(r"[-_./]", " ", nome)
            for cat, sev, rx, fix in CHECKS:
                # so os checks de identidade fazem sentido em nome de arquivo
                if not (cat.startswith("local:") or cat in
                        ("email-real", "telefone-br", "cpf-formatado", "cep")):
                    continue
                if rx.search(nome) or rx.search(legivel):
                    findings.append({
                        "file": os.path.relpath(os.path.join(dirpath, nome), root),
                        "line": 0, "category": f"nome-arquivo:{cat}",
                        "severity": sev,
                        "fix": f"O NOME do arquivo/diretorio identifica ({cat}). "
                               "Renomear — o caminho e publicado junto do conteudo.",
                    })
                    break

    # ---------------------------------------------------------------------
    # ARQUIVOS FORA DO ESCOPO — reportados, nao ignorados em silencio.
    # A lista TEXT_EXT e o escopo do gate. Um arquivo com extensao inventada
    # ("*.py.superseded-2026") contendo senha + IP + cliente foi declarado
    # LIMPO porque o gate nem o abriu. "Nao li" precisa aparecer no relatorio.
    # ---------------------------------------------------------------------
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if fn == ".env.example" or ext in TEXT_EXT or fn in SKIP_FILES:
                continue
            if fn.startswith(".git") or ext in {".ttf", ".otf", ".woff", ".woff2",
                                                 ".png", ".jpg", ".jpeg", ".gif",
                                                 ".ico", ".pdf", ".lock", ".highwatermark"}:
                continue  # binario ou estado conhecido: fora do texto por natureza
            findings.append({
                "file": os.path.relpath(os.path.join(dirpath, fn), root),
                "line": 0, "category": "arquivo-nao-lido", "severity": "MEDIO",
                "fix": f"Extensao '{ext or '(nenhuma)'}' fora do TEXT_EXT — o gate NAO leu. "
                       "Audite a mao ou adicione a extensao.",
            })

    for path, so_locais in iter_files(root):
        rel = os.path.relpath(path, root)

        # Personas de squad encarnam FIGURAS PUBLICAS (autores, palestrantes)
        # citadas como metodologia — Hormozi, Ogilvy, Park Howell. O nome ali
        # e referencia intelectual, nao dado privado. Sem esta excecao o check
        # de antroponimo acusa o catalogo inteiro e vira ruido.
        eh_persona = "/squads/" in rel.replace(os.sep, "/") and "/agents/" in rel.replace(os.sep, "/")

        # Symlink e caso proprio: o conteudo sensivel pode estar no ALVO do
        # link, nao no texto. Um link absoluto carrega o caminho (e o nome de
        # usuario) de quem o criou, e o gate nunca leria isso abrindo o arquivo.
        if os.path.islink(path):
            alvo = os.readlink(path)
            if os.path.isabs(alvo):
                findings.append({
                    "file": rel, "line": 0, "category": "symlink-absoluto",
                    "severity": "ALTO",
                    "fix": f"Symlink aponta para caminho absoluto ({alvo}) — "
                           "vaza o path de quem criou e quebra em outra maquina. "
                           "Recriar relativo.",
                })
            if not os.path.exists(path):
                findings.append({
                    "file": rel, "line": 0, "category": "symlink-quebrado",
                    "severity": "MEDIO",
                    "fix": f"Symlink aponta para alvo inexistente ({alvo}).",
                })
                continue

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                ext = os.path.splitext(path)[1]
                for lineno, line in enumerate(fh, 1):
                    # ALLOW so vale para checks genericos, e nunca em formato
                    # onde a linha e um registro inteiro (ver comentario acima)
                    isenta_genericos = (ext not in NO_ALLOW_EXT
                                        and bool(ALLOW_LINE.search(line)))
                    for cat, sev, rx, fix in CHECKS:
                        if isenta_genericos and not cat.startswith("local:"):
                            continue
                        # ferramenta de deteccao: so cobramos literal privado.
                        # Excecao: o proprio arquivo de identificadores E a
                        # lista de literais (e esta no .gitignore) — acusa-lo
                        # seria ruido de 100% das linhas.
                        if "identificadores.local" in rel:
                            continue
                        if so_locais and not cat.startswith("local:"):
                            continue
                        if eh_persona and cat in ("pessoa-com-titulo", "titulo-por-extenso"):
                            continue
                        if rx.search(line):
                            findings.append({
                                "file": rel, "line": lineno, "category": cat,
                                "severity": sev, "fix": fix,
                            })
        except (OSError, UnicodeDecodeError) as e:
            # NAO engolir: "nao consegui abrir" e diferente de "esta limpo".
            # Silenciar aqui faz o gate reportar LIMPO para arquivo que nem leu
            # — foi assim que um symlink absoluto com o nome do autor passou.
            findings.append({
                "file": rel, "line": 0, "category": "arquivo-ilegivel",
                "severity": "MEDIO",
                "fix": f"Gate NAO conseguiu ler este arquivo ({type(e).__name__}) "
                       "— audite a mao. Ilegivel nao e o mesmo que limpo.",
            })
    return findings


def main():
    if len(sys.argv) < 2:
        print("uso: validate-publish.py <dir> [--json]", file=sys.stderr)
        sys.exit(2)
    root = sys.argv[1]
    as_json = "--json" in sys.argv
    findings = scan(root)
    blocking = [f for f in findings if f["severity"] in ("CRITICO", "ALTO")]

    if as_json:
        print(json.dumps({"findings": findings, "blocking": len(blocking)},
                         ensure_ascii=False, indent=2))
        sys.exit(1 if blocking else 0)

    if not LOCAIS:
        print("AVISO: identificadores.local.json ausente — so os padroes")
        print("       genericos estao ativos. Copie o .example e preencha")
        print("       com os seus dados para uma cobertura completa.\n")

    if not findings:
        print(f"LIMPO — nenhuma violacao em {root}")
    else:
        by_cat = {}
        for f in findings:
            by_cat.setdefault((f["severity"], f["category"]), []).append(f)
        order = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2}
        print(f"VIOLACOES em {root}:\n")
        for (sev, cat), items in sorted(by_cat.items(), key=lambda x: order[x[0][0]]):
            print(f"[{sev}] {cat} — {len(items)} ocorrencia(s) — {items[0]['fix']}")
            for it in items[:5]:
                print(f"    {it['file']}:{it['line']}")
            if len(items) > 5:
                print(f"    ... +{len(items) - 5} mais")
            print()
        print(f"TOTAL: {len(findings)} violacoes ({len(blocking)} bloqueantes)")

    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
