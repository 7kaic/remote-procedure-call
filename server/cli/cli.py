from .commands import COMMANDS

def run_cli(server):
    current_client = None

    while True:
        try:   
            parts = input(">> ").strip().split()
            if not parts:
                continue

            cmd = COMMANDS.get(parts[0])
            if not cmd:
                print("unknown command (type 'help')")
                continue

            current_client = cmd(server, parts[1:], current_client)

        except KeyboardInterrupt:
             print("\nuse 'exit' to quit")
        except Exception as e:
            print(f"error: {e}")  
