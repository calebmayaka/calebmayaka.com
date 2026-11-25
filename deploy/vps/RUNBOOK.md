# calebmayaka.com: runbook

Server: Contabo VPS `161.97.79.224` (Ubuntu 26.04). Log in with SSH key as `caleb`.
App folder: `/srv/apps/calebmayaka.com`. Commands below run on the server.

| | |
|---|---|
| Site | https://calebmayaka.com (www redirects to it) |
| CMS | https://calebmayaka.com/cms/ |
| Health check | https://calebmayaka.com/healthz → `ok` |
| Code | github.com/calebmayaka/calebmayaka.com (branch `main`), cloned to `src/` |

## Layout

```
/srv/apps/calebmayaka.com/
  compose.yml      container "calebmayaka" (gunicorn :8000, networks "web" + "db")
  .env             secrets: DJANGO_SECRET_KEY, DB_* (shared postgres), SMTP, Giscus (never in git)
  media/           CMS uploads (served by Caddy at /media/)
  static/          collected static files (served by Caddy at /static/)
  src/             git clone of the repo (Dockerfile is src/calebmayaka/Dockerfile)
  bin/             deploy.sh, rollback.sh
/srv/proxy/sites/calebmayaka.com.caddy   HTTPS + routing (shared Caddy container)
Database: "calebmayaka" (role "calebmayaka") on the shared postgres container (/srv/db)
```

The server-side files are versioned in the repo under `deploy/vps/`; `bin/deploy.sh` copies them into place.

## Everyday

**Deploy** (after pushing to `main`): `/srv/apps/calebmayaka.com/bin/deploy.sh`
Backs up, pulls, builds `calebmayaka:<commit>`, restarts and health-checks. Migrations and collectstatic run on container start.

**A deploy broke something:** `/srv/apps/calebmayaka.com/bin/rollback.sh` (or `rollback.sh <tag>`; tags: `sudo docker images calebmayaka`).
Rollback does not undo migrations.

**Site down:**
```
sudo docker ps                                  # calebmayaka, postgres and caddy "Up"?
sudo docker logs --tail 50 calebmayaka          # app errors
sudo docker logs --tail 50 caddy                # HTTPS / proxy errors
cd /srv/apps/calebmayaka.com && sudo docker compose up -d
```

**Management commands:**
```
sudo docker exec -it calebmayaka python manage.py createsuperuser
sudo docker exec -it calebmayaka python manage.py changepassword <user>
sudo docker exec -it calebmayaka python manage.py purge_blog_visits
```

**Change a setting in .env:** edit `/srv/apps/calebmayaka.com/.env`, then `cd /srv/apps/calebmayaka.com && sudo docker compose up -d --force-recreate`.

## Backups

The nightly `backup-postgres.service` (~02:00) dumps every Postgres database, including `calebmayaka.dump`,
and also stores `calebmayaka.media.tgz` and `calebmayaka.env` → `/srv/backups/postgres/<date_time>/`. Kept 14 days.

Take one now: `sudo systemctl start backup-postgres.service`

Restore:
```
B=/srv/backups/postgres/<pick-one>
cd /srv/apps/calebmayaka.com && sudo docker compose stop app
sudo cat $B/calebmayaka.dump | sudo docker exec -i postgres pg_restore -U postgres -d calebmayaka --clean --if-exists --no-owner --role=calebmayaka
sudo tar -xzf $B/calebmayaka.media.tgz -C .     # only if uploads were lost
sudo docker compose start app
```

## DNS / HTTPS

Cloudflare DNS: `calebmayaka.com` and `www` are A records → `161.97.79.224`, proxied (orange cloud).
Other subdomains (uptime, jobs, 431, jarvis, elimisha) still go through the Cloudflare tunnel to the Windows server.
Cloudflare SSL/TLS mode must be **Full (strict)**. Caddy obtains and renews the Let's Encrypt certificate itself.
