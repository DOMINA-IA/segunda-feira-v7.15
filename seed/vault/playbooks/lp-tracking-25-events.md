---
id: lp-tracking-25-events
title: LP Tracking Avançado — 25 Eventos Customizados Meta Ads
type: playbook
domain:
- traffic
- cro
agents:
- traffic
- cro-specialist
- growth-hacker
tags:
- meta-ads
- tracking
- pixel
- eventos
- lp
- retargeting
- lookalike
status: active
source: Parceiro INEMA (Abr/2026)
created: '2026-04-13'
last_verified: '2026-04-13'
decay_rate: 0.02
links:
- target: heuristic-dev-lp-de-evento-gratuito-captura-precisa-de-copy-enxuta-cta
  type: auto-linked
- target: bavi-pit-de-vendas-13-passos-anthony-nichols
  type: auto-linked
- target: bavi-12-pilares-de-campanha-anthony-nichols
  type: auto-linked
- to: meta-ads-operations
  type: supports
- target: evento-7-cidades-offer-audit
  type: related
axis: ops
---

# LP Tracking Avançado — 25 Eventos Customizados Meta Ads

> Fonte: Parceiro INEMA (Abr/2026)
> Técnica de rastreamento avançado de landing page que mapeia comportamento do lead em granularidade alta.
> Objetivo: fornecer ao algoritmo da Meta 8x mais sinal para aprendizado, gerando audiências segmentadas por intenção.

---

## Princípio Central

A maioria dos anunciantes dispara apenas 3 eventos standard: PageView, Lead, ViewContent. Isso gera uma única audiência genérica e pouco sinal para o algoritmo aprender quem converte.

Com 25 eventos customizados mapeando comportamento real na LP — scroll, tempo, seções vistas, interações — o algoritmo da Meta recebe sinal suficiente para identificar padrões de intenção antes da conversão. O resultado prático: CPL menor, lookalikes mais qualificados, retargeting segmentado por objeção específica.

---

## Eventos de Engajamento

Estes eventos medem o quanto o lead se aprofundou na leitura da LP.

| Evento | Gatilho | Sinal para o algoritmo |
|--------|---------|------------------------|
| ScrollDepth_25 | Lead rolou 25% da página | Baseline de engajamento mínimo |
| ScrollDepth_50 | Lead rolou 50% da página | Leu pelo menos metade do conteúdo |
| ScrollDepth_75 | Lead rolou 75% da página | Alto engajamento — provável interesse |
| ScrollDepth_90 | Lead rolou 90% da página | Leu quase tudo — intenção muito alta |
| TimeOnPage_30s | 30 segundos na página | Não saiu imediatamente |
| TimeOnPage_60s | 60 segundos na página | Engajamento real, não bounce |
| TimeOnPage_120s | 2 minutos na página | Leitura ativa — alta qualidade |
| TimeOnPage_180s | 3 minutos na página | Consideração profunda — melhor sinal para lookalike |

**Implementação:** Usar `performance.now()` para TimeOnPage com `setTimeout` em cascata. Não usar visibilityState isolado — o lead pode ficar com aba aberta sem ler.

---

## Eventos de Interesse por Seção

Estes eventos identificam qual parte da LP o lead consumiu, revelando sua objeção ou motivação dominante.

| Evento | Seção correspondente | Insight comportamental |
|--------|---------------------|------------------------|
| SectionView_Pricing | Seção de preço | Intent forte — avalia viabilidade financeira |
| SectionView_Depoimentos | Seção de depoimentos | Busca prova social — objeção de credibilidade |
| SectionView_Programacao | Seção de conteúdo/grade | Interesse no que vai aprender — objeção de fit |
| SectionView_Mentora | Seção da mentora/about | Verificando autoridade — objeção de autoridade |
| SectionView_Garantia | Seção de garantia | Objeção financeira ou risco — precisa de segurança |

**Implementação:** Usar `IntersectionObserver` com threshold de 0.5 (50% da seção visível). Não usar scroll cego com offsetTop — o IntersectionObserver é mais preciso e performático.

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      fbq('trackCustom', 'SectionView_Pricing');
      observer.unobserve(entry.target); // dispara apenas uma vez
    }
  });
}, { threshold: 0.5 });

observer.observe(document.querySelector('#pricing'));
```

---

## Eventos de Micro-Conversão

Estes eventos mapeiam os passos intermediários do funil dentro da LP, antes do Lead final.

| Evento custom | Evento standard disparado junto | Significado |
|--------------|--------------------------------|-------------|
| PopupOpen | AddToCart | Abriu o formulário de captação — demonstrou intenção de agir |
| FormStart | InitiateCheckout | Começou a digitar no form — está a 5% da conversão |
| WhatsAppClick | Contact | Clicou no botão de suporte pelo WhatsApp |

**Lógica de duplo disparo:** Eventos standard (AddToCart, InitiateCheckout, Contact) disparam junto com os custom para aproveitar o histórico de otimização da Meta para esses eventos.

```javascript
// Popup aberto
function onPopupOpen() {
  fbq('trackCustom', 'PopupOpen');
  fbq('track', 'AddToCart');
}

// Usuário começou a digitar no campo nome ou email
function onFormStart() {
  fbq('trackCustom', 'FormStart');
  fbq('track', 'InitiateCheckout');
}
```

---

## Eventos de Inteligência

Estes eventos capturam sinais de comportamento que revelam objeções específicas ou sinais de abandono.

| Evento | Gatilho | Dado capturado |
|--------|---------|---------------|
| FAQClick | Lead clicou em uma pergunta do FAQ | Texto da pergunta clicada — mapeia objeção real |
| ExitIntent | Mouse se move para fora da área da página (barra de abas) | Sinal de abandono iminente |

**FAQClick — captura de texto da objeção:**

```javascript
document.querySelectorAll('.faq-question').forEach(el => {
  el.addEventListener('click', () => {
    fbq('trackCustom', 'FAQClick', {
      question_text: el.textContent.trim().substring(0, 100)
    });
  });
});
```

O parâmetro `question_text` fica disponível nos eventos do Gerenciador de Eventos da Meta e pode ser usado para entender quais objeções são mais frequentes.

**ExitIntent:**

```javascript
document.addEventListener('mouseleave', (e) => {
  if (e.clientY <= 0) {
    fbq('trackCustom', 'ExitIntent');
  }
}, { once: true }); // dispara apenas uma vez por sessão
```

---

## Uso Estratégico — Audiências de Retargeting por Objeção

### Mapa de Audiências

| Audiência | Evento-base | Estratégia de retargeting |
|-----------|------------|--------------------------|
| Engajamento Alto | ScrollDepth_75 ou ScrollDepth_90 | Remarketing com depoimento em vídeo ou urgência de prazo |
| Tráfego Qualidade | TimeOnPage_120s ou TimeOnPage_180s | Lookalike 1% — alta qualidade, melhor que lookalike de PageView |
| Objeção Preço | SectionView_Pricing sem Lead | Ad com parcelamento, bônus ou comparação de valor |
| Objeção Social | SectionView_Depoimentos sem Lead | Ad com mais depoimentos em vídeo — preferir casos similares ao lead |
| Objeção Autoridade | SectionView_Mentora sem Lead | Ad com vídeo da mentora apresentando resultado de aluno |
| Objeção Conteúdo | SectionView_Programacao sem Lead | Ad detalhando módulo específico ou transformação do conteúdo |
| Objeção Risco | SectionView_Garantia sem Lead | Ad reenfatizando garantia — zero risco, testou e aprovou |
| Abandono Form | FormStart sem Lead | Recovery agressivo — estão a 5% da conversão |
| Abandono Popup | PopupOpen sem FormStart | Recovery leve — abriram mas não digitaram |
| Suporte | WhatsAppClick | Campanha Contact + acionar atendimento humano para fechar |
| Exit | ExitIntent | Retargeting com urgência ou oferta de desconto por tempo limitado |

### Configuração no Gerenciador de Públicos

Todas as audiências acima são criadas em Gerenciador de Públicos > Público Personalizado > Site > Evento específico. Janela de retenção recomendada:

- Eventos de engajamento (Scroll, Time): 30 dias
- Eventos de seção (SectionView): 14 dias
- Eventos de micro-conversão (PopupOpen, FormStart): 7 dias — urgência maior
- ExitIntent: 3 dias — quanto mais rápido o retargeting, melhor

---

## Impacto vs Tracking Padrão

| Dimensão | Antes (3 eventos) | Agora (25 eventos) |
|----------|------------------|--------------------|
| Audiências de retargeting | 1 genérica (visitantes) | 6+ segmentadas por intenção |
| Sinal para algoritmo | PageView, Lead, ViewContent | 25 eventos com gradação de intent |
| Qualidade do lookalike | Lookalike de PageView (qualidade média) | Lookalike de TimeOnPage_120s+ (qualidade alta) |
| Diagnóstico de objeções | Nenhum | FAQ clicks + SectionView mapeiam objeção dominante |
| CPL tendência | Linha de base | Queda esperada: algoritmo tem 8x mais sinal para aprender |

---

## Checklist de Implementação

- [ ] Instalar IntersectionObserver para cada seção mapeada (SectionView_*)
- [ ] Implementar contadores de TimeOnPage com setTimeout em cascata
- [ ] Implementar ScrollDepth com eventos de scroll throttled
- [ ] Disparar PopupOpen + AddToCart ao abrir form
- [ ] Disparar FormStart + InitiateCheckout ao detectar primeiro input
- [ ] Disparar WhatsAppClick + Contact em todos os CTAs de WhatsApp
- [ ] Implementar FAQClick com captura do texto da pergunta
- [ ] Implementar ExitIntent com listener mouseleave { once: true }
- [ ] Verificar no Gerenciador de Eventos da Meta que todos os 25 eventos estão chegando
- [ ] Criar as audiências de retargeting no Gerenciador de Públicos
- [ ] Criar lookalike baseado em TimeOnPage_120s+ após acumular 100+ eventos

---

## Notas Operacionais

- Cada evento custom dispara via `fbq('trackCustom', 'NomeDoEvento', {parametros_opcionais})`
- Eventos standard complementares disparam via `fbq('track', 'NomeStandard')`
- Testar implementação com o Meta Pixel Helper (extensão Chrome) — mostra eventos em tempo real
- Verificar no Gerenciador de Eventos (events.facebook.com) se os eventos estão chegando antes de criar audiências
- Para CAPI (Conversion API): os eventos custom também devem ser enviados pelo servidor para deduplicação — especialmente FormStart e Lead