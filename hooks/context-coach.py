#!/usr/bin/env python3
"""context-coach.py — Mede o contexto do pedido e faz o agente cobrar o que falta (UserPromptSubmit).

Operacionaliza a rule context-quality.md: pontua o prompt nos 5 elementos (objetivo, entrega,
onde, critério de pronto, restrições). Se for uma TAREFA com pontuação baixa, injeta no
contexto do agente a instrução de parar, perguntar as faltas concretas e avisar o usuário,
uma vez por sessão, que a forma de passar informação está limitando a entrega.

Não fala com o usuário diretamente: quem fala é o agente, com o tom da rule.
Nunca dispara em continuação curta ("segue", "faz o push"), pergunta ou conversa.
No máximo 2 disparos por sessão (estado em ~/.claude/.context-coach/<session>).
Falha silenciosa: qualquer erro → exit 0 sem saída.
"""
import json
import re
import sys
from pathlib import Path

STATE = Path.home() / ".claude" / ".context-coach"
MAX_POR_SESSAO = 2

VERBOS_TAREFA = r"\b(cria|criar|faz|fazer|monta|montar|implementa|implementar|gera|gerar|escreve|escrever|desenvolve|desenvolver|constr[óo]i|construir|refatora|refatorar|corrige|corrigir|ajusta|ajustar|melhora|melhorar|otimiza|otimizar|automatiza|automatizar|integra|integrar|configura|configurar|analisa|analisar|planeja|planejar|prepara|preparar|migra|migrar|adiciona|adicionar|remove|remover|muda|mudar|troca|trocar|deploy|publica|publicar|sobe|subir|lança|lançar|redesenha|redesenhar|traduz|traduzir|resume|resumir|audita|auditar|revisa|revisar|calcula|calcular|extrai|extrair|conecta|conectar|instala|instalar|documenta|documentar)\b"
CONTINUACAO = r"^\s*(ok|sim|isso|segue|continua|vai|pode|manda|faz o push|agora|próximo|proximo|beleza|show|perfeito|obrigado|valeu|e aí|e ai|de novo|repete|mais|outro|também|tambem)\b"
OBJETIVO = r"\b(para|pra|porque|objetivo|meta|resultado|reduzir|aumentar|converter|vender|economizar|evitar|ganhar|cliente|lead|receita|CPL|ROI|conversão|conversao)\b"
ENTREGA = r"\b(markdown|pdf|planilha|tabela|relatório|relatorio|arquivo|script|página|pagina|landing|api|endpoint|componente|função|funcao|classe|teste|post|carrossel|reel|email|sequência|sequencia|copy|headline|campanha|dashboard|formulário|formulario|\d+\s*(variações|variacoes|opções|opcoes|versões|versoes|linhas|posts|itens))\b"
ONDE = r"(~/|/[a-z0-9_./-]+/|\.(js|ts|py|md|html|css|json|sql|sh)\b|https?://|@[a-z-]+|\b(projeto|repo|repositório|repositorio|pasta|diretório|diretorio|rota|tabela|banco|campanha|conta|site|app)\s+[\w./-]+)"
CRITERIO = r"\b(deve|precisa|tem que|até|ate|no máximo|no maximo|no mínimo|no minimo|pronto quando|critério|criterio|passar|lint|teste|abaixo de|acima de|menos de|mais de|igual|exatamente|sem erro|funcionando|validar|aceite)\b"
RESTRICAO = r"\b(sem|não|nao|nunca|mantendo|mantém|mantem|só|somente|apenas|exceto|prazo|até (segunda|terça|quarta|quinta|sexta|sábado|domingo|amanhã|hoje)|orçamento|orcamento|R\$|tom|estilo|formato|limite)\b"


def pontuar(p: str):
    p = p.strip()
    pts = {
        "objetivo": bool(re.search(OBJETIVO, p, re.I)),
        "entrega": bool(re.search(ENTREGA, p, re.I)),
        "onde": bool(re.search(ONDE, p, re.I)),
        "critério de pronto": bool(re.search(CRITERIO, p, re.I)),
        "restrições": bool(re.search(RESTRICAO, p, re.I)),
    }
    return pts


def eh_tarefa(p: str) -> bool:
    p = p.strip()
    if len(p.split()) < 6:
        return False
    if re.search(CONTINUACAO, p, re.I) and len(p.split()) < 12:
        return False
    if p.endswith("?") and not re.search(VERBOS_TAREFA, p, re.I):
        return False
    return bool(re.search(VERBOS_TAREFA, p, re.I))


def main():
    import os
    if os.environ.get("SF_AUTOMATED"):
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    prompt = payload.get("prompt", "") if isinstance(payload, dict) else ""
    sid = payload.get("session_id", "sem-sessao") if isinstance(payload, dict) else "sem-sessao"
    if not prompt or not eh_tarefa(prompt):
        return 0
    pts = pontuar(prompt)
    score = sum(pts.values())
    if score > 2:
        return 0
    STATE.mkdir(exist_ok=True)
    st = STATE / sid
    n = int(st.read_text() or "0") if st.exists() else 0
    if n >= MAX_POR_SESSAO:
        return 0
    st.write_text(str(n + 1))
    faltas = [k for k, v in pts.items() if not v][:3]
    primeira = (n == 0)
    print(
        f"[context-coach] O pedido veio com {score}/5 elementos de contexto (faltou: {', '.join(faltas)}). "
        "Rule context-quality: antes de executar, verifique memória/CLAUDE.md/stories; se ainda faltar, "
        "faça no máximo 3 perguntas CONCRETAS sobre as faltas acima, ofereça a saída 'seguir com estas "
        "suposições: …', e NÃO entregue pela metade sem avisar. "
        + ("Diga também, uma vez, que a forma como o usuário passou a informação limita o nível da entrega e "
           "mostre o modelo de pedido: objetivo, o que sai, onde, como saber que ficou bom, o que não pode mudar."
           if primeira else "O aviso sobre a forma de pedir já foi dado nesta sessão; só as perguntas.")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
