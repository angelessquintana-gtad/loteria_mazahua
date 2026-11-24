#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p deploy/backups
exec 9>deploy/backups/.backup.lock
flock -n 9 || { echo "Ya hay una copia en curso" >&2; exit 1; }
COMPOSE=(docker compose --env-file deploy/.env)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
dest="deploy/backups/$stamp"
mkdir "$dest"
restart_app() { "${COMPOSE[@]}" start app >/dev/null; }
trap restart_app EXIT
# Pausa escrituras durante la copia para conservar coherencia entre BD y audios.
"${COMPOSE[@]}" stop app
"${COMPOSE[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysqldump -u"$MYSQL_USER" --single-transaction --no-tablespaces --set-gtid-purged=OFF "$MYSQL_DATABASE"' | gzip > "$dest/database.sql.gz"
"${COMPOSE[@]}" run --rm --no-deps -T app tar -C /data -czf - uploads > "$dest/uploads.tar.gz"
tar -czf "$dest/catalogo.tar.gz" catalogo
"${COMPOSE[@]}" config --images > "$dest/images.txt"
(cd "$dest" && sha256sum ./*.gz > SHA256SUMS)
touch "$dest/COMPLETO"
echo "Copia completa: $dest. Descárgala fuera de la VPS."
# Solo borrar copias completas generadas por este script y con más de 7 días.
find deploy/backups -mindepth 2 -maxdepth 2 -name COMPLETO -mtime +7 -print0 | while IFS= read -r -d '' marker; do
    carpeta=$(dirname "$marker")
    [[ $(basename "$carpeta") =~ ^[0-9]{8}T[0-9]{6}Z$ ]] && rm -rf -- "$carpeta"
done
