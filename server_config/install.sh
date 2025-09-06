#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

### ----- configurable bits -----
TINY_USER="tinymrp"
TINY_HOME="/home/${TINY_USER}"
TINY_APP_DIR="${TINY_HOME}/tinymrp"                    # repo checkout
DELIVERABLES_DIR="${TINY_HOME}/Fileserver/Deliverables"
REPO_URL="https://github.com/pzetairoi/TinyMRP.git"    # original repo

# Deliverables subfolders (space-separated)
DELIVERABLES_SUBDIRS="3mf datasheet dxf edr pdf pic png reports step temp"
### --------------------------------

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash install.sh"; exit 1
fi

echo "[1/9] Apt prep + Python 3.10 (Deadsnakes)…"
apt-get update -y
apt-get install -y software-properties-common gnupg
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y

echo "[2/9] Base packages…"
apt-get install -y \
  build-essential git nginx samba net-tools \
  python3.10 python3.10-venv python3.10-dev \
  libxml2-dev libxslt1-dev zlib1g-dev pkg-config \
  magic-wormhole

echo "[3/9] Ensure user '${TINY_USER}' exists…"
if ! id -u "${TINY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${TINY_USER}"
fi
usermod -a -G www-data,sambashare "${TINY_USER}"

echo "[4/9] Folders & permissions…"
mkdir -p "${DELIVERABLES_DIR}"
for d in ${DELIVERABLES_SUBDIRS}; do
  mkdir -p "${DELIVERABLES_DIR}/${d}"
done
chown -R "${TINY_USER}:sambashare" "${TINY_HOME}"
chmod -R 775 "${TINY_HOME}"

echo "[5/9] Clone/refresh TinyMRP repo…"
if [[ -d "${TINY_APP_DIR}/.git" ]]; then
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" fetch --all --prune
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" reset --hard origin/main || \
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" reset --hard origin/master || true
else
  sudo -u "${TINY_USER}" git clone "${REPO_URL}" "${TINY_APP_DIR}"
fi

echo "[6/9] Python venv (3.10) + deps…"
sudo -u "${TINY_USER}" /usr/bin/python3.10 -m venv "${TINY_APP_DIR}/venv"
sudo -u "${TINY_USER}" bash -lc "source '${TINY_APP_DIR}/venv/bin/activate' \
  && pip install -U pip setuptools wheel \
  && pip install -r '${TINY_APP_DIR}/requirements.txt'"

echo "[7/9] Samba config…"
if [[ -f "${TINY_APP_DIR}/server_config/smb.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/smb.conf" /etc/samba/smb.conf
  # patch share path if a different folder was chosen
  sed -i "s|/home/tinymrp/Fileserver/Deliverables|${DELIVERABLES_DIR}|g" /etc/samba/smb.conf || true
  systemctl restart smbd.service
fi

echo "[8/9] Nginx config…"
if [[ -f "${TINY_APP_DIR}/server_config/nginx.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/nginx.conf" /etc/nginx/nginx.conf
fi
if [[ -f "${TINY_APP_DIR}/server_config/tinymrp.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/tinymrp.conf" /etc/nginx/sites-available/tinymrp.conf
  sed -i "s|/home/tinymrp/Fileserver/Deliverables|${DELIVERABLES_DIR}|g" /etc/nginx/sites-available/tinymrp.conf || true
  ln -sf /etc/nginx/sites-available/tinymrp.conf /etc/nginx/sites-enabled/tinymrp.conf
  rm -f /etc/nginx/sites-enabled/default
fi
nginx -t
systemctl restart nginx

echo "[9/9] Systemd service…"
SERVICE_SRC="${TINY_APP_DIR}/server_config/tinymrp_server.service"
SERVICE_DST="/etc/systemd/system/tinymrp_server.service"
if [[ -f "${SERVICE_SRC}" ]]; then
  cp "${SERVICE_SRC}" "${SERVICE_DST}"
  # ensure service runs as the right user and paths are correct
  sed -i "s|^User=.*|User=${TINY_USER}|g" "${SERVICE_DST}" || true
  sed -i "s|/home/tinymrp/tinymrp|${TINY_APP_DIR}|g" "${SERVICE_DST}" || true
  sed -i "s|/home/tinymrp/venv|${TINY_APP_DIR}/venv|g" "${SERVICE_DST}" || true
fi
systemctl daemon-reload
systemctl enable tinymrp_server.service
systemctl restart tinymrp_server.service

# Optional: open firewall if UFW is active
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow "Nginx Full" || true
fi

echo "✅ Done. Visit http://<server-ip>/"
echo "   App dir: ${TINY_APP_DIR}"
echo "   Deliverables: ${DELIVERABLES_DIR}"
