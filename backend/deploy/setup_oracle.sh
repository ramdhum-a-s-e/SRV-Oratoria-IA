#!/bin/bash
# =============================================================================
# setup_oracle.sh — Configuración inicial de Oracle Cloud Ubuntu 22.04 (ARM)
# Ejecutar UNA SOLA VEZ como usuario ubuntu después de crear la instancia
# Uso: bash setup_oracle.sh
# =============================================================================
set -e
echo "=== SRV-Oratoria-IA: Setup Oracle Cloud ARM ==="

# ── 1. Sistema base ───────────────────────────────────────────────────────────
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3.11 python3.11-venv python3.11-dev \
    python3-pip nginx ffmpeg libavcodec-extra build-essential \
    libsndfile1 curl unzip

# ── 2. Abrir puertos en firewall del sistema ──────────────────────────────────
# IMPORTANTE: También debes abrir puerto 8000 en Oracle Cloud Console →
# Networking → VCN → Security Lists → Add Ingress Rule → Puerto 8000
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80   -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443  -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save

# ── 3. Clonar repositorio ─────────────────────────────────────────────────────
cd /home/ubuntu
git clone https://github.com/TU_USUARIO/SRV-Oratoria-IA.git
cd SRV-Oratoria-IA/backend

# ── 4. Entorno virtual Python ─────────────────────────────────────────────────
python3.11 -m venv venv
source venv/bin/activate

# ── 5. Instalar dependencias (sin paquetes de desarrollo) ────────────────────
pip install --upgrade pip
pip install -r requirements-prod.txt

# ── 6. Descargar modelo Whisper (primera vez, tarda ~5 min) ──────────────────
python3 -c "
from faster_whisper import WhisperModel
print('Descargando faster-whisper medium...')
WhisperModel('medium', device='cpu', compute_type='int8')
print('Modelo descargado OK')
"

# ── 7. Crear .env de producción ───────────────────────────────────────────────
echo ""
echo "=== PASO MANUAL: Debes crear el archivo .env ==="
echo "Ejecuta: nano /home/ubuntu/SRV-Oratoria-IA/backend/.env"
echo "Y pega el contenido del .env.example con tus valores reales"
echo ""

# ── 8. Instalar servicio systemd ──────────────────────────────────────────────
sudo cp /home/ubuntu/SRV-Oratoria-IA/backend/deploy/srv.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable srv
echo "Servicio srv instalado. Para iniciarlo: sudo systemctl start srv"

# ── 9. Configurar nginx ───────────────────────────────────────────────────────
sudo cp /home/ubuntu/SRV-Oratoria-IA/backend/deploy/nginx.conf /etc/nginx/sites-available/srv
sudo ln -sf /etc/nginx/sites-available/srv /etc/nginx/sites-enabled/srv
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "=== Setup completado ==="
echo "Próximos pasos:"
echo "1. Crea /home/ubuntu/SRV-Oratoria-IA/backend/.env con tus variables reales"
echo "2. sudo systemctl start srv"
echo "3. sudo systemctl status srv  (verifica que esté corriendo)"
echo "4. Visita http://TU_IP_PUBLICA  para verificar"
