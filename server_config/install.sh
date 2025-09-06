#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

### ====== CONFIGURABLES ======
TINY_USER="tinymrp"
TINY_HOME="/home/${TINY_USER}"
TINY_APP_DIR="${TINY_HOME}/tinymrp"                      # repo checkout
REPO_URL="https://github.com/pzetairoi/TinyMRP.git"      # original TinyMRP

DELIVERABLES_DIR="${TINY_HOME}/Fileserver/Deliverables"
DELIVERABLES_SUBDIRS="3mf datasheet dxf edr pdf pic png reports step temp"

# MongoDB settings
MONGO_VERSION_SHORT="8.0"                                # official repo series
MONGO_ALLOW_REMOTE="false"                               # "true" to bind 0.0.0.0
MONGO_ENABLE_AUTH="true"                                 # enable SCRAM auth
MONGO_ADMIN_USER="admin"
MONGO_ADMIN_PASS="${MONGO_ADMIN_PASS:-}"                 # optional preseed via env
MONGO_APP_DB="tinymrp"
MONGO_APP_USER="tinymrp"
MONGO_APP_PASS="${MONGO_APP_PASS:-}"                     # optional preseed via env
### ===========================

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash install.sh"; exit 1
fi

rand_pw () { openssl rand -base64 24 | tr -d '\n='; }

echo "[0/12] Ensure base apt tools…"
apt-get update -y
apt-get install -y software-properties-common gnupg curl ca-certificates

echo "[1/12] Python 3.10 via Deadsnakes (TinyMRP’s 2021 pins expect <=3.10)…"
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y python3.10 python3.10-venv python3.10-dev build-essential \
                   libxml2-dev libxslt1-dev zlib1g-dev pkg-config git nginx samba net-tools \
                   magic-wormhole

echo "[2/12] Create '${TINY_USER}' user and folders…"
if ! id -u "${TINY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${TINY_USER}"
fi
usermod -a -G www-data,sambashare "${TINY_USER}"

mkdir -p "${DELIVERABLES_DIR}"
for d in ${DELIVERABLES_SUBDIRS}; do
  mkdir -p "${DELIVERABLES_DIR}/${d}"
done
chown -R "${TINY_USER}:sambashare" "${TINY_HOME}"
chmod -R 775 "${TINY_HOME}"

echo "[3/12] Clone/refresh TinyMRP repo…"
if [[ -d "${TINY_APP_DIR}/.git" ]]; then
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" fetch --all --prune
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" reset --hard origin/main || \
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" reset --hard origin/master || true
else
  sudo -u "${TINY_USER}" git clone "${REPO_URL}" "${TINY_APP_DIR}"
fi

echo "[4/12] Python venv + deps…"
sudo -u "${TINY_USER}" /usr/bin/python3.10 -m venv "${TINY_APP_DIR}/venv"
sudo -u "${TINY_USER}" bash -lc "source '${TINY_APP_DIR}/venv/bin/activate' \
  && pip install -U pip setuptools wheel \
  && pip install -r '${TINY_APP_DIR}/requirements.txt'"

echo "[5/12] MongoDB ${MONGO_VERSION_SHORT} repo (Ubuntu 24.04 Noble)…"
# Official instructions: add GPG key + apt list file for Noble (8.0 series)
# https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/
curl -fsSL "https://www.mongodb.org/static/pgp/server-${MONGO_VERSION_SHORT}.asc" \
  | gpg -o /usr/share/keyrings/mongodb-server-${MONGO_VERSION_SHORT}.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-${MONGO_VERSION_SHORT}.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/${MONGO_VERSION_SHORT} multiverse" \
  > /etc/apt/sources.list.d/mongodb-org-${MONGO_VERSION_SHORT}.list
apt-get update -y
apt-get install -y mongodb-org mongodb-mongosh mongodb-org-tools

echo "[6/12] Start MongoDB…"
systemctl daemon-reload
systemctl enable mongod
systemctl start mongod

echo "[7/12] Configure mongod.conf (bindIp, then later enable auth)…"
# bindIp: keep localhost by default; allow remote if requested
if [[ "${MONGO_ALLOW_REMOTE}" == "true" ]]; then
  sed -i 's/^\(\s*bindIp:\s*\).*/\10.0.0.0/' /etc/mongod.conf || true
else
  # ensure localhost is set (default)
  sed -i 's/^\(\s*bindIp:\s*\).*/\1127.0.0.1/' /etc/mongod.conf || true
fi
systemctl restart mongod

echo "[8/12] Create Mongo users…"
# Seed passwords if not provided
if [[ -z "${MONGO_ADMIN_PASS}" ]]; then MONGO_ADMIN_PASS="$(rand_pw)"; fi
if [[ -z "${MONGO_APP_PASS}"  ]]; then MONGO_APP_PASS="$(rand_pw)"; fi

# 8a) Create admin user (no auth yet)
mongosh --quiet --eval "
db = db.getSiblingDB('admin');
if (!db.getUser('${MONGO_ADMIN_USER}')) {
  db.createUser({user: '${MONGO_ADMIN_USER}', pwd: '${MONGO_ADMIN_PASS}', roles: ['root']});
}
"

# 8b) Enable authorization now
if [[ "${MONGO_ENABLE_AUTH}" == "true" ]]; then
  if ! grep -q '^\s*authorization:\s*enabled' /etc/mongod.conf; then
    awk '
      BEGIN{insec=0}
      /^security:/ {print; print "  authorization: enabled"; insec=1; next}
      {print}
      END{if(insec==0) print "security:\n  authorization: enabled"}
    ' /etc/mongod.conf > /etc/mongod.conf.new
    mv /etc/mongod.conf.new /etc/mongod.conf
  fi
  systemctl restart mongod
fi

# 8c) Create app user on ${MONGO_APP_DB} (authenticate as admin if auth enabled)
AUTH_ARGS=()
if [[ "${MONGO_ENABLE_AUTH}" == "true" ]]; then
  AUTH_ARGS=( -u "${MONGO_ADMIN_USER}" -p "${MONGO_ADMIN_PASS}" --authenticationDatabase admin )
fi
mongosh --quiet "${AUTH_ARGS[@]}" --eval "
db = db.getSiblingDB('${MONGO_APP_DB}');
if (!db.getUser('${MONGO_APP_USER}')) {
  db.createUser({user: '${MONGO_APP_USER}', pwd: '${MONGO_APP_PASS}', roles: ['readWrite']});
}
"

echo "[9/12] Write app environment (/etc/tinymrp.env) with MONGO_URI…"
MONGO_HOST="127.0.0.1"
[[ "${MONGO_ALLOW_REMOTE}" == "true" ]] && MONGO_HOST="0.0.0.0"
MONGO_URI="mongodb://${MONGO_APP_USER}:${MONGO_APP_PASS}@${MONGO_HOST}:27017/${MONGO_APP_DB}?authSource=admin"
cat > /etc/tinymrp.env <<EOF
# TinyMRP runtime
MONGO_URI=${MONGO_URI}
DELIVERABLES_DIR=${DELIVERABLES_DIR}
EOF
chmod 640 /etc/tinymrp.env
chown root:${TINY_USER} /etc/tinymrp.env

echo "[10/12] Samba config…"
if [[ -f "${TINY_APP_DIR}/server_config/smb.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/smb.conf" /etc/samba/smb.conf
  sed -i "s|/home/tinymrp/Fileserver/Deliverables|${DELIVERABLES_DIR}|g" /etc/samba/smb.conf || true
  systemctl restart smbd.service || systemctl restart samba.service || true
fi
chmod -R 775 "${DELIVERABLES_DIR}"

echo "[11/12] Nginx config…"
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

echo "[12/12] Systemd service for TinyMRP…"
SERVICE_SRC="${TINY_APP_DIR}/server_config/tinymrp_server.service"
SERVICE_DST="/etc/systemd/system/tinymrp_server.service"
if [[ -f "${SERVICE_SRC}" ]]; then
  cp "${SERVICE_SRC}" "${SERVICE_DST}"
fi
# Ensure paths + user + environment file
sed -i "s|^User=.*|User=${TINY_USER}|g" "${SERVICE_DST}" || true
sed -i "s|/home/tinymrp/tinymrp|${TINY_APP_DIR}|g" "${SERVICE_DST}" || true
sed -i "s|/home/tinymrp/venv|${TINY_APP_DIR}/venv|g" "${SERVICE_DST}" || true
# Inject EnvironmentFile if not present
grep -q '^EnvironmentFile=' "${SERVICE_DST}" || \
  sed -i '/^\[Service\]/a EnvironmentFile=/etc/tinymrp.env' "${SERVICE_DST}"

systemctl daemon-reload
systemctl enable tinymrp_server.service
systemctl restart tinymrp_server.service

# Optional: open firewall
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow "Nginx Full" || true
  ufw allow 27017/tcp || true
fi

echo
echo "✅ Install complete."
echo "URL:  http://<server-ip>/"
echo "App:  ${TINY_APP_DIR}"
echo "Files: ${DELIVERABLES_DIR}"
[[ "${MONGO_ENABLE_AUTH}" == "true" ]] && \
  echo "Mongo admin: ${MONGO_ADMIN_USER} / ${MONGO_ADMIN_PASS}"
echo "Mongo app:   ${MONGO_APP_USER} / ${MONGO_APP_PASS} (db: ${MONGO_APP_DB})"
echo "MONGO_URI saved to /etc/tinymrp.env"
