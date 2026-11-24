#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
source_dir=${1:?Uso: bash deploy/restore.sh deploy/backups/FECHA}
[[ -f "$source_dir/COMPLETO" ]] || { echo "La copia no está completa" >&2; exit 1; }
(cd "$source_dir" && sha256sum -c SHA256SUMS)
read -r -p 'Esto sustituye la base y uploads. Escribe RESTAURAR: ' confirm
[[ "$confirm" == RESTAURAR ]] || exit 1
COMPOSE=(docker compose --env-file deploy/.env)
"${COMPOSE[@]}" stop app
gzip -dc "$source_dir/database.sql.gz" | "${COMPOSE[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -u"$MYSQL_USER" "$MYSQL_DATABASE"'
# El volumen mantiene el usuario no-root de la aplicación.
"${COMPOSE[@]}" run --rm --no-deps -T app python -c 'import shutil; from pathlib import Path; p=Path("/data/uploads"); [shutil.rmtree(x) if x.is_dir() else x.unlink() for x in p.iterdir()]'
cat "$source_dir/uploads.tar.gz" | "${COMPOSE[@]}" run --rm --no-deps -T app tar -C /data -xzf -
tar -xzf "$source_dir/catalogo.tar.gz"
"${COMPOSE[@]}" build app migrate
"${COMPOSE[@]}" run --rm migrate
"${COMPOSE[@]}" up -d app caddy
echo "Restauración completada. Verifica /api/ready y una tarjeta con audio."
