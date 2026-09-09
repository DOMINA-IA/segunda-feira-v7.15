---
name: lp-companion-bot
description: "Injeta um robozinho animado em CSS puro (sem dependências), com balão de chat estilo WhatsApp que muda mensagem conforme o scroll, em qualquer landing page HTML. Use quando o CEO pedir para adicionar o companion robot em uma LP — elemento aprovado desde 06/Abr/2026."
user-invocable: true
allowed-tools:
  - Read
  - Edit
  - Grep
  - Glob
---

# LP Companion Bot — Robozinho CSS + Balão WhatsApp

## Contexto

Adiciona um companion robot fixo no canto inferior direito de qualquer LP. O robô é desenhado 100% em CSS (zero dependências externas), com olhos que piscam, antena com glow, boca expressiva e balão estilo WhatsApp que muda mensagem conforme o scroll.

**Aprovado pelo CEO em 06/Abr/2026.** Preferência confirmada: companion CSS pequeno > SVG grande no hero > iframe Sketchfab 3D.

---

## Execução

### Passo 1: Receber parâmetros
- Caminho do arquivo HTML
- (Opcional) Array de mensagens customizadas `{ at: percentScroll, msg: 'texto' }`
- Se não fornecido, usar mensagens padrão genéricas

### Passo 2: Injetar CSS

Adicionar ANTES do `</style>` ou como novo `<style>` antes do `</head>`:

```css
.companion{position:fixed;right:16px;bottom:16px;z-index:9999;display:flex;align-items:flex-end;gap:8px}
.comp-chat{max-width:200px;opacity:0;transform:translateY(10px) scale(.92);transition:all .4s cubic-bezier(.34,1.56,.64,1);pointer-events:auto}
.comp-chat.show{opacity:1;transform:translateY(0) scale(1)}
.comp-bubble{background:#1e1b4b;border:1px solid rgba(139,92,246,.35);border-radius:16px 16px 4px 16px;padding:10px 14px;font-size:.75rem;color:rgba(255,255,255,.92);line-height:1.5;box-shadow:0 4px 24px rgba(0,0,0,.5);position:relative}
.comp-bubble::after{content:'';position:absolute;bottom:0;right:-6px;width:0;height:0;border-left:8px solid #1e1b4b;border-bottom:8px solid transparent}
.comp-bubble-time{display:block;text-align:right;font-size:.58rem;color:rgba(139,92,246,.5);margin-top:4px}
.comp-bubble-tick{color:#06B6D4;margin-left:3px}
.comp-typing{display:inline-flex;gap:3px;padding:6px 12px;background:#1e1b4b;border:1px solid rgba(139,92,246,.25);border-radius:12px}
.comp-typing span{width:5px;height:5px;background:rgba(139,92,246,.5);border-radius:50%;animation:typing-dot 1.2s ease-in-out infinite}
.comp-typing span:nth-child(2){animation-delay:.2s}
.comp-typing span:nth-child(3){animation-delay:.4s}
@keyframes typing-dot{0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1.2)}}
.comp-bot{width:70px;flex-shrink:0;display:flex;flex-direction:column;align-items:center;animation:bot-float 3.5s ease-in-out infinite}
@keyframes bot-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.bot-head{width:50px;height:40px;background:linear-gradient(145deg,#1e1b4b,#312e81);border:2px solid rgba(139,92,246,.55);border-radius:14px;margin:0 auto 2px;position:relative;overflow:visible;box-shadow:0 0 18px rgba(139,92,246,.3)}
.bot-brows{position:absolute;top:5px;left:8px;right:8px;display:flex;justify-content:space-between}
.bot-brow{width:10px;height:2px;background:rgba(6,182,212,.6);border-radius:1px}
.bot-visor{position:absolute;top:10px;left:5px;right:5px;height:18px;background:rgba(6,182,212,.06);border-radius:7px;border:1px solid rgba(6,182,212,.2);display:flex;align-items:center;justify-content:center;gap:10px}
.bot-eye{width:9px;height:9px;background:radial-gradient(circle,#fff 25%,#06B6D4 65%,rgba(6,182,212,.3));border-radius:50%;position:relative;box-shadow:0 0 6px rgba(6,182,212,.6)}
.bot-eye-pupil{width:3.5px;height:3.5px;background:#fff;border-radius:50%;position:absolute;top:2.8px;left:2.8px}
.bot-eye.blink{animation:eye-blink .25s ease}
@keyframes eye-blink{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.1)}}
.bot-mouth{position:absolute;bottom:5px;left:50%;transform:translateX(-50%);width:14px;height:2px;background:rgba(6,182,212,.45);border-radius:1px;transition:all .35s cubic-bezier(.34,1.56,.64,1)}
.bot-mouth.smile{width:18px;height:7px;border-radius:0 0 9px 9px;background:rgba(6,182,212,.55)}
.bot-antenna{width:2px;height:9px;background:rgba(139,92,246,.4);margin:0 auto;position:relative}
.bot-antenna::after{content:'';position:absolute;top:-4px;left:50%;transform:translateX(-50%);width:6px;height:6px;background:#8B5CF6;border-radius:50%;animation:ant-glow 2s ease-in-out infinite}
@keyframes ant-glow{0%,100%{box-shadow:0 0 4px rgba(139,92,246,.4)}50%{box-shadow:0 0 12px rgba(139,92,246,1)}}
.bot-torso{width:36px;height:26px;background:linear-gradient(180deg,#1e1b4b,#0f0d24);border:1.5px solid rgba(139,92,246,.35);border-radius:5px 5px 8px 8px;margin:0 auto;position:relative}
.bot-core{position:absolute;top:7px;left:50%;transform:translateX(-50%);width:7px;height:7px;border-radius:50%;background:rgba(6,182,212,.12);border:1.5px solid rgba(6,182,212,.45);animation:core-glow 2.5s ease-in-out infinite}
@keyframes core-glow{0%,100%{box-shadow:0 0 4px rgba(6,182,212,.2)}50%{box-shadow:0 0 12px rgba(6,182,212,.7)}}
.bot-arms{position:absolute;top:2px;left:-5px;right:-5px;display:flex;justify-content:space-between}
.bot-arm{width:7px;height:20px;background:linear-gradient(180deg,rgba(139,92,246,.35),rgba(139,92,246,.15));border-radius:4px}
.bot-legs{display:flex;justify-content:center;gap:5px}
.bot-leg{width:7px;height:12px;background:linear-gradient(180deg,rgba(139,92,246,.25),rgba(139,92,246,.1));border-radius:3px 3px 4px 4px}
@media(max-width:640px){.companion{right:6px;bottom:6px;gap:4px}.comp-bot{width:55px}.bot-head{width:40px;height:32px}.bot-torso{width:28px;height:20px}.comp-chat{max-width:150px}.comp-bubble{font-size:.65rem;padding:7px 10px}}
```

### Passo 3: Injetar HTML

Adicionar ANTES do `</body>` ou antes do `<footer>`:

```html
<div class="companion" id="companion">
  <div class="comp-chat" id="comp-chat">
    <div class="comp-bubble" id="comp-bubble">
      <span id="comp-msg"></span>
      <span class="comp-bubble-time"><span id="comp-time"></span> <span class="comp-bubble-tick">&#10003;&#10003;</span></span>
    </div>
  </div>
  <div class="comp-bot">
    <div class="bot-antenna"></div>
    <div class="bot-head">
      <div class="bot-brows"><div class="bot-brow"></div><div class="bot-brow"></div></div>
      <div class="bot-visor">
        <div class="bot-eye"><div class="bot-eye-pupil"></div></div>
        <div class="bot-eye"><div class="bot-eye-pupil"></div></div>
      </div>
      <div class="bot-mouth smile"></div>
    </div>
    <div class="bot-torso">
      <div class="bot-core"></div>
      <div class="bot-arms">
        <div class="bot-arm"></div>
        <div class="bot-arm"></div>
      </div>
    </div>
    <div class="bot-legs">
      <div class="bot-leg"></div>
      <div class="bot-leg"></div>
    </div>
  </div>
</div>
```

### Passo 4: Injetar JavaScript

Adicionar ANTES do `</body>` (dentro de um `<script>` existente ou novo):

```javascript
(function() {
  var chat = document.getElementById('comp-chat');
  var msgEl = document.getElementById('comp-msg');
  var timeEl = document.getElementById('comp-time');
  var mouth = document.querySelector('.bot-mouth');
  var eyes = document.querySelectorAll('.bot-eye');
  if (!chat) return;

  function now() {
    var d = new Date();
    return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
  }

  setInterval(function() {
    eyes.forEach(function(e) { e.classList.add('blink'); });
    setTimeout(function() { eyes.forEach(function(e) { e.classList.remove('blink'); }); }, 300);
  }, 4000);

  // CUSTOMIZAR ESTAS MENSAGENS para cada LP
  var reactions = [
    { at: 0,    msg: 'Olá! Bem-vindo!' },
    { at: 0.15, msg: 'Continue lendo...' },
    { at: 0.30, msg: 'Interessante, né?' },
    { at: 0.50, msg: 'Veja a oferta!' },
    { at: 0.70, msg: 'Quase lá!' },
    { at: 0.90, msg: 'Não perca essa chance!' },
  ];

  var curr = -1;
  var hideTimer = null;

  function showMsg(text) {
    chat.classList.add('show');
    msgEl.innerHTML = '<span class="comp-typing"><span></span><span></span><span></span></span>';
    timeEl.textContent = '';
    if (mouth) mouth.className = 'bot-mouth';
    setTimeout(function() {
      msgEl.textContent = text;
      timeEl.textContent = now();
      if (mouth) mouth.className = 'bot-mouth smile';
    }, 700);
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function() { chat.classList.remove('show'); }, 5000);
  }

  window.addEventListener('scroll', function() {
    var pct = window.scrollY / (document.body.scrollHeight - window.innerHeight);
    var matched = 0;
    for (var i = reactions.length - 1; i >= 0; i--) {
      if (pct >= reactions[i].at) { matched = i; break; }
    }
    if (matched !== curr) {
      curr = matched;
      showMsg(reactions[matched].msg);
    }
  });

  setTimeout(function() { showMsg(reactions[0].msg); }, 2000);
})();
```

### Passo 5: Customizar mensagens

Perguntar ao usuário quais mensagens quer no balão, ou gerar automaticamente com base no conteúdo da LP. Cada mensagem tem:
- `at`: posição de scroll (0.0 = topo, 1.0 = fundo)
- `msg`: texto do balão

Regra: 1 mensagem a cada ~8-10% de scroll. Máximo 13 mensagens.

---

## Notas

- O companion é `position:fixed` — fica visível em toda a LP
- Em mobile, reduz de tamanho automaticamente (media query 640px)
- Peso total: ~2KB CSS + ~1KB JS (zero dependências externas)
- Funciona em qualquer LP, independente de framework ou libs
