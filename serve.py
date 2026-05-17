"""Servidor local mínimo para abrir los dashboards desde el móvil/otro navegador.

Uso:
    python serve.py            # puerto 8000 por defecto
    python serve.py 9000       # puerto custom
"""
import http.server
import socketserver
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        # silenciar logs verbose
        pass

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Sirviendo {ROOT} en http://localhost:{PORT}")
        print(f"  Dashboard:        http://localhost:{PORT}/dashboards/dashboard.html")
        print(f"  Control:          http://localhost:{PORT}/dashboards/control.html")
        print("Ctrl+C para parar.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nParando servidor.")
