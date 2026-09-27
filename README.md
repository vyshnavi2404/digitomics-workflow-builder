# Digitomics Conversational Workflow Builder

A conversational workflow planning system that turns natural-language automation requests into validated, structured workflow graphs.

Built for the Digitomics AI Engineer assignment.

---

## Problem

Users should be able to describe an automation naturally without needing to know the exact workflow schema.

For example:

> "Every Monday at 9 AM, send the sales report to #sales."

The system must understand the request, identify the workflow type, determine which required information is missing, ask targeted clarification questions, and generate a structured workflow only when the specification is complete.

The key requirement is:

**Never guess missing information.**

---

## Core Design

The system separates language understanding from workflow correctness.

### 1. System Architecture Flowchart

```text
                         ┌─────────────────────────┐
                         │          User           │
                         │ Natural-language        │
                         │ automation request      │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     Intent Gateway      │
                         │                         │
                         │ Request / Update /      │
                         │ Ambiguous / Out-of-     │
                         │ Scope                   │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Workflow Type Resolver  │
                         │                         │
                         │ Invoice / Database /    │
                         │ Scheduled               │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Requirement Extraction  │
                         │                         │
                         │ Values + Evidence +     │
                         │ Confidence              │
                         └────────────┬────────────┘
                                      │
                                      ▼
                 ┌──────────────────────────────────────┐
                 │          Requirement Graph           │
                 │                                      │
                 │ Values                               │
                 │ Evidence                             │
                 │ Confidence                           │
                 │ Status                               │
                 │ Dependencies                         │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────┐
                         │ Deterministic           │
                         │ Clarification Policy    │
                         │                         │
                         │ Ask missing /           │
                         │ ambiguous requirements  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                              ┌───────────────┐
                              │   Complete?   │
                              └───────┬───────┘
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                        No                        Yes
                         │                         │
                         ▼                         ▼
                 ┌─────────────────┐    ┌──────────────────────┐
                 │ Ask the user    │    │ Completeness +       │
                 │ for information │    │ Validation           │
                 └────────┬────────┘    └──────────┬───────────┘
                          │                        │
                          └──────► User ◄─────────┘
                                                   │
                                                   ▼
                                      ┌────────────────────────┐
                                      │   Workflow Compiler    │
                                      └────────────┬───────────┘
                                                   │
                                                   ▼
                                      ┌────────────────────────┐
                                      │ Structured Workflow    │
                                      │ JSON / Graph           │
                                      └────────────────────────┘
```

### Why this architecture?

A simple implementation could look like:

```text
Prompt → LLM → JSON
```

However, that approach can allow the model to silently invent missing values.

This project instead uses:

```text
Natural Language
      ↓
Interpretation
      ↓
Structured Requirements
      ↓
Deterministic State
      ↓
Deterministic Completeness Check
      ↓
Validated Workflow
```

The LLM is responsible for **understanding language**.

Deterministic application code is responsible for:

- required-field validation
- dependencies
- ambiguity handling
- clarification ordering
- workflow completeness
- final compilation
- structural validation

This separation makes the system predictable and testable.

---

## Supported Workflow Types

The current implementation demonstrates three workflow families.

### 2. Workflow-Type Flowchart

```text
                         ┌─────────────────────┐
                         │    User Request     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Workflow Type       │
                         │ Resolver            │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │ Invoice          │   │ Database         │   │ Scheduled        │
   │ Notification     │   │ Notification     │   │ Report           │
   └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
            │                      │                      │
            ▼                      ▼                      ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │ Trigger Source   │   │ Database         │   │ Schedule         │
   │ Gmail / Outlook  │   │ PostgreSQL /     │   │                  │
   │                  │   │ MySQL / SQL      │   │                  │
   │                  │   │ Server           │   │                  │
   └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
            │                      │                      │
            ▼                      ▼                      ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │ Mailbox / Folder │   │ Table            │   │ Action           │
   └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
            │                      │                      │
            ▼                      │                      │
   ┌──────────────────┐            │                      │
   │ Invoice          │            │                      │
   │ Condition        │            │                      │
   └────────┬─────────┘            │                      │
            │                      │                      │
            ▼                      ▼                      ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │ Notification     │   │ Notification     │   │ Recipient        │
   │ Channel          │   │ Channel          │   │                  │
   └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
            │                      │                      │
            ▼                      ▼                      │
   ┌──────────────────┐   ┌──────────────────┐            │
   │ Recipient        │   │ Recipient        │            │
   └────────┬─────────┘   └────────┬─────────┘            │
            │                      │                      │
            └──────────────┬───────┴──────────────────────┘
                           │
                           ▼
                 ┌──────────────────────┐
                 │ Completeness +       │
                 │ Validation           │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Workflow Compiler    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Structured Workflow  │
                 │ JSON / Graph         │
                 └──────────────────────┘
```

### 1. Invoice Notification

Example:

> Monitor incoming invoices.

The system can collect:

- trigger source
- mailbox/folder
- invoice condition
- notification channel
- recipient

---

### 2. Database Notification

Example:

> Notify #sales when a new customer is added to the PostgreSQL customers table.

The system collects:

- database
- table
- notification channel
- recipient

Dependencies are represented explicitly.

For example:

```text
database
   ↓
table
```

The system does not ask for a dependent requirement until its prerequisite information is available.

---

### 3. Scheduled Report

Example:

> Every Monday at 9 AM, send the sales report to #sales.

The system collects:

- schedule
- action
- recipient

The system supports incremental requirement collection:

```text
User:
Every Monday at 9 AM

Assistant:
What should the workflow do?

User:
Send the sales report to #sales.

Assistant:
Workflow generated.
```

---

## Requirement Graph

Every workflow is represented as a collection of typed requirements.

Conceptually:

```text
Requirement
├── key
├── label
├── required
├── status
├── value
├── evidence[]
├── confidence
├── question
└── depends_on[]
```

Example:

```text
database
├── value: PostgreSQL
├── status: satisfied
└── confidence: 0.95

table
├── value: customers
├── status: satisfied
├── confidence: 0.92
└── depends_on: database
```

This makes the conversation state explicit instead of relying on hidden LLM context.

---

## Evidence and Confidence

Each extracted value can retain its source message and confidence.

For example:

```json
{
  "value": "PostgreSQL",
  "source_message": "Notify #sales when a new customer is added to the PostgreSQL customers table.",
  "confidence": 0.95
}
```

If an extraction is ambiguous or below the confidence threshold, the requirement remains unresolved instead of being silently accepted.

---

## Clarification Policy

The clarification engine is deterministic.

It:

1. Finds unsatisfied required requirements.
2. Checks dependency conditions.
3. Avoids asking blocked questions.
4. Avoids unnecessary duplicate questions.
5. Asks one useful question at a time.
6. Prevents workflow generation while required information is missing.

This is important because **the LLM does not decide when the workflow is complete**.

---

## Ambiguity and Context Handling

The system distinguishes between different conversation states.

### General Question

> What is database normalization?

This does not become a workflow merely because the word "database" appears.

### Ambiguous Automation Request

> Do something with my data.

The system asks for clarification rather than inventing a workflow.

### Unsupported Workflow

> Create an automation that monitors my WhatsApp messages and automatically replies.

The system does not fabricate an unsupported workflow.

### Workflow Correction

After a workflow has been generated:

> Actually, send it to #marketing instead.

The existing workflow state is updated instead of restarting the conversation.

---

## Example Workflow Output

A completed scheduled workflow is compiled into a structured representation similar to:

```json
{
  "name": "Scheduled report workflow",
  "nodes": [
    {
      "id": "schedule",
      "type": "schedule_trigger",
      "schedule": "every monday at 9 am"
    },
    {
      "id": "action",
      "type": "action",
      "description": "send the sales report"
    },
    {
      "id": "notify",
      "type": "notification",
      "recipient": "#sales"
    }
  ],
  "edges": [
    {
      "from": "schedule",
      "to": "action"
    },
    {
      "from": "action",
      "to": "notify"
    }
  ]
}
```

This is a **workflow intermediate representation**, not an execution engine.

The same representation could later be mapped to systems such as n8n or other automation platforms.

---

## Demo UI

The project includes a lightweight browser interface with:

- conversational message history
- assistant and user message states
- loading indicator
- workflow visualization
- workflow node connections
- structured JSON view
- responsive layout

The UI is intentionally separate from the decision engine so the backend can also be consumed through the API.

---

## Repository Structure

```text
digitomics-workflow-builder/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   ├── config.py
│   │   └── orchestrator.py
│   ├── domain/
│   │   ├── models.py
│   │   └── catalog.py
│   ├── agents/
│   │   ├── intent_gateway.py
│   │   ├── workflow_resolver.py
│   │   ├── question_policy.py
│   │   └── compiler.py
│   ├── services/
│   │   └── llm.py
│   └── storage/
│       └── session_store.py
├── web/
│   └── index.html
├── tests/
│   ├── test_engine.py
│   ├── test_evaluation.py
│   ├── test_intent_gateway.py
│   ├── test_policy.py
│   ├── test_database_extractor.py
│   └── test_workflow_resolver.py
├── .env.example
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

---

## Running Locally

### Requirements

- Python 3.11+
- pip

### Setup

Create a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project:

```bash
pip install -e ".[test]"
```

Create environment configuration:

```powershell
Copy-Item .env.example .env
```

The default configuration uses the deterministic mock extractor, so an external LLM API key is not required for the demo.

### Start the Application

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

---

## Testing

Run the complete test suite:

```bash
pytest -q
```

Current result:

```text
23 passed
```

The tests cover:

- intent classification
- workflow type resolution
- invoice workflows
- database workflows
- scheduled workflows
- dependency-aware clarification
- incomplete workflow prevention
- ambiguity handling
- unsupported workflow handling
- acknowledgement handling
- workflow corrections
- action and recipient extraction
- compiled workflow structure

---

## Example Demo Scenarios

### Complete Workflow

```text
User:
Every Monday at 9 AM, send the sales report to #sales.

Assistant:
Workflow generated.
```

### Progressive Clarification

```text
User:
Every Monday at 9 AM

Assistant:
What should the workflow do?

User:
Send the sales report to #sales.

Assistant:
Workflow generated.
```

### Database Workflow

```text
User:
Notify #sales when a new customer is added to the PostgreSQL customers table.

Assistant:
Which database table should I monitor for new records?

User:
customer table

Assistant:
Workflow generated.
```

### Workflow Correction

```text
User:
Actually, send it to #marketing instead.

Assistant:
Updated workflow representation.
```

---

## Engineering Trade-offs

### Deterministic Mock Extractor

The repository includes a deterministic extractor so the complete workflow can be evaluated without requiring an external LLM API.

The extraction layer is isolated behind an interface, allowing an OpenAI-compatible provider to be substituted without changing the orchestration or validation logic.

### In-Memory Sessions

The current demo uses in-memory session storage for simplicity.

A production implementation could replace this with:

- PostgreSQL
- Redis
- another persistent session store

without changing the conversation architecture.

### Planner, Not Executor

The system intentionally stops at workflow planning and compilation.

It does not:

- connect to a user's Gmail account
- query a production database
- send real notifications
- execute generated workflows

This keeps workflow planning and external side effects separate.

---

## Production Extensions

Possible next steps include:

- persistent session storage
- authentication and user-level isolation
- richer workflow schemas
- provider-specific node adapters
- real n8n-compatible workflow compilation
- approval and versioning before execution
- execution monitoring
- structured observability
- extraction-quality evaluation
- broader workflow catalog
- human-in-the-loop approval for ambiguous workflows

---

## Key Takeaway

The central idea of this project is:

> **Use language models for interpretation, but use deterministic software for correctness.**

The result is a conversational workflow builder that can handle incomplete requests, ambiguity, dependencies, corrections, and multiple workflow types without allowing the language model to silently invent required information.
