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

def test_brain_can_recall_memory_from_a_natural_question(tmp_path):
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

    response = brain.respond("What coffee do I like?")

    assert "Sumatra" in response
    assert "UIUC" not in response

def test_brain_prefers_the_most_relevant_personal_memory(tmp_path):
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

    response = brain.respond("What is my favorite coffee?")

    assert "Sumatra" in response
    assert "UIUC" not in response

def test_brain_recalls_college_without_specific_question_rule(tmp_path):
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

    response = brain.respond("Where did I attend college?")

    assert "UIUC" in response
    assert "Sumatra" not in response

def test_brain_stores_favorite_as_structured_memory(tmp_path):
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

    response = brain.respond(
        "remember: My favorite coffee is Sumatra."
    )

    memories = memory.get_memories()

    assert response == "Remembered: My favorite coffee is Sumatra."
    assert len(memories) == 1
    assert memories[0]["content"] == "My favorite coffee is Sumatra."
    assert memories[0]["category"] == "preference"
    assert memories[0]["subject"] == "coffee"
    assert memories[0]["value"] == "Sumatra"

def test_brain_updates_existing_structured_preference(tmp_path):
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

    brain.respond(
        "remember: My favorite coffee is Sumatra."
    )

    brain.respond(
        "remember: My favorite coffee is Ethiopian Yirgacheffe."
    )

    memories = memory.get_memories()

    assert len(memories) == 1
    assert memories[0]["category"] == "preference"
    assert memories[0]["subject"] == "coffee"
    assert memories[0]["value"] == "Ethiopian Yirgacheffe"
    assert memories[0]["content"] == (
        "My favorite coffee is Ethiopian Yirgacheffe."
    )