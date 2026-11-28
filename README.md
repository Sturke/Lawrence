# Butler

Butler is a personal AI assistant designed to act as a trusted gatekeeper between the user and their digital world.

## Core Principle

Butler should not merely answer questions.

Butler should understand the user's intent, determine what is appropriate and permitted, and help execute tasks on the user's behalf.

## Initial Goals

- Understand natural-language requests
- Maintain useful memory
- Protect the user's information
- Respect permissions and boundaries
- Use tools when necessary
- Ask before taking consequential actions
- Learn from corrections and feedback
- Keep its behavior understandable and controllable

## Development Philosophy

Build Butler one capability at a time.

Do not train a custom AI model yet.

The underlying AI model should initially be replaceable. Butler's identity, memory, permissions, tools, and decision-making architecture should belong to Butler itself.

## Status

Early development. Project Butler is the repository/project name; Lawrence is the personal assistant being developed.

See [Current Project Status](docs/project_status.md) for the verified checkpoint,
current test results, remaining work, and session handoff. Bounded Improved
Retrieval v1B is complete; see the roadmap for supported behavior and limits.

Start each development session with [AGENTS.md](AGENTS.md) and the
[Project Accountability Protocol](docs/accountability.md). When a change is
ready, follow the [pull request review checklist](docs/accountability.md#pull-request-review-checklist).
See also [Roadmap](docs/roadmap.md), [Architecture](docs/architecture.md),
and [Architectural Decisions](docs/decisions.md).

## Development setup

From this checkout's repository root, use Python 3.11 or newer to create its
local environment and install the development dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

For optional live DKIM verification, install `requirements-dkim.txt` in the
same environment. Run the full suite with `.venv/bin/python -m pytest -q`.
