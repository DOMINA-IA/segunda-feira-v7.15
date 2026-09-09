#!/bin/bash
# Wrapper do Auto Orchestrator — usa o venv da Segunda-feira (tem fastapi+anthropic+yaml+requests).
SF_VENV="$HOME/Desktop/segunda-feira-jarvis/.venv/bin/python3"
if [[ -x "$SF_VENV" ]]; then
  "$SF_VENV" $HOME/framework/scripts/auto_orchestrator.py "$@"
else
  # Fallback: framework python (pode falhar se faltar fastapi)
  /usr/local/bin/python3 $HOME/framework/scripts/auto_orchestrator.py "$@"
fi
