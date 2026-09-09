# deploy-CLIENTE_EXEMPLO-module

## Purpose
Deploy de módulos no CLIENTE_EXEMPLO VPS via Paramiko (upload SFTP, migration SQL, build Next.js, restart PM2).

---

## Task Definition

```yaml
task: deploy-CLIENTE_EXEMPLO-module()
responsável: Dev (Dex) | DevOps (Gage)
responsavel_type: Agente
atomic_layer: Organism

Entrada:
  - campo: modulo
    tipo: string
    origem: parâmetro
    obrigatório: true
  - campo: arquivos
    tipo: lista
    origem: diretório local ~/CLIENTE_EXEMPLO-{modulo}/
    obrigatório: true
  - campo: migration_file
    tipo: string
    origem: lib/db/migrations/
    obrigatório: false

Saída:
  - campo: deploy_status
    tipo: string (success|failed)
    destino: terminal
```

---

## Credenciais VPS
- IP: ${VPS_HOST}
- Usuário: root
- Senha: ver memory CLIENTE_EXEMPLO.md
- App: /opt/CLIENTE_EXEMPLO/
- PM2: CLIENTE_EXEMPLO

## Padrão do Deploy Script (Python + Paramiko)

```python
# Estrutura do script deploy_{modulo}.py
VPS_HOST = '${VPS_HOST}'
VPS_USER = 'root'
REMOTE_BASE = '/opt/CLIENTE_EXEMPLO'

# [1/5] Upload arquivos via SFTP
# [2/5] Executar migration (se houver)
# [3/5] Configurar variáveis de ambiente
# [4/5] npm run build
# [5/5] pm2 restart CLIENTE_EXEMPLO --update-env
# [Verificação] curl localhost:3000/api/{endpoint}
```

## Checklist pós-deploy
- [ ] Build compilou sem erros
- [ ] PM2 restart com status online
- [ ] Endpoint responde 200
- [ ] Middleware publicPaths atualizado (se webhook público)

---

## Metadata
```yaml
version: 1.0.0
tags: [deploy, vps, CLIENTE_EXEMPLO, pm2]
updated_at: 2026-03-15
```
