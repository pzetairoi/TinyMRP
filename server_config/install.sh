#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

### ========= CONFIG =========
TINY_USER="tinymrp"
TINY_HOME="/home/${TINY_USER}"
TINY_APP_DIR="${TINY_HOME}/tinymrp"                       # repo checkout
REPO_URL="https://github.com/pzetairoi/TinyMRP.git"       # original TinyMRP

DELIVERABLES_DIR="${TINY_HOME}/Fileserver/Deliverables"
DELIVERABLES_SUBDIRS="3mf datasheet dxf edr pdf pic png reports step temp"

# Mongo settings (simple/anonymous: no auth)
MONGO_SERIES="8.0"           # MongoDB repo series for Ubuntu 24.04 (Noble)
MONGO_ALLOW_REMOTE="false"   # "true" binds 0.0.0.0 (no-auth is risky remotely!)
MONGO_DB_NAME="tinymrp"

# Nginx listen port for the app
APP_INTERNAL_HOST="127.0.0.1"
APP_INTERNAL_PORT="5000"
APP_SERVER_NAME="_"          # change to your domain if you have one
### ==========================

# ----- helpers -----
log(){ echo -e "\033[1;32m$*\033[0m"; }
warn(){ echo -e "\033[1;33m$*\033[0m"; }
err(){ echo -e "\033[1;31m$*\033[0m" >&2; }

need_root(){
  if [[ $EUID -ne 0 ]]; then err "Run as root: sudo bash install.sh"; exit 1; fi
}

ensure_group_member(){
  local user="$1" grp="$2"
  id -nG "$user" | tr ' ' '\n' | grep -qx "$grp" || usermod -a -G "$grp" "$user"
}

ensure_mongo_repo(){
  local key="/usr/share/keyrings/mongodb-server-${MONGO_SERIES}.gpg"
  local list="/etc/apt/sources.list.d/mongodb-org-${MONGO_SERIES}.list"
  if [[ ! -s "$key" ]]; then
    log "[mongo] Installing MongoDB ${MONGO_SERIES} apt key…"
    curl -fsSL "https://www.mongodb.org/static/pgp/server-${MONGO_SERIES}.asc" | gpg --dearmor > "$key"
  else
    log "[mongo] Key already present."
  fi
  if [[ ! -f "$list" ]]; then
    log "[mongo] Adding apt source list…"
    echo "deb [ arch=amd64,arm64 signed-by=${key} ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/${MONGO_SERIES} multiverse" > "$list"
  else
    log "[mongo] Apt list already present."
  fi
  apt-get update -y
}

wait_for_mongod(){
  log "[mongo] Waiting for mongod to be ready…"
  for i in {1..60}; do
    if mongosh --quiet --eval 'db.runCommand({ ping: 1 })' >/dev/null 2>&1; then
      log "[mongo] mongod is ready."; return 0
    fi
    sleep 1
  done
  err "[mongo] mongod did not become ready. Recent logs:"
  journalctl -u mongod -n 200 --no-pager || true
  exit 1
}

write_nginx_fallback(){
  # Minimal reverse proxy + static Deliverables alias
  cat >/etc/nginx/sites-available/tinymrp.conf <<EOF
server {
    listen 80;
    server_name ${APP_SERVER_NAME};

    # static deliverables
    location /Deliverables/ {
        alias ${DELIVERABLES_DIR}/;
        autoindex on;
        add_header Access-Control-Allow-Origin *;
    }

    # app reverse proxy
    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://${APP_INTERNAL_HOST}:${APP_INTERNAL_PORT};
        proxy_read_timeout 300;
    }
}
EOF
  ln -sf /etc/nginx/sites-available/tinymrp.conf /etc/nginx/sites-enabled/tinymrp.conf
  rm -f /etc/nginx/sites-enabled/default
}

write_samba_fallback(){
  # Simple anonymous share to the Deliverables folder
  cat >/etc/samba/smb.conf <<EOF
[global]
   workgroup = WORKGROUP
   server role = standalone server
   map to guest = Bad User
   usershare allow guests = yes

[Deliverables]
   path = ${DELIVERABLES_DIR}
   browseable = yes
   read only = no
   guest ok = yes
   force user = ${TINY_USER}
   create mask = 0664
   directory mask = 0775
EOF
}

write_wrapper_launcher(){
  # Wrapper tries common entrypoints to start the Flask app
  cat >/usr/local/bin/tinymrp-launch <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$1"
APP_HOST="$2"
APP_PORT="$3"
ENV_FILE="$4"

cd "$APP_DIR"
source "$APP_DIR/venv/bin/activate" || { echo "Missing venv"; exit 1; }
[ -f "$ENV_FILE" ] && set -o allexport && source "$ENV_FILE" && set +o allexport

# Try common start patterns in order:
if [ -f "run.py" ]; then
  exec python run.py
elif [ -f "app.py" ]; then
  exec python app.py
elif [ -f "wsgi.py" ]; then
  exec gunicorn --workers 3 --bind "${APP_HOST}:${APP_PORT}" wsgi:app
elif grep -qi "Flask" **/*.py 2>/dev/null; then
  # Best-effort: try app:app
  exec gunicorn --workers 3 --bind "${APP_HOST}:${APP_PORT}" app:app
else
  # Last resort: flask run
  export FLASK_APP=app.py
  exec flask run -h "${APP_HOST}" -p "${APP_PORT}"
fi
EOF
  chmod +x /usr/local/bin/tinymrp-launch
}

write_systemd_unit(){
  cat >/etc/systemd/system/tinymrp_server.service <<EOF
[Unit]
Description=TinyMRP (original) web service
After=network.target mongod.service
Wants=mongod.service

[Service]
User=${TINY_USER}
Group=${TINY_USER}
EnvironmentFile=/etc/tinymrp.env
WorkingDirectory=${TINY_APP_DIR}
ExecStart=/usr/local/bin/tinymrp-launch ${TINY_APP_DIR} ${APP_INTERNAL_HOST} ${APP_INTERNAL_PORT} /etc/tinymrp.env
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
}

write_clean_mongod_conf(){
  # One-time backup if not already saved
  if [[ ! -f /etc/mongod.conf.installer.bak ]]; then
    cp -a /etc/mongod.conf /etc/mongod.conf.installer.bak 2>/dev/null || true
  fi

  # Build a minimal, valid config (NO 'security:' block at all)
  local bindip="127.0.0.1"
  [[ "${MONGO_ALLOW_REMOTE}" == "true" ]] && bindip="0.0.0.0"

  cat >/etc/mongod.conf <<EOF
# Minimal mongod.conf written by installer
# Auth is disabled by omission of the 'security' section.
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

processManagement:
  fork: false

net:
  port: 27017
  bindIp: ${bindip}
EOF

  # Ensure dirs/ownership exist as expected
  install -d -o mongodb -g mongodb /var/lib/mongodb /var/log/mongodb || true
  chown -R mongodb:mongodb /var/lib/mongodb /var/log/mongodb || true
}
# -----------------------------

need_root

log "[1/10] Apt prep & base packages…"
apt-get update -y
apt-get install -y software-properties-common curl ca-certificates gpg gnupg

# Python 3.10 for the original pins
add-apt-repository -y ppa:deadsnakes/ppa || true
apt-get update -y
apt-get install -y \
  python3.10 python3.10-venv python3.10-dev build-essential \
  libxml2-dev libxslt1-dev zlib1g-dev pkg-config \
  git nginx samba net-tools magic-wormhole

log "[2/10] Ensure user '${TINY_USER}' exists…"
if ! id -u "${TINY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${TINY_USER}"
fi
ensure_group_member "${TINY_USER}" "www-data"
ensure_group_member "${TINY_USER}" "sambashare"

log "[3/10] Folders & permissions…"
mkdir -p "${DELIVERABLES_DIR}"
for d in ${DELIVERABLES_SUBDIRS}; do
  mkdir -p "${DELIVERABLES_DIR}/${d}"
done
chown -R "${TINY_USER}:sambashare" "${TINY_HOME}"
chmod -R 775 "${TINY_HOME}"

log "[4/10] Clone/refresh TinyMRP repo…"
if [[ -d "${TINY_APP_DIR}/.git" ]]; then
  sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" fetch --all --prune
  # try main, fallback to master
  if sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" rev-parse --verify origin/main >/dev/null 2>&1; then
    sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" reset --hard origin/main
  else
    sudo -u "${TINY_USER}" git -C "${TINY_APP_DIR}" reset --hard origin/master || true
  fi
else
  sudo -u "${TINY_USER}" git clone "${REPO_URL}" "${TINY_APP_DIR}"
fi

log "[5/10] Python venv (3.10) + requirements…"
if [[ ! -d "${TINY_APP_DIR}/venv" ]]; then
  sudo -u "${TINY_USER}" /usr/bin/python3.10 -m venv "${TINY_APP_DIR}/venv"
fi
sudo -u "${TINY_USER}" bash -lc "source '${TINY_APP_DIR}/venv/bin/activate' \
  && pip install -U pip setuptools wheel \
  && pip install -r '${TINY_APP_DIR}/requirements.txt'"

log "[6/10] MongoDB ${MONGO_SERIES} repo & install…"
ensure_mongo_repo
apt-get install -y mongodb-org mongodb-mongosh mongodb-org-tools

log "[7/10] Write a clean mongod.conf (no-auth) and start…"
write_clean_mongod_conf
systemctl daemon-reload
systemctl enable mongod
systemctl restart mongod
wait_for_mongod
# Touch the DB so it's created; no users/auth
mongosh --quiet --eval "db.getSiblingDB('${MONGO_DB_NAME}').runCommand({ ping: 1 })" >/dev/null || true

log "[8/10] Samba config…"
if [[ -f "${TINY_APP_DIR}/server_config/smb.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/smb.conf" /etc/samba/smb.conf
  sed -i "s|/home/tinymrp/Fileserver/Deliverables|${DELIVERABLES_DIR}|g" /etc/samba/smb.conf || true
else
  write_samba_fallback
fi
systemctl restart smbd.service || systemctl restart samba.service || true
chmod -R 775 "${DELIVERABLES_DIR}"

log "[9/10] Nginx config…"
if [[ -f "${TINY_APP_DIR}/server_config/nginx.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/nginx.conf" /etc/nginx/nginx.conf
fi
if [[ -f "${TINY_APP_DIR}/server_config/tinymrp.conf" ]]; then
  cp "${TINY_APP_DIR}/server_config/tinymrp.conf" /etc/nginx/sites-available/tinymrp.conf
  sed -i "s|/home/tinymrp/Fileserver/Deliverables|${DELIVERABLES_DIR}|g" /etc/nginx/sites-available/tinymrp.conf || true
  ln -sf /etc/nginx/sites-available/tinymrp.conf /etc/nginx/sites-enabled/tinymrp.conf
  rm -f /etc/nginx/sites-enabled/default
else
  write_nginx_fallback
fi
nginx -t
systemctl restart nginx

log "[9.1/10] Runtime env file…"
cat > /etc/tinymrp.env <<EOF
# TinyMRP runtime env
MONGO_URI=mongodb://127.0.0.1:27017/${MONGO_DB_NAME}
DELIVERABLES_DIR=${DELIVERABLES_DIR}
EOF
chown root:${TINY_USER} /etc/tinymrp.env
chmod 640 /etc/tinymrp.env

log "[10/10] Systemd service…"
SERVICE_DST="/etc/systemd/system/tinymrp_server.service"
if [[ -f "${TINY_APP_DIR}/server_config/tinymrp_server.service" ]]; then
  cp "${TINY_APP_DIR}/server_config/tinymrp_server.service" "${SERVICE_DST}"
  sed -i "s|^User=.*|User=${TINY_USER}|g" "${SERVICE_DST}" || true
  sed -i "s|/home/tinymrp/tinymrp|${TINY_APP_DIR}|g" "${SERVICE_DST}" || true
  sed -i "s|/home/tinymrp/venv|${TINY_APP_DIR}/venv|g" "${SERVICE_DST}" || true
  grep -q '^EnvironmentFile=' "${SERVICE_DST}" || sed -i '/^\[Service\]/a EnvironmentFile=/etc/tinymrp.env' "${SERVICE_DST}"
else
  write_wrapper_launcher
  write_systemd_unit
fi

systemctl daemon-reload
systemctl enable tinymrp_server.service
systemctl restart tinymrp_server.service

# Optional firewall open
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow "Nginx Full" || true
  # ufw allow 27017/tcp  # uncomment ONLY if MONGO_ALLOW_REMOTE=true
fi

echo
log "✅ Install complete."
echo "URL:  http://<server-ip>/"
echo "App dir: ${TINY_APP_DIR}"
echo "Files:   ${DELIVERABLES_DIR}"
echo "Mongo:   no-auth, bindIp=$( [[ ${MONGO_ALLOW_REMOTE} == true ]] && echo 0.0.0.0 || echo 127.0.0.1 )"
systemctl --no-pager status tinymrp_server | sed -n '1,5p' || true
