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
# Phase 3 — User Security Layer

## Status

✅ Completed

## Objectives

* [x] Install passlib and python-jose
* [x] Configure bcrypt password hashing
* [x] Create password verification service
* [x] Create UserResponse schema
* [x] Create UserLogin schema
* [x] Create Token schema
* [x] Implement secure user creation
* [x] Prevent duplicate email registration
* [x] Prevent duplicate username registration
* [x] Create registration endpoint
* [x] Create login endpoint
* [x] Generate JWT access tokens
* [x] Validate JWT access tokens
* [x] Configure OAuth2 bearer authentication
* [x] Create get_current_user dependency
* [x] Protect API routes
* [x] Create GET /me endpoint
* [x] Hide password fields from API responses

---

## What Was Built

### Password Security

Created:

```text
app/core/security.py
```

Implemented:

* hash_password()
* verify_password()

Passwords are now stored as bcrypt hashes.

Verified that plain text passwords are never persisted to PostgreSQL.

---

### JWT Authentication System

Created:

```text
app/core/auth.py
```

Implemented:

* create_access_token()
* verify_access_token()
* oauth2_scheme
* get_current_user()

JWT tokens now contain:

```json
{
  "sub": "user@example.com",
  "exp": "<expiration>"
}
```

---

### User Authentication Schemas

Updated:

```text
app/schemas/user.py
```

Created:

* UserCreate
* UserResponse
* UserLogin
* Token

Response schemas prevent sensitive fields from leaking through APIs.

---

### Registration Flow

Implemented:

```http
POST /register
```

Features:

* Email validation
* Duplicate email protection
* Duplicate username protection
* Password hashing before database storage

---

### Login Flow

Implemented:

```http
POST /login
```

Features:

* User lookup by email
* Password verification
* JWT generation
* Bearer token response

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

### Protected Routes

Implemented:

```http
GET /me
GET /users
GET /users/{user_id}
```

Protected using:

```python
current_user = Depends(get_current_user)
```

Unauthorized users receive:

```json
{
  "detail": "Not authenticated"
}
```

---

### Current User System

Implemented:

```python
get_current_user()
```

Flow:

```text
Bearer Token
      ↓
JWT Validation
      ↓
Email Extraction
      ↓
Database Lookup
      ↓
User Object
```

This foundation will be reused across all future memory, conversation, document, and RAG endpoints.

---

## Key Concepts Learned

### Authentication

* Password hashing
* Password verification
* User registration
* User login

### JWT

* Token generation
* Token validation
* Claims
* Expiration handling

### FastAPI Security

* OAuth2PasswordBearer
* Dependency-based authentication
* Protected routes
* Current user dependencies

### API Security

* Response models
* Hiding sensitive fields
* HTTP exception handling
* Authorization checks

---

## Current Architecture

```text
Client
   ↓
JWT Token
   ↓
FastAPI Routes
   ↓
get_current_user()
   ↓
CRUD Layer
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

---

# Next Phase

## Phase 4 — User-Owned Study Log System

Planned topics:

* Authenticated study log creation
* User-to-study-log relationships
* Ownership enforcement
* Study log CRUD
* Study history retrieval
* Learning activity tracking

### Goal

Every study log should automatically belong to:

```python
current_user.id
```

using the authentication layer built in Phase 3.

# Phase 4 — User-Owned Study Log System

## Status

✅ Completed

## Objectives

* [x] Create StudyLog schemas
* [x] Create StudyLog CRUD layer
* [x] Create authenticated study log creation
* [x] Link study logs to users
* [x] Implement ownership enforcement
* [x] Create GET study logs endpoint
* [x] Create GET single study log endpoint
* [x] Create UPDATE study log endpoint
* [x] Create DELETE study log endpoint
* [x] Restrict users to their own study logs
* [x] Verify PostgreSQL persistence
* [x] Create study history retrieval APIs

---

## What Was Built

### StudyLog Schema Layer

Created:

```text
app/schemas/study_logs.py
```

Implemented:

* StudyLogCreate
* StudyLogUpdate
* StudyLogResponse

These schemas now provide request validation and response serialization for all Study Log APIs.

---

### StudyLog Model Enhancement

Updated:

```text
app/models/study_log.py
```

Added:

```python
notes
```

field to support richer study session information.

Study logs now contain:

```text
id
user_id
topic
duration_minutes
notes
created_at
```

This structure provides meaningful textual content for future AI memory and retrieval systems.

---

### Database Migration

Created Alembic migration:

```text
add_notes_to_study_logs
```

Successfully migrated PostgreSQL schema.

Verified that:

```text
study_logs
```

contains:

```text
id
user_id
topic
duration_minutes
notes
created_at
```

---

### StudyLog CRUD Layer

Created:

```text
app/crud/study_logs.py
```

Implemented:

* create_study_log()
* get_user_study_logs()
* get_study_log()
* update_study_log()
* delete_study_log()

The CRUD layer centralizes all Study Log database operations and separates business logic from API routes.

---

### StudyLog API Routes

Created:

```text
app/routes/study_logs.py
```

Implemented endpoints:

```http
POST   /study-logs/
GET    /study-logs/
GET    /study-logs/{study_log_id}
PUT    /study-logs/{study_log_id}
DELETE /study-logs/{study_log_id}
```

All endpoints were verified through Postman.

---

### Authenticated Study Log Creation

Integrated:

```python
get_current_user()
```

with Study Log creation.

Study logs are now automatically assigned to:

```python
current_user.id
```

Users cannot manually choose ownership.

Example flow:

```text
JWT Token
      ↓
Current User
      ↓
Study Log Creation
      ↓
user_id assigned automatically
```

---

### Ownership Enforcement

Implemented ownership validation on all protected Study Log operations.

Every Study Log query now includes:

```python
StudyLog.user_id == current_user.id
```

This prevents users from:

* Viewing another user's study logs
* Updating another user's study logs
* Deleting another user's study logs

Unauthorized access attempts return:

```json
{
  "detail": "Study log not found"
}
```

---

### Study History Retrieval

Implemented:

```http
GET /study-logs/
```

Returns only Study Logs owned by the authenticated user.

Example:

```text
User A
   ↓
Only User A Study Logs

User B
   ↓
Only User B Study Logs
```

This endpoint forms the foundation for future learning analytics and progress tracking features.

---

### End-to-End Verification

Successfully verified:

* Study Log creation
* Study Log retrieval
* Single Study Log retrieval
* Study Log updates
* Study Log deletion
* Ownership enforcement
* JWT authentication integration
* PostgreSQL persistence

Verified architecture:

```text
Client
   ↓
JWT Token
   ↓
get_current_user()
   ↓
Study Log Routes
   ↓
CRUD Layer
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

---

## Key Concepts Learned

### FastAPI

* APIRouter
* Route protection
* Path parameters
* Response models
* Dependency injection

### Authentication & Authorization

* Current user dependency
* JWT-protected endpoints
* Ownership enforcement
* User-scoped resources

### CRUD Design

* Create operations
* Read operations
* Update operations
* Delete operations
* Partial updates

### SQLAlchemy

* Query filtering
* User-specific database queries
* Database updates
* Database deletion
* Session management

### Database Migrations

* Schema evolution
* Alembic revision generation
* Migration execution
* PostgreSQL synchronization

---

## Current Architecture

```text
Client
   ↓
JWT Token
   ↓
Authentication Layer
   ↓
Study Log Routes
   ↓
Ownership Validation
   ↓
CRUD Layer
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

---

# Next Phase

## Phase 5 — Memory Layer Foundation

Planned topics:

* Memory model creation
* Memory schemas
* Memory CRUD layer
* Memory ownership
* Memory storage APIs
* Memory retrieval APIs
* Memory categorization
* User-specific memory management

### Goal

Transform raw Study Logs into structured memories that can later be used by retrieval, semantic search, and RAG systems.

# Phase 5 — Memory Layer Foundation

## Status

✅ Completed

## Objectives

* [x] Create Memory model
* [x] Create Memory schemas
* [x] Create Memory CRUD layer
* [x] Create Memory API routes
* [x] Create Memory ↔ User relationship
* [x] Create Memory ↔ StudyLog relationship
* [x] Implement Memory ownership enforcement
* [x] Implement authenticated Memory creation
* [x] Implement authenticated Memory retrieval
* [x] Implement authenticated Memory update
* [x] Implement authenticated Memory deletion
* [x] Implement Memory categorization
* [x] Validate StudyLog ownership before Memory linking
* [x] Generate and apply Alembic migration
* [x] Verify PostgreSQL persistence
* [x] Verify end-to-end API functionality

---

## What Was Built

### Memory Data Model

Created:

```text
app/models/memory.py
```

Implemented Memory entity containing:

```text
id
user_id
study_log_id
title
content
category
```

Each Memory represents a structured knowledge unit that can later be embedded, retrieved, ranked, and used in RAG pipelines.

---

### Memory Relationships

Implemented:

```text
User
   ↓
Memories

StudyLog
   ↓
Memories
```

Added SQLAlchemy relationships between:

* User ↔ Memory
* StudyLog ↔ Memory

This establishes the ownership and knowledge hierarchy required for future retrieval systems.

---

### Database Migration

Generated Alembic migration:

```text
add_memories_table
```

Successfully applied migration to PostgreSQL.

Verified creation of:

```text
memories
```

table.

---

### Memory Schemas

Created:

```text
app/schemas/memory.py
```

Implemented:

* MemoryCreate
* MemoryUpdate
* MemoryResponse

Schemas provide:

* Request validation
* Response serialization
* API contract enforcement

---

### Memory CRUD Layer

Created:

```text
app/crud/memory.py
```

Implemented:

* create_memory()
* get_memory_by_id()
* get_user_memories()
* update_memory()
* delete_memory()

Database operations are now separated from route logic following FastAPI best practices.

---

### Memory API Routes

Created:

```text
app/routes/memory.py
```

Implemented endpoints:

```http
POST   /memories
GET    /memories
GET    /memories/{memory_id}
PUT    /memories/{memory_id}
DELETE /memories/{memory_id}
```

All endpoints were successfully tested.

---

### Authentication Integration

Integrated Memory APIs with:

```python
get_current_user()
```

using the JWT authentication system built in Phase 3.

All Memory operations now require authentication.

Ownership is automatically assigned using:

```python
current_user.id
```

Users cannot manually choose ownership.

---

### Memory Ownership Enforcement

Implemented authorization checks for:

* Retrieve Memory
* Update Memory
* Delete Memory

Users can only access Memories that belong to them.

Unauthorized access attempts return appropriate HTTP errors.

---

### StudyLog Ownership Validation

Implemented validation before Memory creation.

When a Memory references:

```text
study_log_id
```

the system verifies that the referenced StudyLog belongs to the authenticated user.

This prevents:

```text
User A Memory
        ↓
linked to
        ↓
User B Study Log
```

and preserves ownership integrity across the system.

---

### PostgreSQL Persistence Verification

Successfully verified:

* Memory creation
* Memory retrieval
* Memory updates
* Memory deletion
* Memory ↔ StudyLog linking

All operations persist correctly in PostgreSQL.

---

### Authentication Architecture Review

During Phase 5, the authentication system was reviewed.

The project continues using:

```python
OAuth2PasswordBearer
```

and JWT authentication.

Reason:

* Required for user ownership enforcement
* Required for Memory isolation
* Required for future embeddings and retrieval systems
* Required for RAG personalization
* Required for analytics and recommendation features

A Swagger OAuth login-flow usability issue was identified.

This issue affects only developer experience inside Swagger UI and does not affect:

* Security
* Authentication
* Authorization
* Ownership validation
* JWT token handling

For testing, Postman was used successfully.

Future improvement:

```text
Swagger OAuth2 login flow refinement
```

without changing the underlying authentication architecture.

---

## End-to-End Verification

Successfully tested:

```http
POST   /memories
GET    /memories
GET    /memories/{memory_id}
PUT    /memories/{memory_id}
DELETE /memories/{memory_id}
```

Verified:

* JWT authentication
* Ownership enforcement
* StudyLog ownership validation
* PostgreSQL persistence
* API correctness

---

## Current Architecture

```text
Client
   ↓
JWT Authentication
   ↓
Memory Routes
   ↓
Ownership Validation
   ↓
CRUD Layer
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

---

## Outcome

The system now supports structured, user-owned Memories.

Memories are:

* Authenticated
* Authorized
* Persisted
* Categorized
* Linked to Study Logs

The Memory Layer is now ready for:

* Embeddings
* pgvector integration
* Semantic search
* Retrieval
* RAG systems
* Recommendation systems

---

# Next Phase

## Phase 6 — Embedding & Vector Foundation

Planned topics:

* pgvector installation
* Vector database integration
* Embedding generation
* Memory embeddings
* Semantic similarity search
* Retrieval layer
* RAG-ready memory retrieval

```
```
