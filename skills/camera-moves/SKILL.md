---
name: camera-moves
description: "Monta prompts de vídeo IA com movimento de câmera cinematográfico (tracking, orbit, push-in, handheld, crane) pela fórmula de 5 blocos. Use ao gerar vídeo com Kling/VO3/Runway, ou quando o personagem se deformar. NOT for: edição de vídeo já gravado."
axis: ops
harnesses:
  claude-code: full
  codex: full
  cursor: full
provider-fallback:
  - anthropic/claude-sonnet-5
  - google/gemini-3.5-flash
---

# /camera-moves — Movimento de Câmera para Vídeo IA

## Princípio

O que separa vídeo IA amador de cinematográfico quase nunca é o modelo — é o **movimento de
câmera**. E o erro mais caro é empilhar movimento com ação complexa: o personagem derrete.

**Regra de ouro:** "Se o movimento de câmera é complexo, a ação do personagem tem que ser simples."

> Órbita + caminhada lenta = bom.
> Órbita + corrida + salto + troca de roupa = o modelo perde a identidade do personagem.

**Orçamento de movimento:** você tem UMA unidade de complexidade por tomada. Gaste na câmera **ou**
na ação, nunca nas duas. Comece com um movimento limpo, acerte, só então adicione camada.

> Origem: INEMA.VISION, 20-Ago-2026 — guia de movimentos cinematográficos para personagem consistente.

## A fórmula de 5 blocos

Todo prompt de vídeo com personagem segue esta ordem. Trocar a ordem degrada o resultado:

| # | Bloco | O que define |
|---|---|---|
| 1 | **Referência** | `@Image1 define a identidade exata do personagem` — rosto, proporções, roupa, cabelo, acessórios |
| 2 | **Cena** | Onde acontece + **o que NÃO deve aparecer** (a exclusão importa tanto quanto a inclusão) |
| 3 | **Ação** | O que o personagem faz — mantenha simples se a câmera se move |
| 4 | **Iluminação** | Hora do dia, direção da luz, temperatura, reflexos |
| 5 | **Movimento de câmera** | Um movimento único e contínuo, com início e fim declarados |

A exclusão explícita ("nenhuma outra pessoa, construção, barco ou objeto que cause distração")
é o que impede o modelo de povoar o fundo com ruído.

## Os 5 movimentos

| Movimento | O que faz | Quando usar |
|---|---|---|
| **Tracking Shot** | Câmera paralela ao personagem, mesma velocidade, distância constante | Caminhada, apresentação de produto em movimento, abertura de Reel |
| **Orbit Shot** | Arco ao redor do personagem (use **120°**, não 360°) | Revelação, "olha quem é", transição de bloco |
| **Slow Push In** | Aproximação contínua até close do rosto | Momento de tensão, virada de argumento, antes da oferta |
| **Handheld** | Oscilação vertical sutil dos passos + correções orgânicas | Autenticidade, depoimento, "sem produção" |
| **Crane Down** | Desce de plano alto e ligeiramente à frente | Estabelecer contexto, fechamento, escala |

## Templates prontos

### Tracking Shot
```
Crie um novo vídeo cinematográfico em [CENÁRIO]. @Image1 define a identidade exata do personagem,
sua aparência facial, proporções corporais, roupas, penteado e acessórios.

O personagem caminha naturalmente por [DESCRIÇÃO DO LOCAL]. Nenhuma outra pessoa, construção ou
objeto que cause distração deve estar visível. Uma leve brisa movimenta suavemente o cabelo e as
roupas.

A luz quente do fim da tarde, durante a golden hour, vem lateralmente, criando reflexos suaves,
tons naturais de pele e sombras delicadas.

Plano lateral de corpo inteiro com tracking. A câmera se move suavemente em paralelo ao personagem,
na mesma velocidade, mantendo-o centralizado e preservando distância constante durante toda a tomada.
Passos naturais e relaxados, movimento sutil dos braços.
```

### Orbit Shot (120°)
```
[Blocos 1-4 iguais]

Comece em ângulo frontal de três quartos, em plano médio de corpo inteiro. Enquanto o personagem
continua caminhando para frente, a câmera executa uma única órbita suave de 120 graus e termina em
ângulo lateral de três quartos. Mantenha o personagem centralizado e em foco durante todo o arco.
```

### Slow Push In
```
[Blocos 1-4 iguais — personagem PARADO]

Comece com plano médio fechado estável e execute um único push-in lento e contínuo em direção a um
close-up do rosto. O personagem permanece calmo, com respiração sutil e uma piscada natural.
Mantenha os olhos em foco nítido enquanto o fundo perde nitidez gradualmente.
```

### Handheld
```
[Blocos 1-4 iguais]

A câmera acompanha o personagem a partir de ângulo traseiro próximo de três quartos, na mesma
velocidade da caminhada, mantendo distância quase constante. Use movimento handheld contido: leve
oscilação vertical causada pelos passos do operador e pequenas correções orgânicas de enquadramento.
Sem tremor exagerado.
```

### Crane Down
```
[Blocos 1-4 iguais]

Comece com plano geral em ângulo alto, mostrando o personagem como pequena figura dentro da paisagem.
Execute uma única descida suave de grua, movendo-se gradualmente para baixo e ligeiramente para
frente em direção ao personagem. Termine em ângulo médio-aberto elevado.
```

## Uso no funil DOMINA.IA

| Peça | Movimento | Por quê |
|---|---|---|
| Hook de Reel (0-3s) | Push In rápido ou Handheld | Prende o olho antes do scroll |
| Corpo de VSL | Tracking | Sensação de progresso, acompanha a narrativa |
| Revelação da oferta | Orbit 120° | Marca a virada sem cortar |
| Fechamento / CTA | Crane Down | Dá escala e encerra |
| Depoimento | Handheld | Autenticidade > produção |

## Anti-patterns

Dois movimentos na mesma tomada · órbita de 360° (o modelo perde a identidade na volta) ·
movimento complexo + ação complexa · esquecer o bloco de exclusão (fundo vira ruído) ·
mudar o cenário inteiro a cada teste — **fixe personagem e cena, varie só a câmera** para
descobrir o que o movimento faz.
