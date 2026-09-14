# Importing a saved email

Gatekeeper can import one local `.eml` file into its existing message store.
This does not connect to an inbox, send email, or classify messages.
`tests/fixtures/sample.eml` contains a fictional message using example.com
addresses, suitable for repeatable tests and manual demonstrations.

From the repository root, run:

```bash
.venv/bin/python -m tools.gatekeeper_import tests/fixtures/sample.eml
```

The command creates the parent folder if necessary and saves the message in
`~/Library/Application Support/Butler/gatekeeper.sqlite3`. It reports the local
message ID and database path. To use a separate practice database:

```bash
.venv/bin/python -m tools.gatekeeper_import tests/fixtures/sample.eml --database /tmp/butler-demo/gatekeeper.sqlite3
```

The `/tmp` example is temporary practice storage and may be cleared by the
system. Use the default Application Support location for persistent storage.

The importer decodes the sender and subject headers and selects the plain-text
body, including in multipart emails. Attachments are ignored. HTML-only emails
are rejected; HTML is never rendered and remote content is never fetched.
Missing subjects and empty text bodies are allowed. A From header and a valid
Date header with a known timezone are required. Invalid input produces an error
without inserting a message.

For this initial importer, `received_at` stores the email's Date header converted
to ISO 8601. This is the sender-provided date, not verified arrival time. A future
live inbox adapter should provide actual receipt metadata.

Repeated imports create separate rows, even when Message-ID is identical.
Deduplication is deferred until provider/message identity is added to the schema.
The existing storage schema and conversation loop are unchanged.

Run `.venv/bin/python -m pytest -q` for the full suite. Tests use temporary
databases; they do not add sample messages to your persistent database.
