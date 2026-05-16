#!/bin/bash
# update.sh — Actualizar el backend desde GitHub (usar después de cada git push)
# Ejecutar en Oracle Cloud: bash update.sh
set -e
cd /home/ubuntu/SRV-Oratoria-IA
git pull origin main
source backend/venv/bin/activate
pip install -r backend/requirements-prod.txt --quiet
sudo systemctl restart srv
echo "Backend actualizado y reiniciado OK"
sudo systemctl status srv --no-pager
