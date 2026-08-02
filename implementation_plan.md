# Implementation Plan - Production-Ready FastAPI Backend Conversion

Convert the existing AI Business Risk Analysis System into a production-ready FastAPI backend following Clean Architecture, preserving existing AI business logic in `core/`, and setting up PostgreSQL/Alembic database foundations for future expansion.

---

## User Review Required

> [!IMPORTANT]
> **Preservation of Existing AI Pipeline**: The underlying AI business logic, scrapers, XLM-R model inference, fuzzy inference systems (FIS), statistical aggregators, and risk calculators in `core/` will remain completely untouched.
> FastAPI will act as an orchestration and API presentation layer around `core/`.

> [!NOTE]
> **Async Execution & Adapter Strategy**: Heavy synchronous/blocking AI pipeline calls (Selenium scraping & PyTorch inference) will be executed via `AIEngineAdapter` offloaded to background threads via `asyncio.to_thread`.

---

## Open Questions

> [!NOTE]
> All architectural feedback from prompt updates has been fully integrated:
> - `app/adapters/`: `ai_engine_adapter.py` moved outside services into `app/adapters/`.
> - `app/repositories/`: `analysis_repository.py`, `health_repository.py` created for DB integration.
> - `app/mappers/`: `analysis_mapper.py` created to map core AI results cleanly to API schemas.
> - `app/state/`: `core_state.py` created for global runtime health and AI model state tracking.
> - `app/domain/enums.py`: `RiskLevel` and `AnalysisStatus` enums introduced.
> - `app/security/`: `jwt.py` and `password.py` initialized as security placeholders.
> - `app/tasks/`: `recommendations.py`, `retraining.py`, `reports.py` added for background jobs.
> - Categorized logging: `API`, `AI`, `SCRAPER`, `DATABASE` logger instances.
> - Open API Tags: `System`, `Analysis`, `Authentication`, `History`, `Profile`.
> - Detailed health response: `{ "status": "healthy", "checks": { "database": "pending", "ai": "healthy", "scraper": "healthy" } }`.
> - Future-proof request: `{ "productUrl": "...", "options": { "saveHistory": true } }`.

---

## Proposed Project Structure

```
app/
├── main.py                         # FastAPI entry point, lifespan, CORS, middleware, global exception handlers
├── startup.py                      # Step-by-step verification, XLM-R load, adapter & engine warming
├── config/
│   ├── __init__.py
│   └── settings.py                 # Application & environment settings via Pydantic Settings
├── constants/
│   ├── __init__.py
│   ├── api_constants.py            # Route paths (/api/v1), headers (X-Request-ID)
│   └── messages.py                 # Response & error message templates
├── domain/
│   ├── __init__.py
│   └── enums.py                    # RiskLevel (LOW, MEDIUM, HIGH, CRITICAL) & AnalysisStatus enums
├── state/
│   ├── __init__.py
│   └── core_state.py               # Central ApplicationState (ai_loaded, engine, model, checks)
├── mappers/
│   ├── __init__.py
│   └── analysis_mapper.py          # Maps core AI result outputs cleanly into API response schemas
├── adapters/
│   ├── __init__.py
│   └── ai_engine_adapter.py        # Infrastructure adapter isolating FastAPI from core AI engine
├── services/
│   ├── __init__.py
│   ├── analysis_service.py         # Business service orchestrating Analysis workflow
│   └── health_service.py           # Service querying ApplicationState & DB repository
├── repositories/
│   ├── __init__.py
│   ├── analysis_repository.py      # Repository interface & placeholder DB operations for Analysis
│   └── health_repository.py        # Repository interface for DB health check query
├── security/
│   ├── __init__.py
│   ├── jwt.py                      # Security placeholder for JWT processing
│   └── password.py                 # Security placeholder for password hashing
├── tasks/
│   ├── __init__.py
│   ├── recommendations.py          # Background task placeholder for recommendations
│   ├── retraining.py               # Background task placeholder for model retraining
│   └── reports.py                  # Background task placeholder for email reports
├── api/
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py               # GET /api/v1/health, GET /api/v1/version (Tag: System)
│   │   ├── analysis.py             # POST /api/v1/analysis (Tag: Analysis)
│   │   ├── auth.py                 # POST /api/v1/auth/login, POST /api/v1/auth/register (Tag: Authentication)
│   │   ├── history.py              # GET /api/v1/history (Tag: History)
│   │   └── profile.py              # GET /api/v1/profile (Tag: Profile)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common_schema.py        # ApiResponse wrapper with meta (requestId, timestamp, version)
│   │   ├── health_schema.py        # HealthCheckResponse & VersionResponse schemas
│   │   └── analysis_schema.py      # AnalysisRequest (productUrl, options) & AnalysisResultResponse
│   └── dependencies/
│       ├── __init__.py
│       ├── database.py             # SQLAlchemy DB session dependency generator
│       └── services.py             # Service layer dependency injection
├── database/
│   ├── __init__.py
│   ├── session.py                  # SQLAlchemy 2.x engine & sessionmaker setup
│   └── base.py                     # DeclarativeBase foundation
├── models/
│   ├── __init__.py                 # Database ORM models placeholder
├── middleware/
│   ├── __init__.py
│   ├── request_id_middleware.py    # X-Request-ID header & context management
│   └── logging_middleware.py       # Categorized request/response logging
├── utils/
│   ├── __init__.py
│   ├── exceptions.py               # Domain custom exceptions and FastAPI error handlers
│   └── logger.py                   # Categorized logger factory (API, AI, SCRAPER, DATABASE)
alembic.ini                          # Alembic configuration for SQLAlchemy migrations
```

---

## Detailed Implementation Steps

### 1. Settings & Core State (`app/config/settings.py` & `app/state/core_state.py`)
- Define `Settings` loading configuration from `.env`.
- Define `ApplicationState` storing runtime health check flags (`ai_loaded`, `db_healthy`, `scraper_healthy`, `checks` dictionary).

### 2. Startup Loader with Step Verification (`app/startup.py`)
- Startup steps:
  1. Verify XLM-R model paths & config.
  2. Load tokenizer & model adapter.
  3. Instantiate `ProductAnalysisEngine`.
  4. Perform warm-up inference run.
  5. Mark `ApplicationState.ai_loaded = True` and set `checks["ai"] = "healthy"`.

### 3. Core Adapter & Mapper (`app/adapters/` & `app/mappers/`)
- `AIEngineAdapter`: Calls `ProductAnalysisEngine`, `QualityFIS`, `DeliveryFIS`, `TrustFIS`, `BusinessRiskCalculator`.
- `AnalysisMapper`: Transforms core execution DTOs into structured response schemas:
  - `product`: Title, URL, review count, rating.
  - `statistics`: Sentiment stats, aspect stats, confidence stats.
  - `risks`: Quality risk, delivery risk, trust risk, business risk index, and `RiskLevel` enum.

### 4. Services & Repositories (`app/services/` & `app/repositories/`)
- `HealthService`: Checks `ApplicationState` and calls `HealthRepository.check_db_connection()`.
- `AnalysisService`: Receives `AnalysisRequest`, executes `AIEngineAdapter` in thread worker (`asyncio.to_thread`), maps results via `AnalysisMapper`, and persists history via `AnalysisRepository`.

### 5. API Endpoints, Tags & Schemas (`app/api/`)
- OpenAPI tags: `System`, `Analysis`, `Authentication`, `History`, `Profile`.
- `POST /api/v1/analysis` accepts `{ "productUrl": "...", "options": { "saveHistory": true } }`.
- Response structure:
  ```json
  {
      "success": true,
      "message": "Analysis completed successfully.",
      "data": {
          "analysisId": "anl_123456789",
          "status": "completed",
          "product": { ... },
          "statistics": { ... },
          "risks": { ... }
      },
      "meta": {
          "requestId": "3a7d4f...",
          "timestamp": "2026-07-27T23:06:57Z",
          "version": "1.0.0"
      }
  }
  ```
- Placeholder endpoints (`POST /api/v1/auth/login`, `POST /api/v1/auth/register`, `GET /api/v1/history`, `GET /api/v1/profile`) return HTTP 501 with structured JSON.

---

## Verification Plan

### Automated Tests
- Create `tests/api/test_endpoints.py`:
  - Verify `/api/v1/health` status and `checks` payload.
  - Verify `/api/v1/version` response metadata.
  - Verify placeholder endpoints return HTTP 501 with standardized response.
  - Verify `/api/v1/analysis` validates invalid URLs gracefully.

### Manual Verification
- Start Uvicorn: `uvicorn app.main:app --reload`.
- Inspect Swagger UI at `http://localhost:8000/docs`.
- Run sample test execution against Daraz product URL.
