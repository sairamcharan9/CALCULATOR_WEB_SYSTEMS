"""
Memory Commands Plugin
======================
Implements memory functionality described in the assignment README.
"""

from decimal import Decimal, InvalidOperation
from colorama import Fore
from app.commands import command

class CalculatorMemory:
    def __init__(self):
        self.storage = {}

    def store(self, name: str, val: Decimal):
        self.storage[name] = val
        
    def recall(self, name: str) -> Decimal:
        return self.storage.get(name)
        
    def list(self) -> dict:
        return self.storage
        
    def clear(self):
        self.storage.clear()

global_memory = CalculatorMemory()

@command("memory", "Manage memory. Usage: memory store <name> <val>, memory recall <name>, memory clear", "memory <action> [<name>] [<val>]")
def memory_command(calculator, *args) -> str:
    """Handles memory store, recall, list, and clear actions."""
    if not args:
        return "Usage: memory store <name> <val> | memory recall <name> | memory list | memory clear"
        
    action = args[0].lower()
    
    if action == "store":
        if len(args) != 3:
            return "Usage: memory store <name> <val>"
        name = args[1]
        try:
            val = Decimal(args[2])
            global_memory.store(name, val)
            msg = f"Stored {val} into memory '{name}'."
            print(f"{Fore.GREEN}{msg}")
            return msg
        except InvalidOperation:
            msg = f"Error: '{args[2]}' is not a valid number."
            print(f"{Fore.RED}{msg}")
            return msg
            
    elif action == "recall":
        if len(args) != 2:
            return "Usage: memory recall <name>"
        name = args[1]
        val = global_memory.recall(name)
        if val is None:
            msg = f"Error: Memory '{name}' not found."
            print(f"{Fore.RED}{msg}")
            return msg
        msg = f"Recalled {name}: {val}"
        print(f"{Fore.GREEN}{msg}")
        return msg
        
    elif action == "list":
        mem = global_memory.list()
        if not mem:
            msg = "Memory is empty."
            print(f"{Fore.YELLOW}{msg}")
            return msg
        lines = ["=== Memory ==="]
        for k, v in mem.items():
            lines.append(f"  {k}: {v}")
        result = "\n".join(lines)
        print(f"{Fore.BLUE}{result}")
        return result
        
    elif action == "clear":
        global_memory.clear()
        msg = "Memory cleared."
        print(f"{Fore.GREEN}{msg}")
        return msg
        
    else:
        msg = f"Error: Unknown memory action '{action}'."
        print(f"{Fore.RED}{msg}")
        return msg
