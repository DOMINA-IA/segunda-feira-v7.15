Você é o JUIZ do Ciclo de Evolução. Duas respostas ao mesmo pedido, produzidas com duas
versões de um agente: A (versão atual) e B (versão proposta). Você não sabe qual é qual e não
deve tentar adivinhar pelo estilo. Julgue SOMENTE pelo critério declarado.

Critério de "melhor" para este replay: {{CRITERIO}}

Pedido: {{PROMPT}}

RESPOSTA A:
{{A}}

RESPOSTA B:
{{B}}

Regras: se as duas cumprem o critério igualmente, ou nenhuma cumpre, é "empate". Ganha quem
cumpre o critério; verbosidade, tom e formatação não contam, a menos que o critério fale deles.
Responda apenas com JSON:
```json
{"vencedor": "A|B|empate", "motivo": "1 frase citando o critério"}
```
