import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from brain import Brain


def test_brain_remembers_conversation():
    config = {
        "identity": {
            "role": "personl AI assistant",
            "description": "A trusted gatekeeper.",
            "Principles": [
                "Be helpful, honest, and harmless.",
                "Respect user privacy and confidentiality.",
                "Provide accurate and relevant information.",
                "Avoid engaging in harmful or malicious activities.",
                "Protect the user's data and personal information.",
                "Protect the user's interests."
            ]
        }
    }

    brain = Brain(config)

    brain.respond("My name is Burke.")
    response = brain.respond("What did I just tell you?")

    assert "My name is Burke." in response 

    