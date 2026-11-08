#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
A=cc-pz2-tenant-a
B=cc-pz2-tenant-b
IA=cc-pz2/tenant-a:1.0
IB=cc-pz2/tenant-b:1.0
LABEL=cc-pz2-lab-v1
fail() { echo "ERROR: $*" >&2; exit 1; }
command -v docker >/dev/null || fail 'Install Docker Engine in the Linux VM.'
command -v python3 >/dev/null || fail 'Install python3 in the Linux VM.'
docker info >/dev/null 2>&1 || fail 'Docker daemon unavailable or access denied. See README.'
owned() {
  [[ "$(docker inspect -f '{{index .Config.Labels "edu.cc-pz2"}}' "$1" 2>/dev/null)" == "$LABEL" ]] || fail "Container $1 is absent or belongs to another project."
}
running() { owned "$1"; [[ "$(docker inspect -f '{{.State.Running}}' "$1")" == true ]] || fail "$1 is not running."; }
status() {
  owned "$A"; owned "$B"
  docker inspect -f '{{.Name}} running={{.State.Running}} cpuset={{.HostConfig.CpusetCpus}} NanoCpus={{.HostConfig.NanoCpus}} period={{.HostConfig.CpuPeriod}} quota={{.HostConfig.CpuQuota}}' "$A" "$B"
  docker stats --no-stream "$A" "$B"
}
case "${1:-help}" in
 build)
  docker build -t "$IA" tenant-a
  docker build -t "$IB" tenant-b
  ;;
 up)
  for name in "$A" "$B"; do
    if docker inspect "$name" >/dev/null 2>&1; then fail "$name already exists. Use 'bash lab.sh down' first."; fi
  done
  CPU="${LAB_CPU:-$(python3 -c 'import os; print(min(os.sched_getaffinity(0)))')}"
  [[ "$CPU" =~ ^[0-9]+$ ]] || fail 'LAB_CPU must be one logical CPU number.'
  docker image inspect "$IA" "$IB" >/dev/null || fail 'Run build or import first.'
  common=(--label "edu.cc-pz2=$LABEL" --cpuset-cpus "$CPU" --memory 256m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --log-opt max-size=2m --log-opt max-file=2)
  docker run -d --name "$A" "${common[@]}" -p 127.0.0.1:8080:8080 "$IA"
  docker create --name "$B" "${common[@]}" --network none "$IB"
  python3 - <<'PY'
import json, time, urllib.request
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for attempt in range(50):
    try:
        with opener.open('http://127.0.0.1:8080/health', timeout=1) as response:
            assert json.load(response) == {'tenant': 'A', 'status': 'ok'}
        print('Ready. Tenant-A: http://127.0.0.1:8080/work; Tenant-B is stopped.')
        break
    except Exception:
        time.sleep(0.2)
else:
    raise SystemExit('Tenant-A did not start; inspect docker logs cc-pz2-tenant-a')
PY
  echo "Both tenants pinned to CPU $CPU."
  ;;
 load-on) running "$A"; owned "$B"; docker start "$B" ;;
 load-off) owned "$B"; docker stop -t 10 "$B" ;;
 limit) owned "$B"; docker update --cpu-period 100000 --cpu-quota 25000 "$B" ;;
 unlimit) owned "$B"; docker update --cpu-period 100000 --cpu-quota -1 "$B" ;;
 status) status ;;
 measure)
  running "$A"; owned "$B"
  name="${2:-}"
  [[ "$name" =~ ^[a-zA-Z0-9_-]+$ ]] || fail 'Example: bash lab.sh measure baseline-1'
  stamp="$(date -u +%Y%m%dT%H%M%S)-$$"
  target="results/${name}-${stamp}"
  mkdir -p results
  docker inspect "$A" "$B" > "${target}-before.json"
  status | tee "${target}-status.txt"
  rc=0
  python3 benchmark.py --output "$target" | tee "${target}-summary.txt" || rc=$?
  docker inspect "$A" "$B" > "${target}-after.json"
  for container in "$A" "$B"; do
    if [[ "$(docker inspect -f '{{.State.Running}}' "$container")" == true ]]; then
      docker exec "$container" sh -c 'cat /sys/fs/cgroup/cpu.stat 2>/dev/null || true' > "${target}-${container}-cpu-stat.txt"
    fi
  done
  echo "Saved: ${target}.*"
  exit "$rc"
  ;;
 down)
  for container in "$A" "$B"; do
    if docker inspect "$container" >/dev/null 2>&1; then owned "$container"; docker rm -f "$container"; fi
  done
  ;;
 export) docker save -o cc-pz2-images.tar "$IA" "$IB" ;;
 import) [[ -f cc-pz2-images.tar ]] || fail 'Place cc-pz2-images.tar in this directory.'; docker load -i cc-pz2-images.tar ;;
 *) echo 'Usage: bash lab.sh build|up|load-on|load-off|limit|unlimit|status|measure NAME|down|export|import' ;;
esac
