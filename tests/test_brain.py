from memory.personal import PersonalMemoryStore
from core.brain import Brain
from core.conversation import Conversation


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



def test_brain_can_recall_personal_memory(tmp_path):
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

    database = tmp_path / "personal.sqlite3"
    memory = PersonalMemoryStore(database)
    memory.save_memory(content="My favorite college is UIUC.")

    conversation = Conversation()
    brain = Brain(config, conversation, memory)

    response = brain.respond("What do you remember about me?")

    assert "My favorite college is UIUC." in response


def test_brain_saves_explicitly_approved_memory(tmp_path):
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

    database = tmp_path / "personal.sqlite3"
    memory = PersonalMemoryStore(database)

    conversation = Conversation()
    brain = Brain(config, conversation, memory)

    response = brain.respond("remember: My favorite college is UIUC.")

    memories = memory.get_memories()

    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite college is UIUC."
    assert "remembered" in response.lower()

def test_brain_can_recall_a_specific_personal_memory(tmp_path):
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

    database = tmp_path / "personal.sqlite3"
    memory = PersonalMemoryStore(database)

    memory.save_memory(content="My favorite college is UIUC.")
    memory.save_memory(content="My favorite coffee is Sumatra.")

    conversation = Conversation()
    brain = Brain(config, conversation, memory)

    response = brain.respond("What is my favorite college?")

    assert "UIUC" in response
    assert "Sumatra" not in response
