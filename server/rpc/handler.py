from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .protocol import response, process
import json

class RPCHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def write_json(self, body: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def write_error(self, code: int):
        self.send_response(code)
        self.end_headers()

    def do_POST(self):
        if self.path != "/rpc":
            self.write_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            res = process(self.server.dispatcher, data)

            if res is None:
                self.write_error(204)
                return
            
            self.write_json(json.dumps(res).encode())

        except Exception as e:
            self.write_json(json.dumps(response(None, error="internal error")).encode())
    
    def do_GET(self):
        if not self.path.startswith("/download/"):
            self.write_error(404)
            return
        
        name = self.path.removeprefix("/download/")

        try:
            path = self.server.app.get_download(name)
            size = path.stat().st_size

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.end_headers()

            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)

        except Exception as e:
            self.write_error(500)