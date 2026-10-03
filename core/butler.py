import json
from pathlib import Path

from core.brain import Brain
from core.conversation import Conversation
from memory.personal import PersonalMemoryStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = PROJECT_ROOT / "config" / "butler.json"
PERSONAL_MEMORY_FILE = PROJECT_ROOT / "data" / "personal.sqlite3"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


def main():
    config = load_config()
    conversation = Conversation()
    memory = PersonalMemoryStore(PERSONAL_MEMORY_FILE)
    brain = Brain(config, conversation, memory)
    print(f"{config['name']} is starting...")
    print(f"Version: {config['version']}")
    print(f"Mode: {config['mode']}")
    print("Butler is alive.")
    print()

    while True:
        user_input = input("You: ")

        if user_input.lower() in {"exit", "quit"}:
            print("Butler: Goodbye.")
            break

        if user_input.strip():
            print(f"Butler: {brain.respond(user_input)}")

if __name__ == "__main__":
    main()
