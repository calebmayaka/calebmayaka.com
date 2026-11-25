#!/usr/bin/env bash
# Deploy the latest main branch of calebmayaka.com.
#   backup -> git pull -> build image tagged with the commit -> restart -> health check
# Every deploy keeps its image (calebmayaka:<commit>) so bin/rollback.sh can go back.
set -euo pipefail
APP=/srv/apps/calebmayaka.com
cd "$APP"
echo "== backup";  sudo systemctl start backup-postgres.service && sudo ls /srv/backups/postgres | tail -1
echo "== update";  git -C src checkout -q main && git -C src pull -q --ff-only
REV=$(git -C src rev-parse --short HEAD)
# Pick up changes to the server-side files that live in the repo.
cp src/deploy/vps/compose.yml compose.yml
cp src/deploy/vps/bin/*.sh bin/ && chmod +x bin/*.sh
if ! sudo cmp -s src/deploy/vps/calebmayaka.com.caddy /srv/proxy/sites/calebmayaka.com.caddy; then
  echo "== caddy config changed: reloading"
  sudo install -m 644 src/deploy/vps/calebmayaka.com.caddy /srv/proxy/sites/calebmayaka.com.caddy
  sudo docker exec caddy caddy reload --config /etc/caddy/Caddyfile
fi
PREV_ID=$(sudo docker inspect -f '{{.Image}}' calebmayaka 2>/dev/null || true)
[ -n "$PREV_ID" ] && sudo docker tag "$PREV_ID" calebmayaka:previous || true
echo "== build $REV"; sudo docker compose build -q && sudo docker tag calebmayaka:latest "calebmayaka:$REV"
echo "== restart"; sudo docker compose up -d
for i in $(seq 1 30); do
  sleep 2
  if sudo docker exec calebmayaka python -c "import urllib.request as u; r=u.urlopen(u.Request('http://127.0.0.1:8000/healthz', headers={'Host': 'calebmayaka.com', 'X-Forwarded-Proto': 'https'}), timeout=5); raise SystemExit(r.status != 200)" 2>/dev/null; then
    echo "== healthy: calebmayaka /healthz OK ($REV)"; break
  fi
  [ "$i" = 30 ] && { echo "!! health check failed - see: sudo docker logs --tail 50 calebmayaka ; or $APP/bin/rollback.sh"; exit 1; }
done
# keep the 5 most recent commit-tagged images
sudo docker images calebmayaka --format '{{.Tag}} {{.CreatedAt}}' | grep -vE '^(latest|previous) ' | sort -k2 -r | tail -n +6 | awk '{print "calebmayaka:"$1}' | xargs -r sudo docker rmi >/dev/null 2>&1 || true
