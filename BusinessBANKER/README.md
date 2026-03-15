# BusinessBANKER

**Decision & Workflow Management Platform for Banking Institutions**

Implements the functional specification from Jira ticket [BNDE-84](https://cognitivegroup.atlassian.net/browse/BNDE-84).

---

## Architecture

```
BusinessBANKER/
├── main.py                  # FastAPI app & startup
├── requirements.txt
├── models/
│   ├── client.py            # Client Base File (§2.2)
│   ├── loan_request.py      # Loan Request + configurable sections (§2.3)
│   ├── workflow.py          # Workflow steps, transitions, routing conditions (§2.1)
│   └── user.py              # Users, Roles (human & AI), Org Units (§4.1–4.2)
├── engine/
│   └── workflow_engine.py   # Step orchestration, condition evaluation, portfolio view
├── config/
│   └── configuration.py     # Bank-level configuration (§4)
└── api/
    ├── clients.py            # Client CRUD
    ├── loan_requests.py      # Request lifecycle + workflow advancement
    └── dependencies.py      # DI: store & engine
```

---

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Interactive API docs: **http://localhost:8000/docs**

---

## Standard Banking Workflow

```
[Initiation / RM]
       ↓
[Credit Analysis / Analyst]
       ↓
[Adjudication / Adjudicator]
   ↓ amount > 500k → [Head of Credit]
                         ↓ amount > 2M → [Managing Director]
                                            ↓ amount > 10M → [Board]
       ↓ (approved at any level)
[Legal & Documentation]
       ↓
[Disbursement / Operations]
       ↓
[Completed]
```

Every transition condition is configurable. Any field on the request can be used as a routing variable.

---

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/clients/` | Create a client base file |
| `GET`  | `/api/v1/clients/` | List all clients |
| `POST` | `/api/v1/requests/` | Create a loan request |
| `GET`  | `/api/v1/requests/portfolio` | Portfolio view (filtered by role + branch) |
| `GET`  | `/api/v1/requests/{id}/transitions` | Available next steps |
| `POST` | `/api/v1/requests/{id}/advance` | Advance workflow step |
| `PATCH`| `/api/v1/requests/{id}/sections/{section_id}` | Update a section |
| `POST` | `/api/v1/requests/{id}/decisions` | Record a committee decision |
| `GET`  | `/api/v1/config` | View active bank configuration |

---

## AI Integration (§6)

Roles can be flagged as `is_ai_agent=True`. The `WorkflowEngine.auto_route()` method
evaluates all conditions and automatically advances the request — enabling AI agents
to participate in the workflow without human intervention at their assigned steps.

---

## Spec Reference

- **§2** System Architecture (Workflow Engine, Client Base File, Loan Request)
- **§3** Standard Banking Workflow (Front / Middle / Back Office)
- **§4** System Configuration (Org, Roles, Workflow, Permissions)
- **§5** Portfolio View
- **§6** AI Integration
