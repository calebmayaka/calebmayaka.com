#!/usr/bin/env bash
# Roll calebmayaka.com back to the image from before the last deploy (or a given tag).
#   bin/rollback.sh            -> calebmayaka:previous
#   bin/rollback.sh c1b73bd    -> calebmayaka:c1b73bd   (list: sudo docker images calebmayaka)
# Does NOT undo database migrations; restore a backup if a migration is the problem.
set -euo pipefail
cd /srv/apps/calebmayaka.com
TAG=${1:-previous}
sudo docker image inspect "calebmayaka:$TAG" >/dev/null
sudo docker tag "calebmayaka:$TAG" calebmayaka:latest
sudo docker compose up -d --no-build --force-recreate
echo "== rolled back to calebmayaka:$TAG"
