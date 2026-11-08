#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
image=coursehub-pz3:1
container=cc-pz3-coursehub
volume=cc-pz3-coursehub-data
label=coursehub.lab
backup=coursehub-backup.sqlite
api=http://127.0.0.1:8080/registrations

die() {
    printf '%s\n' "$*" >&2
    exit 1
}

owned_container() {
    local owner
    owner=$(docker container inspect -f "{{ index .Config.Labels \"$label\" }}" "$container") ||
        die "Lab container is missing."
    [[ "$owner" == pz3 ]] || die "Container name is in use outside the lab."
}

owned_volume() {
    local owner
    owner=$(docker volume inspect -f "{{ index .Labels \"$label\" }}" "$volume") ||
        die "Lab volume is missing."
    [[ "$owner" == pz3 ]] || die "Volume name is in use outside the lab."
}

start() {
    docker volume create --label "$label=pz3" "$volume" >/dev/null
    owned_volume
    docker run --pull=never -d --name "$container" --label "$label=pz3" \
        -p 127.0.0.1:8080:8080 --mount "type=volume,src=$volume,dst=/data" "$image"
    for ((attempt=0; attempt<30; attempt++)); do
        if curl --noproxy '*' -fsS --max-time 1 "$api" >/dev/null 2>&1; then
            return
        fi
        sleep 0.2
    done
    docker logs "$container" >&2
    die "CourseHub did not become ready."
}

stop() {
    if docker container inspect "$container" >/dev/null 2>&1; then
        owned_container
        docker stop "$container" >/dev/null
        docker rm "$container" >/dev/null
    fi
}

case "${1:-help}" in
    help|-h|--help)
        cat <<'EOF'
Usage: bash lab.sh COMMAND
  up                 Start CourseHub (create the lab volume if needed)
  status             Show the current container ID and mounted volume
  add A|B|C          Register a synthetic student for CC101 through HTTP
  list               List registrations with HTTP status
  recreate           Replace the container and retain the volume
  backup            Create and check a SQLite backup outside the volume
  lose-volume      Stop CourseHub and remove the dedicated lab volume
  restore           Restore the backup into an existing lab volume with CourseHub stopped
  down               Stop and remove the container, keeping volume and backup
EOF
        ;;
    up) start ;;
    status)
        owned_container
        docker container inspect -f 'container_id={{.Id}} running={{.State.Running}} {{range .Mounts}}{{if eq .Destination "/data"}}volume={{.Name}}{{end}}{{end}}' "$container"
        ;;
    add)
        case "${2:-}" in A|B|C) ;; *) die 'Usage: bash lab.sh add A|B|C' ;; esac
        curl --noproxy '*' -fsS --max-time 5 -H 'Content-Type: application/json' \
            --data "{\"student_id\":\"$2\",\"course_id\":\"CC101\"}" \
            -w '\nHTTP %{http_code}\n' "$api"
        ;;
    list) curl --noproxy '*' -fsS --max-time 5 -w '\nHTTP %{http_code}\n' "$api" ;;
    recreate)
        owned_volume
        stop
        start
        ;;
    backup)
        owned_container
        temp_backup=$(mktemp .coursehub-backup.XXXXXX)
        trap 'rm -f -- "$temp_backup"' EXIT
        docker exec "$container" python database.py backup /data/coursehub.sqlite > "$temp_backup"
        mv -- "$temp_backup" "$backup"
        printf 't_backup=%s\npath=%s/%s\nbytes=%s\nSQLite integrity_check=ok\n' \
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$PWD" "$backup" "$(wc -c < "$backup")"
        sha256sum "$backup"
        ;;
    lose-volume)
        [[ -s "$backup" ]] || die "Create a backup before removing the lab volume."
        owned_volume
        stop
        docker volume rm "$volume"
        ;;
    restore)
        [[ -s "$backup" ]] || die "Backup file is missing."
        owned_volume
        if docker container inspect "$container" >/dev/null 2>&1; then
            die "Run bash lab.sh down before restoring."
        fi
        docker run --pull=never --rm -i --network none \
            --mount "type=volume,src=$volume,dst=/data" "$image" \
            python database.py restore /data/coursehub.sqlite < "$backup"
        ;;
    down) stop ;;
    *) die "Unknown command. Run bash lab.sh help." ;;
esac
