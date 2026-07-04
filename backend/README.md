# How to run

first start the api

```shell
make api
```

To run the judging of samples

```shell
make judge
```

To init the app with some mock data run

```shell
make init
```

To create more mock data

```shell
make eval
```

# Evaluation Framework Architecture

## Overview

Standalone evaluation service, decoupled from the application being evaluated.

## Separation of Concerns

```
App                          Evaluator Service
├── runs questions           ├── runs judges (human + LLM)
├── gets answers             ├── tracks judge costs
├── tracks app costs         ├── stores results
└── reports to evaluator     └── provides verdicts
```

## Entities

- App -- created for each application (not implemented yet)
- Evaluation -- created only for 1 app, contains metadata, app version etc, should created after every change in the app
- Sample -- tied to only 1 evaluation, contains the question, human & app anwers and some more metadata
- Judgment -- a sample can have many llm judgments and ONLY 1 human judgment, contains the verdict

## Data Flow (Single-turn Q&A)

1. App sends `{question, human_answer, app_answer, app_cost, metadata}` to evaluator
2. Evaluator runs N judges (human and/or LLM)
3. Results stored with verdicts, explanations
4. App queries results to track improvement

## Judge Calibration

- Human judges = gold standard (used heavily early on)
- LLM judges calibrated against human baseline
- Track agreement rate until LLM judges can run solo
- Periodic human spot-checks after graduation

## Deployment

Evaluator deployed as standalone service. Callable from:

- Local development
- Staging
- Production

## Architecture

```mermaid
flowchart TB
    User([User])
    App[AI Application]
    API[FastAPI Backend]
    DB[(Database)]
    Worker[LLMJudgeWorker]
    LLM[LLM Provider]
    Frontend[FE app]
    TestSuite[AI App Test suite]

    User -->|views results & submits human judgments| API
    Frontend -->|Get result for evals| API 
    TestSuite -->|Call for evals without human evals| API
    App -->|POST evaluation for development| API
    API --> DB
    Worker --> DB
    Worker -->|call for verdict| LLM
```

Consists of a backend and fronend parts.

## Backend

FastAPI REST API. Stores prompts per-app for different LLM judging prompts.

### Design (Work Queue Pattern)

```
EvaluationService              LLMJudgeWorker
├── creates evaluations        ├── polls pending LLM judgments
├── creates pending judgments  ├── executes in parallel
└── returns immediately        └── marks complete

POST /sample/{sample_id}/judgment
└── completes human judgments (manual consumer)
```

- All judgments start as `pending`
- `LLMJudgeWorker` processes LLM judgments async
- Human judgments completed via API
- Evaluation complete when all judgments complete

## Frontend

Frontend part is PURELY for interacting with the human for judging and displaying result information.

## Database Schema

```mermaid
erDiagram
    apps {
        int id PK
        string name
        int current_prompt_version_id FK
        datetime created_at
    }

    prompt_versions {
        int id PK
        int app_id FK
        string hash
        text content
        datetime created_at
    }

    evaluations {
        int id PK
        int app_id FK
        int prompt_version_id FK
        string version
        string type
        datetime created_at
    }

    samples {
        int id PK
        int evaluation_id FK
        text question
        text human_answer
        text app_answer
        float app_cost
        datetime created_at
    }

    judgments {
        int id PK
        int sample_id FK
        string status
        string judgment_type
        string judgment_model
        text reasoning
        bool passed
        int input_tokens
        int output_tokens
        float input_tokens_cost
        float output_tokens_cost
        datetime created_at
        datetime updated_at
    }

    app_datasets {
        int id PK
        int app_id FK
        text question
        text human_answer
        datetime created_at
        datetime updated_at
    }

    machine_clients {
        int id PK
        string client_id UK
        string client_secret_hash
        string name
        bool is_admin
        bool revoked
        datetime created_at
    }

    machine_tokens {
        int id PK
        string token_hash UK
        string client_id FK
        datetime expires_at
        bool revoked
        datetime created_at
    }

    app_principals {
        int id PK
        int app_id FK
        string subject_type
        string subject
    }

    apps ||--o{ prompt_versions : "has"
    apps ||--o| prompt_versions : "current"
    apps ||--o{ evaluations : "has"
    apps ||--o{ app_datasets : "has"
    prompt_versions ||--o{ evaluations : "used in"
    evaluations ||--o{ samples : "contains"
    samples ||--o{ judgments : "judged by"
    machine_clients ||--o{ machine_tokens : "issues"
    apps ||--o{ app_principals : "bound to"
```

## Auth

- **Humans**: generic OIDC id_token verified against the issuer's JWKS
  (`src/api/auth.py`).
- **Machines**: Verdikt is its own OAuth2 `client_credentials` issuer — opaque
  `vkt_` tokens stored in `machine_tokens` (`src/auth/`, discovery + `/auth/token`
  in `src/api_app.py`). Clients are created/removed per-app via
  `/v1/app/{app_id}/machine-clients` (`require_app_access`).
- Both resolve to one `Principal` (`src/api/deps.py: authenticate`), authorized
  per app via `app_principals`; admins (access-config `admins:` list, or an
  admin client) see all.
- Email principals + admins are managed declaratively via the access-config YAML
  (`ACCESS_CONFIG_PATH`, `src/auth/access_config.py`), reconciled on startup.

## Components

repositories -- data access only, no business logic, no data transformation beyond mapping DB rows to base schemas
services -- business logic and validation
schemas -- always have up to 2 api schemas 1 for list returns and 1 for detail return
