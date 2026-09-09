#!/bin/bash
# Wrapper para request-approval.js que está em meeting-pipeline (onde node_modules existe)
# Uso: ~/scripts/request-approval.sh --action ACTION_ID [--diagnosis "texto"]
cd "$HOME/meeting-pipeline" && node scripts/request-approval.js "$@"
