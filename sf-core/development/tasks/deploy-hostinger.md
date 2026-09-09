# deploy-hostinger

## Purpose
Upload de arquivos HTML/CSS/JS para o servidor Hostinger via SCP (expect + porta 65002).

---

## Task Definition

```yaml
task: deploy-hostinger()
responsável: Dev (Dex)
responsavel_type: Agente
atomic_layer: Organism

Entrada:
  - campo: arquivo_local
    tipo: string
    origem: parâmetro
    obrigatório: true
    validação: arquivo deve existir localmente
  - campo: destino
    tipo: string
    origem: parâmetro
    obrigatório: true
    validação: path relativo a ~/domains/seudominio.com.br/public_html/

Saída:
  - campo: url_publica
    tipo: string
    destino: terminal
    persistido: false
```

---

## Credenciais
- IP: ${VPS_HOST}
- Porta: 65002
- Usuário: ${HOSTINGER_USER}
- Senha: ver memory hostinger.md
- Método: expect + SCP (sshpass não disponível no Mac)

## Execução

### 1. Verificar arquivo local
```bash
ls -la {arquivo_local}
```

### 2. Criar diretório remoto (se necessário)
```bash
expect -c '
spawn ssh -p ${SSH_PORT} ${HOSTINGER_USER}@${VPS_HOST}
expect "password:"
send "{senha}\r"
expect "$ "
send "mkdir -p ~/domains/seudominio.com.br/public_html/{destino} && echo OK\r"
expect "OK"
send "exit\r"
expect eof
'
```

### 3. Upload via SCP
```bash
expect -c '
spawn scp -P 65002 {arquivo_local} ${HOSTINGER_USER}@${VPS_HOST}:~/domains/seudominio.com.br/public_html/{destino}/index.html
expect "password:"
send "{senha}\r"
expect eof
'
```

### 4. Confirmar
URL pública: https://seudominio.com.br/{destino}/

---

## Metadata
```yaml
version: 1.0.0
tags: [deploy, hostinger, upload]
updated_at: 2026-03-15
```
