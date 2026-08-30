import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from brain import Brain
from conversation import Conversation


def test_brain_remembers_conversation():
    config = {
        "identity": {
            "role": "personal AI assistant",
            "description": "A trusted gatekeeper.",
            "principles": [
                "Be helpful",
                "Protect the user's interests"
            ]
        }
    }

    conversation = Conversation()
    brain = Brain(config, conversation)

    brain.respond("My name is Burke.")
    response = brain.respond("What did I just tell you?")

    assert "My name is Burke." in response