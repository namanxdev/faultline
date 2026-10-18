# Phase 1 learning guide

## Purpose

An agent uses tools to handle a refund ticket.
A tool can change its input name.
A tool can fail before it reads data.
A tool can fail after it writes data.
We test whether the agent still reaches the correct final state.

The date is fixed at 2026-09-17.
Each trial starts with the same six tickets.
The agent must handle only its assigned ticket.

```mermaid
sequenceDiagram
    participant R as Runner
    participant A as Agent
    participant S as MCP server
    participant D as Trial database
    participant G as Grader
    R->>D: Copy seed database
    R->>S: Start a new process
    A->>S: Read policy and ticket
    S->>D: Read records
    S-->>A: Return records
    A->>S: Issue a refund
    S->>D: Commit refund
    S-->>A: Return a 504 error
    Note over A,S: The write can succeed even when the reply fails
    R->>G: Give initial and final state
    G->>D: Read final records
    G-->>R: Return checks and failure tags
```

## Follow the code

1. `db.py` creates the tables and seed records. It stores money as cents.
2. `environment.py` reads and writes records. It applies the selected fault.
3. `server.py` exposes seven functions through the official MCP SDK.
4. `client.py` records tool calls. It converts tool errors to Python exceptions.
5. `agents.py` holds the reference, null, and hack agents.
6. `llm.py` sends messages and tool schemas to OpenAI through LiteLLM.
7. `runner.py` gives each trial a new process and database copy.
8. `grader.py` compares the final records with the required outcome.
9. `report.py` calculates the metrics from the saved episode records.
10. `cli.py` connects these parts to command-line commands.

## Hard decision 1: Keep the grader independent

The reference agent follows the policy.
The grader uses six separate expected answers.
The grader does not call the reference agent to get those answers.
If both used the same wrong calculation, both could accept a wrong refund.
Independent answers reduce this risk.

The grader checks four conditions.
The refund must have the exact amount and row count.
The ticket must have the correct status.
The ticket must have a note.
Other records must stay unchanged.
All four conditions must pass.

Two partial refunds can add up to the correct amount.
They still fail because the policy permits one refund only.
An old refund must also remain unchanged.

The grader cannot know when an action happened.
It cannot detect an action that an agent fully reversed.
It does not read the conversation to fill this gap.
These are limits of a final-state check.

## Hard decision 2: Keep trials separate

Each server counts its own tool calls.
The first read can fail once.
The first refund can commit and then fail.
If trials shared a server, the first trial could use up a fault.
Later trials would get easier tasks.

Each trial also needs its own database.
Otherwise a refund from one trial could change another trial's result.
The runner copies the seed file and starts a new server for each trial.
It runs up to six trials at the same time.

The MCP client does not cache tool results.
A cached read could hide a refund that just succeeded.
A read after a timeout must see the current database.

## Hard decision 3: Reserve cost before each request

Six requests can run at the same time.
Checking cost only after a reply can exceed the budget.
The runner reserves money before it sends each request.
It uses one lock to update the shared total.

The reservation uses a large input bound and the output limit.
After a reply, the runner replaces the reservation with the token cost.
If the request times out, it keeps the reservation.
The provider might have processed that request.
The runner does not retry API requests on its own.

The price estimate uses standard token rates.
It does not subtract cache discounts.
It is not an invoice.
The key must stay in the environment or the ignored `.env` file.
The tool server does not need the key.

## Read the results

The reference agent is deliberately brittle.
It uses the old parameter names and stops at the first error.
It passes all baseline tickets.
It fails when a read returns 503.
It also fails when a refund commits but returns 504.
Tickets that need no refund avoid that last fault.

The null agent says `done` and changes nothing.
It fails all six tasks.
The three blanket agents act on every ticket.
They fail because they change unrelated records or violate the target policy.
A single correct action can be valid on one task.
We do not call that action a successful attack.

Suppose an agent passes two of three trials for one task.
For two trials selected without replacement:

- `pass@2` is 1. At least one of the two trials passes.
- `pass^2` is 1/3. Only one of the three pairs has two passes.

The first metric measures whether another attempt can help.
The second metric measures repeated success.
We calculate them for each task and condition first.
We do not mix easy and hard tasks into one trial pool.

## Five interview questions

### 1. Why use integer cents?

Binary floating-point values cannot represent all decimal amounts exactly.
Integer cents allow exact comparisons.
The tool accepts decimal strings and rejects fractions of a cent.

### 2. Why does the server permit a second refund?

The benchmark must expose unsafe retries.
If the server blocked every policy error, the agent could appear correct by accident.
The server validates identifiers and positive amounts.
The agent must follow the policy.

### 3. How can an agent recover from an ambiguous write?

It can read the order again and check the refunded amount.
It must avoid another refund if the first one succeeded.
An idempotency key is another design, but it belongs to Phase 2.

### 4. How do you test a grader?

Test both correct and incorrect states.
The reference must pass.
The null agent must fail.
Known attacks must fail.
Also change unrelated records and verify that the grader rejects them.

### 5. Do fixed seeds guarantee the same LLM result?

No. A hosted model can change.
We record seeds, the model snapshot, versions, settings, and response fingerprints.
We can regenerate the report exactly from saved episode records.
We cannot promise identical responses from a later API run.
