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

## Data Flow (Single-turn Q&A)

1. App sends `{question, answer, app_cost, metadata}` to evaluator
2. Evaluator runs N judges (human and/or LLM)
3. Results stored with verdicts, scores, explanations
4. App queries results to track improvement

## Judge Calibration

- Human judges = gold standard (used heavily early on)
- LLM judges calibrated against human baseline
- Track agreement rate until LLM judges can run solo
- Periodic human spot-checks after graduation

## Judge Prompts

- **Generic** (shared): coherence, hallucination, relevance
- **App-specific** (configured per app): domain rules, tone, safety

## Deployment

Evaluator deployed as standalone service. Callable from:
- Local development
- Staging
- Production

# Evaluation app architecture

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

POST /human-judgment
└── completes human judgments (manual consumer)
```

- All judgments start as `pending`
- `LLMJudgeWorker` processes LLM judgments async
- Human judgments completed via API
- Evaluation complete when all judgments complete

### API TODO

When summary data is returned from `summary` endpoint, need to implement 2 additional endpoints

1. GET for all samples for an evaluation which returns the sample results like score and passing
2. GET for judgments to get all sample judgments to look at reasonings

Something similiar for the `golden-comparison` which returns all samples (same GET) but then for each sample make 2 calls to get Human and LLM details


## Frontend

Frontend part is PURELY for interacting with the human for judging and displaying result information.


## Implementation plan

- create basic api for creating evals & human judge api
- basic FE for human judging
- deploy


## Components
services -- business logic and validation
schemas -- always have up to 2 api schemas 1 for list returns and 1 for detail return