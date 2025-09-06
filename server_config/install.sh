# 1) If you partially added the Mongo key/list, make them consistent
test -s /usr/share/keyrings/mongodb-server-8.0.gpg || \
  curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc \
  | gpg --dearmor > /usr/share/keyrings/mongodb-server-8.0.gpg

test -f /etc/apt/sources.list.d/mongodb-org-8.0.list || \
  echo 'deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse' \
  > /etc/apt/sources.list.d/mongodb-org-8.0.list

apt-get update -y
apt-get install -y mongodb-org mongodb-mongosh

# 2) Ensure mongod is up
systemctl enable --now mongod

# 3) Wait until mongod answers (up to 60s)
for i in {1..60}; do
  mongosh --quiet --eval 'db.runCommand({ ping: 1 })' && break
  sleep 1
  if [ $i -eq 60 ]; then
    echo "mongod never became ready. Recent logs:"; journalctl -u mongod -n 200 --no-pager; exit 1
  fi
done

# 4) Create users if missing (AUTH OFF path)
# If you already enabled authorization and forgot the admin password, temporarily disable it:
#   sed -i 's/^\s*authorization:\s*enabled/# authorization: enabled/' /etc/mongod.conf && systemctl restart mongod
mongosh --quiet --eval "
db = db.getSiblingDB('admin');
if (!db.getUser('admin')) {
  db.createUser({user:'admin',pwd:'$(openssl rand -base64 24)',roles:['root']});
}
"

# 5) Re-enable authorization (safe if already enabled)
grep -q '^\s*authorization:\s*enabled' /etc/mongod.conf || \
awk 'BEGIN{insec=0} /^security:/ {print; print "  authorization: enabled"; insec=1; next} {print}
     END{if(insec==0) print "security:\n  authorization: enabled"}' \
/etc/mongod.conf > /etc/mongod.conf.new && mv /etc/mongod.conf.new /etc/mongod.conf
systemctl restart mongod

# 6) Ensure the app user exists (authenticate as admin)
mongosh --quiet -u admin -p 'YOUR_ADMIN_PASS' --authenticationDatabase admin --eval "
db = db.getSiblingDB('tinymrp');
if (!db.getUser('tinymrp')) {
  db.createUser({user:'tinymrp',pwd:'$(openssl rand -base64 24)',roles:['readWrite']});
}
"
