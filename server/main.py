from core.server import Server
from core.dispatcher import Dispatcher
from rpc.handler import RPCHandler
from cli.cli import run_cli

from http.server import ThreadingHTTPServer
import threading

def main():
    server = Server()

    dispatcher = Dispatcher()
    dispatcher.register("identify", server.identify)
    dispatcher.register("beacon", server.beacon)
    dispatcher.register("task_result", server.task_result)
    
    http = ThreadingHTTPServer(("0.0.0.0", 8000), RPCHandler)
    http.app = server
    http.dispatcher = dispatcher

    threading.Thread(target=run_cli, args=(server,), daemon=True).start()
    http.serve_forever()

if __name__ == "__main__":
    main()