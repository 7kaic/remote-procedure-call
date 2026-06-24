from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .protocol import response, process
import json

class RPCHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        if self.path != "/rpc":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))

            res = process(self.dispatcher, data)

            if res is None:
                self.send_response(204)
                self.end_headers()
                return

            body = json.dumps(res).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            body = json.dumps(response(None, error="internal error")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)