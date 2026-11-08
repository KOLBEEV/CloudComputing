#!/usr/bin/env python3
"""Fixed CPU work per request; no third-party packages."""
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

ITERATIONS = int(os.environ.get('WORK_ITERATIONS', '120000'))
if not 1000 <= ITERATIONS <= 10000000:
    raise ValueError('WORK_ITERATIONS must be between 1000 and 10000000')


def compute():
    return hashlib.pbkdf2_hmac('sha256', b'cc-pz2-work', b'fixed-lab-salt', ITERATIONS).hex()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            payload = {'tenant': 'A', 'status': 'ok'}
        elif self.path == '/work':
            payload = {'tenant': 'A', 'iterations': ITERATIONS, 'result': compute()}
        else:
            self.send_error(404)
            return
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    print(f'Tenant-A port={port} iterations={ITERATIONS}', flush=True)
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()
