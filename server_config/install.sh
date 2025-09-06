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
        add_header_
