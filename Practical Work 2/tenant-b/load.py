#!/usr/bin/env python3
"""Finite number of CPU workers, stopped cleanly with SIGTERM."""
import hashlib
import multiprocessing as mp
import os
import signal
import time


def worker(stop):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while not stop.is_set():
        hashlib.pbkdf2_hmac('sha256', b'cc-pz2-neighbor', b'fixed-lab-salt', 120000)


def main():
    count = int(os.environ.get('LOAD_WORKERS', '4'))
    if not 1 <= count <= 8:
        raise ValueError('LOAD_WORKERS must be between 1 and 8')
    stop = mp.Event()
    requested = [False]
    def request_stop(*_):
        requested[0] = True
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    children = [mp.Process(target=worker, args=(stop,)) for _ in range(count)]
    for child in children:
        child.start()
    print(f'Tenant-B: {count} CPU workers started', flush=True)
    failed = False
    while not requested[0]:
        if any(not child.is_alive() for child in children):
            failed = True
            break
        time.sleep(0.1)
    stop.set()
    for child in children:
        child.join(timeout=3)
        if child.is_alive():
            child.kill()
            child.join()
    print('Tenant-B: stopped', flush=True)
    if failed:
        raise SystemExit('A worker exited unexpectedly')


if __name__ == '__main__':
    main()
