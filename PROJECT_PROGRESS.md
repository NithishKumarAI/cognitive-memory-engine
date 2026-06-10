# Cognitive Memory Engine

## Project Overview

Cognitive Memory Engine is a production-style AI Memory and Progress Intelligence System.

### Goal

Build an AI-powered system that can:

* Ingest documents and study logs
* Store long-term memories
* Retrieve relevant information
* Track learning progress
* Generate analytics
* Provide intelligent recommendations

### Tech Stack

#### Frontend

* Next.js
* TailwindCSS
* shadcn/ui
* Recharts

#### Backend

* FastAPI

#### Database

* PostgreSQL
* pgvector

#### AI Frameworks

* LlamaIndex
* LangChain

#### Observability

* Langfuse

#### Deployment

* Vercel
* Railway
* Neon/Supabase

---

# Progress Tracker

## Phase 1 — Foundation Setup

### Status

✅ Completed

### Objectives

* [x] Create GitHub repository
* [x] Create Python virtual environment
* [x] Install FastAPI
* [x] Install PostgreSQL
* [x] Create PostgreSQL database
* [x] Configure SQLAlchemy
* [x] Configure psycopg
* [x] Connect FastAPI to PostgreSQL
* [x] Create health endpoint
* [x] Configure environment variables
* [x] Configure gitignore

---

## What Was Built

### FastAPI Application

Created a FastAPI backend application and verified:

* Server startup
* API routing
* Swagger documentation

Endpoints:

* GET /
* GET /health

---

### PostgreSQL Database

Created database:

```sql
cognitive_memory_engine
```

Verified connectivity between:

FastAPI → SQLAlchemy → psycopg → PostgreSQL

---

### Environment Configuration

Created:

```text
.env
```

Moved database credentials out of source code.

---

## Key Concepts Learned

### FastAPI

* Application instance
* Routes
* Request handling
* Swagger/OpenAPI docs

### Uvicorn

* ASGI server
* Development reload mode

### PostgreSQL

* Database creation
* Database server architecture
* Connection strings

### SQLAlchemy

* Engine creation
* Database connectivity

### Environment Variables

* Secret management
* .env files
* Configuration separation

---

## Current Architecture

```text
Browser
   ↓
FastAPI
   ↓
SQLAlchemy
   ↓
psycopg
   ↓
PostgreSQL
```

---

# Next Phase

## Phase 2 — Database Foundation

Planned topics:

* SQLAlchemy sessions
* Database models
* Base model creation
* Users table
* Study logs table
* Database schema design
* Alembic migrations
* CRUD operations

---

## Notes

### Decisions

* PostgreSQL + pgvector selected instead of ChromaDB
* FastAPI selected for backend
* PyCharm selected as primary IDE
* Environment variables used for secrets

### Repository

Project Name:

```text
cognitive-memory-engine
```
# Phase 2 — Database Foundation

## Status

✅ Completed

## Objectives

* [x] Create SQLAlchemy Base
* [x] Configure SessionLocal
* [x] Create Users model
* [x] Create StudyLogs model
* [x] Create Conversations model
* [x] Create UsageLimits model
* [x] Register models with SQLAlchemy
* [x] Generate PostgreSQL tables
* [x] Configure Alembic
* [x] Create initial migration baseline
* [x] Create database dependency (`get_db`)
* [x] Create UserCreate schema
* [x] Create User CRUD layer
* [x] Create POST /users endpoint
* [x] Create GET /users endpoint
* [x] Create GET /users/{user_id} endpoint
* [x] Verify PostgreSQL persistence

---

## What Was Built

### Database Infrastructure

Created:

```text
app/db/
├── database.py
└── dependencies.py
```

Implemented:

* SQLAlchemy Engine
* SessionLocal
* Declarative Base
* Database dependency injection

---

### Database Models

Created:

```text
app/models/
├── user.py
├── study_log.py
├── conversation.py
└── usage_limit.py
```

Implemented tables:

* users
* study_logs
* conversations
* usage_limits

---

### PostgreSQL Schema

Verified tables exist:

```text
users
study_logs
conversations
usage_limits
```

Database successfully stores and retrieves records.

---

### Alembic Migration System

Configured:

```text
alembic/
├── env.py
├── versions/
└── script.py.mako
```

Created migration baseline.

Verified:

```bash
alembic current
```

Output:

```text
(head)
```

Alembic is now synchronized with SQLAlchemy models.

---

### CRUD Foundation

Created:

```text
app/crud/
└── user.py
```

Implemented:

* create_user()
* get_users()
* get_user()

---

### API Routes

Created:

```text
app/routes/
└── user.py
```

Implemented endpoints:

```http
POST /users
GET  /users
GET  /users/{user_id}
```

Verified through Swagger UI.

---

### Data Persistence Test

Successfully:

* Created user records
* Retrieved all users
* Retrieved a single user by ID

Verified:

```text
FastAPI
    ↓
Pydantic
    ↓
CRUD Layer
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

works end-to-end.

---

## Key Concepts Learned

### SQLAlchemy ORM

* Declarative Base
* Models
* Columns
* Primary Keys
* Foreign Keys
* Sessions

### Database Design

* User table design
* Study log design
* Conversation storage design
* Usage tracking design

### Alembic

* Migration initialization
* Metadata discovery
* Revision generation
* Database stamping
* Schema synchronization

### FastAPI Architecture

* Dependency Injection
* APIRouter
* Request Validation
* CRUD Separation

### Pydantic

* Request schemas
* Email validation
* Data validation

---

## Current Architecture

```text
Client
   ↓
FastAPI Routes
   ↓
Pydantic Schemas
   ↓
CRUD Layer
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

---

# Next Phase

## Phase 2.1 — User Security Layer

Planned topics:

* Password hashing (bcrypt)
* Response schemas
* Hide password fields from API responses
* Duplicate email protection
* Duplicate username protection
* Proper HTTP exceptions
* Improved API responses

---

## Future Phases

### Phase 3 — Study Log System

* Study Log CRUD
* User-to-study-log relationships
* Learning history

### Phase 4 — Memory Layer

* Memory storage
* Memory retrieval
* Memory categorization

### Phase 5 — RAG Foundation

* Document ingestion
* Chunking
* Embeddings
* pgvector integration
* Semantic search

### Phase 6 — Intelligence Layer

* Progress analytics
* Learning insights
* Recommendations
* Memory ranking
