"""
Servidor local del dashboard de licitaciones.

Uso:
    python data/scripts/servidor_feedback.py

Lo que hace:
- Sirve `dashboards/dashboard.html` en http://localhost:8765/
- Acepta POST /api/feedback con eventos individuales (like, dislike, fav, comentario, mensaje)
- Persiste TODO en `data/feedback_dashboard.json` (live JSON, sin merges manuales)
- Cero dependencias externas (sólo stdlib).

Cuando el usuario hace cualquier cambio en el navegador, el JS hace fetch('/api/feedback')
y el servidor escribe el cambio. En próximas sesiones de Claude, leer ese JSON
da el estado completo del feedback humano sin que el usuario tenga que exportar nada.
"""
import http.server
import json
import os
import socketserver
import threading
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DASHBOARD_PATH = ROOT / "dashboards" / "dashboard.html"
FEEDBACK_PATH = ROOT / "data" / "feedback_dashboard.json"
COLA_PROFUNDIZAR_PATH = ROOT / "data" / "cola_profundizar.json"
PORT = 8765

_lock = threading.Lock()


def _load_feedback():
    if FEEDBACK_PATH.exists():
        try:
            with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "_comment": "Feedback humano del dashboard de licitaciones — persistido automáticamente vía servidor_feedback.py.",
        "ultima_actualizacion": None,
        "likes_dislikes": {},
        "favoritos": [],
        "comentarios": {},
        "mensajes_generados": {},
        "eventos": [],
    }


def _save_feedback(fb):
    fb["ultima_actualizacion"] = datetime.now().isoformat(timespec="seconds")
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = FEEDBACK_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(fb, f, indent=2, ensure_ascii=False)
    os.replace(tmp, FEEDBACK_PATH)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # silenciar logs ruidosos
        if "/api/feedback" in args[0] if args else False:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.address_string()} - {format % args}")

    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard.html":
            if not DASHBOARD_PATH.exists():
                self.send_error(404, "dashboard.html no existe — regenera con generar_dashboard.py")
                return
            content = DASHBOARD_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)
            return
        if self.path == "/api/feedback":
            # Devuelve el JSON actual (útil para el frontend hidratar al cargar)
            with _lock:
                fb = _load_feedback()
            payload = json.dumps(fb, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/api/ping":
            payload = json.dumps({"ok": True, "ts": datetime.now().isoformat()}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path == "/api/cola_profundizar":
            with _lock:
                cola = self._load_cola()
            payload = json.dumps(cola, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_error(404, "Not found")

    def _load_cola(self):
        if COLA_PROFUNDIZAR_PATH.exists():
            try:
                with open(COLA_PROFUNDIZAR_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"_comment": "Cola de profundización", "items_pendientes": [], "items_procesados": [], "ultima_actualizacion": None}

    def _save_cola(self, cola):
        cola["ultima_actualizacion"] = datetime.now().isoformat(timespec="seconds")
        COLA_PROFUNDIZAR_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = COLA_PROFUNDIZAR_PATH.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cola, f, indent=2, ensure_ascii=False)
        os.replace(tmp, COLA_PROFUNDIZAR_PATH)

    def do_POST(self):
        if self.path == "/api/profundizar":
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length).decode("utf-8") if length else "{}"
                req = json.loads(body)
            except Exception as e:
                self.send_error(400, f"Bad JSON: {e}")
                return
            with _lock:
                cola = self._load_cola()
                # Evita duplicados
                if not any(p.get("hash") == req.get("hash") for p in cola["items_pendientes"]):
                    cola["items_pendientes"].append({
                        "hash": req.get("hash"),
                        "id_oficial": req.get("id_oficial"),
                        "url_oficial": req.get("url_oficial"),
                        "url_pliego_pcap": req.get("url_pliego_pcap"),
                        "url_pliego_ppt": req.get("url_pliego_ppt"),
                        "titulo": req.get("titulo"),
                        "encolado_at": datetime.now().isoformat(timespec="seconds"),
                    })
                self._save_cola(cola)
                pendientes = len(cola["items_pendientes"])
            payload = json.dumps({"ok": True, "pendientes": pendientes}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path != "/api/feedback":
            self.send_error(404, "Not found")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            evt = json.loads(body)
        except Exception as e:
            self.send_error(400, f"Bad JSON: {e}")
            return

        with _lock:
            fb = _load_feedback()
            tipo = evt.get("type")
            id_key = evt.get("id_key")
            value = evt.get("value")

            # Log de evento atómico
            fb["eventos"].append({
                "ts": datetime.now().isoformat(timespec="seconds"),
                "type": tipo,
                "id_key": id_key,
                "value": value,
            })
            # Limitamos eventos para que el archivo no crezca infinito
            if len(fb["eventos"]) > 2000:
                fb["eventos"] = fb["eventos"][-2000:]

            if tipo == "like" or tipo == "dislike":
                # value = 'like' | 'dislike' | None (toggle off)
                if value is None:
                    fb["likes_dislikes"].pop(id_key, None)
                else:
                    fb["likes_dislikes"][id_key] = value
            elif tipo == "favorito":
                # value = True | False
                if value:
                    if id_key not in fb["favoritos"]:
                        fb["favoritos"].append(id_key)
                else:
                    fb["favoritos"] = [x for x in fb["favoritos"] if x != id_key]
            elif tipo == "comentario_add":
                fb["comentarios"].setdefault(id_key, []).append({
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "texto": value or "",
                })
            elif tipo == "mensaje":
                campo = evt.get("campo", "email_previo")
                fb["mensajes_generados"].setdefault(id_key, {})[campo] = value or ""
            elif tipo == "bulk_import":
                # Para importar un JSON exportado previamente (manual)
                if "likes_dislikes" in value: fb["likes_dislikes"].update(value["likes_dislikes"] or {})
                if "favoritos" in value:
                    for k in (value["favoritos"] or []):
                        if k not in fb["favoritos"]:
                            fb["favoritos"].append(k)
                if "comentarios" in value:
                    for k, v in (value["comentarios"] or {}).items():
                        fb["comentarios"].setdefault(k, []).extend(v)
                if "mensajes_generados" in value:
                    for k, v in (value["mensajes_generados"] or {}).items():
                        fb["mensajes_generados"].setdefault(k, {}).update(v)
            else:
                self.send_error(400, f"Tipo de evento desconocido: {tipo}")
                return

            _save_feedback(fb)

        payload = json.dumps({"ok": True, "saved_at": fb["ultima_actualizacion"]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    print(f"Servidor de feedback en http://localhost:{PORT}/")
    print(f"Dashboard:   http://localhost:{PORT}/")
    print(f"Persistencia: {FEEDBACK_PATH}")
    print(f"Para parar: Ctrl+C")
    print("-" * 60)
    with ReusableTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
