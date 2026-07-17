from .commands import COMMANDS

def run_cli(server):
    current_client = None

    while True:
        try:
            prompt = f"[{current_client[:8]}]>> " if current_client else ">> "
            parts = input(prompt).strip().split()
            if not parts:
                continue

            cmd, _ = COMMANDS.get(parts[0], (None, None))
            if not cmd:
                print("unknown command (type 'help')")
                continue

            current_client = cmd(server, parts[1:], current_client)

        except KeyboardInterrupt:
             print("\nuse 'exit' to quit")
        except Exception as e:
            print(f"error: {e}")  
