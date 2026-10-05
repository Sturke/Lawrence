##  main.py
The application's entry point.
Its responsibility is to start Butler.

##  core/butler.py
Coordinates the Butler application.
It loads configuration, creates the Conversation, PersonalMemoryStore, and Brain, and manages the interaction loop. Personal memory is stored in `data/personal.sqlite3`.

##  core/brain.py
Represents Butler's intelligence layer.
The Brain currently contains simple response logic. It is intentionally designed so that a more capable AI model can eventually replace or extend this logic.

##  core/conversation.py
Stores the current conversation.
Conversation history is deliberately separated from the Brain so that memory can evolve independently of the intelligence layer.

##  config/butler.json
Contains Butler's configuration and identity.

####   memory/
Contains SQLite stores for personal memory (`personal.py`) and Gatekeeper messages (`gatekeeper.py`). Personal memory supports explicit `remember:` requests, structured fields, updates, legacy migration, provenance, and ranked retrieval. Gatekeeper storage remains separate from the interaction loop; see [storage](gatekeeper-storage.md) and [saved-email import](gatekeeper-import.md).
####    tools/
Contains the local saved-email importer (`gatekeeper_import.py`). Broader tool permissions and execution remain future work.
####    verification/
Contains `evidence.py`, the Evidence & Verification Foundation v0.1 models. These models are not yet connected to Brain response generation.
####    tests/
Contains automated tests that protect existing behavior as Butler evolves.

##  Design Principle
Butler's architecture should remain independent from any specific AI model.
The underlying model should be replaceable without requiring Butler's entire architecture to be rebuilt.