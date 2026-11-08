#!/usr/bin/env python3
"""Sequential requests, validated bodies, raw CSV plus machine-readable summary."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8080/work')
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--warmup', type=int, default=5)
    parser.add_argument('--timeout', type=float, default=15)
    parser.add_argument('--iterations', type=int, default=120000)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.count < 1 or args.warmup < 0 or args.timeout <= 0:
        parser.error('Invalid count, warmup or timeout')
    expected = hashlib.pbkdf2_hmac('sha256', b'cc-pz2-work', b'fixed-lab-salt', args.iterations).hex()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request():
        with opener.open(args.url, timeout=args.timeout) as response:
            body = json.load(response)
            if response.status != 200 or body.get('tenant') != 'A' or body.get('iterations') != args.iterations or body.get('result') != expected:
                raise ValueError('Unexpected response or computation result')

    for _ in range(args.warmup):
        request()  # Fail before measurement if the service is not ready.
    rows, durations = [], []
    started = datetime.now(timezone.utc).isoformat()
    for number in range(1, args.count + 1):
        start, error = time.perf_counter(), ''
        try:
            request()
        except Exception as exc:
            error = f'{type(exc).__name__}: {exc}'
        elapsed = (time.perf_counter() - start) * 1000
        rows.append([number, round(elapsed, 3), not bool(error), error])
        if not error:
            durations.append(elapsed)
    summary = {
        'started_utc': started, 'url': args.url, 'count': args.count,
        'warmup': args.warmup, 'iterations': args.iterations,
        'timeout_seconds': args.timeout, 'successes': len(durations),
        'errors': args.count - len(durations),
        'mean_ms': round(statistics.mean(durations), 3) if durations else None,
        'max_ms': round(max(durations), 3) if durations else None,
        'note': 'Latency statistics include successful requests only; inspect errors separately.'
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix('.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['request', 'elapsed_ms', 'success', 'error'])
        writer.writerows(rows)
    output.with_suffix('.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    if summary['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
