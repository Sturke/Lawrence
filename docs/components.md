##  main.py
The application's entry point.
Its responsibility is to start Butler.

##  core/butler.py
Coordinates the Butler application.
It loads configuration, creates the Conversation and Brain, and manages the interaction loop.

##  core/brain.py
Represents Butler's intelligence layer.
The Brain currently contains simple response logic. It is intentionally designed so that a more capable AI model can eventually replace or extend this logic.

##  core/conversation.py
Stores the current conversation.
Conversation history is deliberately separated from the Brain so that memory can evolve independently of the intelligence layer.

##  config/butler.json
Contains Butler's configuration and identity.

####   memory/
Reserved for Butler's persistent memory system.
####    tools/
Reserved for capabilities Butler will eventually be able to use.
####    tests/
Contains automated tests that protect existing behavior as Butler evolves.

##  Design Principle
Butler's architecture should remain independent from any specific AI model.
The underlying model should be replaceable without requiring Butler's entire architecture to be rebuilt.