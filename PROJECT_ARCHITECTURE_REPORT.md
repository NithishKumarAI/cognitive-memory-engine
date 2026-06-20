# 1. Project Overview

## What Problem This Project Solves

Cognitive Memory Engine is a backend system for capturing study activity, converting that activity into structured long-term memories, generating embeddings for those memories, and retrieving semantically relevant memories later.

The project is aimed at becoming a production-style RAG memory and progress intelligence system.

Current implemented focus:

* User registration and JWT authentication
* User-owned study logs
* User-owned memories
* Memory embeddings
* Semantic memory retrieval with pgvector

Planned broader goal:

* Document ingestion
* Learning analytics
* Recommendations
* RAG reasoning workflows
* Progress tracking intelligence

## Type of System

This is currently a backend API service.

Architecturally, it is a FastAPI + PostgreSQL application with a layered backend structure:

```text
Client
  -> FastAPI Routes
  -> Authentication / Authorization
  -> Schemas
  -> CRUD Layer
  -> SQLAlchemy ORM
  -> PostgreSQL
  -> pgvector
```

## Main Technologies Used

Implemented:

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* pgvector
* Alembic
* Pydantic
* JWT with `python-jose`
* OAuth2 bearer authentication
* bcrypt password hashing via `passlib`
* Sentence Transformers
* `BAAI/bge-base-en-v1.5` embedding model
* Torch

Planned but not yet implemented in the repository:

* Next.js
* TailwindCSS
* shadcn/ui
* Recharts
* LangChain
* LlamaIndex
* Langfuse
* Vercel
* Railway
* Neon / Supabase
* Notion API integration

---

# 2. Folder Structure

Source tree, excluding `.git`, `.venv`, `.idea`, and generated `__pycache__` folders:

```text
cognitive-memory-engine/
├── .env
├── .gitignore
├── LICENSE
├── PROJECT_PROGRESS.md
├── PROJECT_ARCHITECTURE_REPORT.md
├── README.md
└── backend/
    ├── alembic.ini
    ├── project_structure.txt
    ├── requirements.txt
    ├── temp_requirements.txt
    ├── alembic/
    │   ├── README
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │       ├── 3d0e118a4fdf_initial_schema.py
    │       ├── 9de2f17eda3a_add_notes_to_study_logs.py
    │       ├── 305e4c8b7844_add_memories_table.py
    │       └── 86a536d3ece5_test_memory_embedding.py
    └── app/
        ├── create_tables.py
        ├── main.py
        ├── core/
        │   ├── auth.py
        │   ├── config.py
        │   └── security.py
        ├── crud/
        │   ├── __init__.py
        │   ├── memory.py
        │   ├── memory_embedding.py
        │   ├── retrieval.py
        │   ├── study_logs.py
        │   └── user.py
        ├── db/
        │   ├── database.py
        │   ├── dependencies.py
        │   ├── rebuild_embeddings.py
        │   ├── temp.py
        │   └── test.py
        ├── models/
        │   ├── __init__.py
        │   ├── conversation.py
        │   ├── memory.py
        │   ├── memory_embedding.py
        │   ├── study_log.py
        │   ├── usage_limit.py
        │   └── user.py
        ├── routes/
        │   ├── __init__.py
        │   ├── memory.py
        │   ├── study_logs.py
        │   └── user.py
        ├── schemas/
        │   ├── __init__.py
        │   ├── memory.py
        │   ├── retrieval.py
        │   ├── study_logs.py
        │   └── user.py
        └── services/
            └── embedding_service.py
```

## Root Folder

Purpose:

* Repository metadata and project documentation.

Responsibilities:

* Describe project vision.
* Track development phases.
* Store backend source.

Key files:

* `README.md`
* `PROJECT_PROGRESS.md`
* `PROJECT_ARCHITECTURE_REPORT.md`
* `.env`
* `.gitignore`
* `LICENSE`

## `backend/`

Purpose:

* Main backend application directory.

Responsibilities:

* API server
* Database models
* Migrations
* CRUD operations
* Authentication
* Embedding and retrieval logic

Key files:

* `requirements.txt`
* `alembic.ini`
* `project_structure.txt`

## `backend/app/`

Purpose:

* Main FastAPI application package.

Responsibilities:

* Application startup
* Router registration
* Database integration
* Business-layer organization

Key files:

* `main.py`
* `create_tables.py`

## `backend/app/core/`

Purpose:

* Core security and configuration layer.

Responsibilities:

* JWT creation and validation
* OAuth2 bearer token handling
* Password hashing
* Auth dependency resolution
* Static configuration values

Key files:

* `auth.py`
* `security.py`
* `config.py`

## `backend/app/db/`

Purpose:

* Database connection and operational utilities.

Responsibilities:

* SQLAlchemy engine setup
* Session management
* FastAPI DB dependency
* Embedding rebuild utility
* Local testing scripts

Key files:

* `database.py`
* `dependencies.py`
* `rebuild_embeddings.py`
* `test.py`
* `temp.py`

Note: `temp.py` references a missing `reranking_service`, so it appears to be experimental or incomplete.

## `backend/app/models/`

Purpose:

* SQLAlchemy ORM table definitions.

Responsibilities:

* Define database tables
* Define relationships
* Register models with SQLAlchemy metadata

Key files:

* `user.py`
* `study_log.py`
* `memory.py`
* `memory_embedding.py`
* `conversation.py`
* `usage_limit.py`

## `backend/app/schemas/`

Purpose:

* Pydantic request/response contracts.

Responsibilities:

* Validate incoming API payloads
* Shape API responses
* Hide sensitive fields such as password hashes

Key files:

* `user.py`
* `study_logs.py`
* `memory.py`
* `retrieval.py`

## `backend/app/crud/`

Purpose:

* Database access layer.

Responsibilities:

* Encapsulate persistence operations
* Keep route handlers separate from database queries
* Provide user, study log, memory, embedding, and retrieval operations

Key files:

* `user.py`
* `study_logs.py`
* `memory.py`
* `memory_embedding.py`
* `retrieval.py`

## `backend/app/routes/`

Purpose:

* FastAPI API route layer.

Responsibilities:

* Define public HTTP endpoints
* Apply authentication dependencies
* Enforce ownership checks
* Call CRUD and service layers

Key files:

* `user.py`
* `study_logs.py`
* `memory.py`

## `backend/app/services/`

Purpose:

* External/model service logic.

Responsibilities:

* Load embedding model
* Generate normalized embeddings

Key file:

* `embedding_service.py`

## `backend/alembic/`

Purpose:

* Database migration system.

Responsibilities:

* Track schema evolution
* Generate/apply database migrations
* Register SQLAlchemy model metadata

Key files:

* `env.py`
* `versions/*.py`

---

# 3. System Architecture

## Request Flow

Current backend request flow:

```text
Client
  |
  v
FastAPI Application
  |
  v
Router Layer
  |
  v
Authentication Dependency
  |
  v
Pydantic Schema Validation
  |
  v
CRUD Layer
  |
  v
SQLAlchemy Session
  |
  v
PostgreSQL Database
```

For memory search:

```text
Client
  |
  v
POST /memories/search
  |
  v
JWT Authentication
  |
  v
Query Embedding Generation
  |
  v
pgvector Similarity Search
  |
  v
User-Scoped Memory Results
```

## Architecture Diagram

```text
+----------------+
|    Client      |
+----------------+
        |
        v
+------------------------+
| FastAPI App             |
| backend/app/main.py     |
+------------------------+
        |
        v
+------------------------+
| API Routes              |
| users / study logs      |
| memories / search       |
+------------------------+
        |
        v
+------------------------+
| Auth Layer              |
| JWT + OAuth2 Bearer     |
| get_current_user        |
+------------------------+
        |
        v
+------------------------+
| Schema Layer            |
| Pydantic validation     |
+------------------------+
        |
        v
+------------------------+
| CRUD Layer              |
| User / StudyLog /       |
| Memory / Retrieval      |
+------------------------+
        |
        v
+------------------------+
| SQLAlchemy ORM          |
+------------------------+
        |
        v
+------------------------+
| PostgreSQL              |
| pgvector extension      |
+------------------------+
        |
        v
+------------------------+
| Vector Similarity       |
| Memory Embeddings       |
+------------------------+
```

---

# 4. Database Architecture

## Tables

Implemented ORM models define these tables:

1. `users`
2. `study_logs`
3. `memories`
4. `memory_embeddings`
5. `conversations`
6. `usage_limits`

## `users`

Purpose:

* Stores registered application users.

Columns:

* `id`: primary key
* `username`: unique username
* `email`: unique email
* `hashed_password`: bcrypt password hash
* `created_at`: creation timestamp

Relationships:

* One user has many study logs.
* One user has many memories.
* One user can have many conversations.
* One user can have one usage limit record.

## `study_logs`

Purpose:

* Stores user-owned study sessions.

Columns:

* `id`: primary key
* `user_id`: foreign key to `users.id`
* `topic`: studied topic
* `duration_minutes`: session duration
* `notes`: textual study notes
* `created_at`: creation timestamp

Relationships:

* Belongs to one user.
* Can have many memories.

## `memories`

Purpose:

* Stores structured long-term memory records created by users.

Columns:

* `id`: primary key
* `user_id`: foreign key to `users.id`
* `study_log_id`: optional foreign key to `study_logs.id`
* `title`: memory title
* `content`: memory body
* `category`: memory category

Relationships:

* Belongs to one user.
* Optionally belongs to one study log.
* Has one memory embedding.

## `memory_embeddings`

Purpose:

* Stores vector embeddings for memory records.

Columns:

* `id`: primary key
* `memory_id`: unique foreign key to `memories.id`
* `model_name`: embedding model identifier
* `embedding`: pgvector column, 768 dimensions
* `created_at`: creation timestamp

Relationships:

* Belongs to one memory.
* One-to-one with `memories`.

## `conversations`

Purpose:

* Intended to store user conversation history.

Columns:

* `id`: primary key
* `user_id`: foreign key to `users.id`
* `message`: user message
* `response`: system/assistant response
* `created_at`: creation timestamp

Relationships:

* Belongs to one user by foreign key.

Current status:

* Model exists.
* No CRUD layer or API routes currently expose conversations.

## `usage_limits`

Purpose:

* Intended to track user request quotas.

Columns:

* `id`: primary key
* `user_id`: unique foreign key to `users.id`
* `daily_requests`: daily request count
* `monthly_requests`: monthly request count
* `created_at`: creation timestamp

Relationships:

* One usage limit record belongs to one user.

Current status:

* Model exists.
* No CRUD layer or API routes currently enforce usage limits.

## ER-Style Relationship Overview

```text
users
  |--< study_logs
  |       |--< memories
  |
  |--< memories
  |       |-- memory_embeddings
  |
  |--< conversations
  |
  |-- usage_limits
```

Expanded:

```text
User 1 --- N StudyLog
User 1 --- N Memory
StudyLog 1 --- N Memory
Memory 1 --- 1 MemoryEmbedding
User 1 --- N Conversation
User 1 --- 1 UsageLimit
```

Important database note:

* The project documentation says an HNSW index exists, but the repository does not contain a migration that creates the HNSW index.
* The pgvector extension setup is documented in `PROJECT_PROGRESS.md`, but `CREATE EXTENSION vector` is not represented in Alembic migrations.

---

# 5. Authentication Architecture

## JWT Flow

```text
User logs in
  |
  v
Credentials validated
  |
  v
JWT access token created
  |
  v
Token contains user email in "sub"
  |
  v
Client sends token as Bearer token
  |
  v
Protected routes decode token
  |
  v
User is loaded from database
```

JWT payload shape:

```text
sub: user email
exp: expiration timestamp
```

Token settings:

* Algorithm: `HS256`
* Expiration: 30 minutes
* Secret key: currently hardcoded in config

## OAuth2PasswordBearer

The auth layer uses FastAPI's OAuth2 bearer mechanism.

```text
Authorization: Bearer <access_token>
```

Configured token URL:

```text
login
```

This allows protected routes to depend on bearer-token authentication.

## Login Flow

```text
POST /login
  |
  v
Validate email + password
  |
  v
Find user by email
  |
  v
Verify bcrypt password
  |
  v
Create JWT access token
  |
  v
Return bearer token
```

## Registration Flow

```text
POST /register
  |
  v
Validate username, email, password
  |
  v
Check duplicate email
  |
  v
Check duplicate username
  |
  v
Hash password
  |
  v
Create user
  |
  v
Return safe user response
```

## Protected Route Flow

```text
Protected endpoint
  |
  v
OAuth2 bearer dependency extracts token
  |
  v
JWT is decoded
  |
  v
Email is extracted from token subject
  |
  v
Database user lookup
  |
  v
Route receives current_user
```

## `get_current_user` Flow

```text
Bearer Token
  |
  v
verify_access_token()
  |
  v
Extract email from JWT "sub"
  |
  v
get_user_by_email()
  |
  v
Return User ORM object
```

## Authentication Flow Diagram

```text
+---------+
| Client  |
+---------+
    |
    | POST /login
    v
+-------------------+
| Login Endpoint    |
+-------------------+
    |
    v
+-------------------+
| Authenticate User |
+-------------------+
    |
    v
+-------------------+
| Create JWT        |
+-------------------+
    |
    v
+-------------------+
| Return Token      |
+-------------------+
    |
    | Authorization: Bearer token
    v
+-------------------+
| Protected Route   |
+-------------------+
    |
    v
+-------------------+
| get_current_user  |
+-------------------+
    |
    v
+-------------------+
| User-Scoped Logic |
+-------------------+
```

---

# 6. Memory System Architecture

## StudyLog Architecture

Study logs represent authenticated user study sessions.

Each study log contains:

* Topic
* Duration
* Notes
* Owning user
* Creation timestamp

Study logs are user-scoped. All study log access is filtered by the authenticated user.

```text
User
  |
  v
StudyLog
```

## Memory Architecture

Memories are structured knowledge units.

Each memory contains:

* Title
* Content
* Category
* Owning user
* Optional study log link
* Optional one-to-one embedding record

```text
User
  |
  v
Memory
  |
  v
MemoryEmbedding
```

## Memory Ownership

Memory ownership is assigned from the authenticated user.

A client cannot create a memory for another user directly because `user_id` is taken from `current_user`.

```text
JWT User
  |
  v
current_user.id
  |
  v
memory.user_id
```

## StudyLog to Memory Ownership Enforcement

During memory creation, if a `study_log_id` is provided, the system validates that the study log belongs to the authenticated user.

```text
Create Memory Request
  |
  v
Has study_log_id?
  |
  v
Check StudyLog.id + current_user.id
  |
  v
Allow or reject memory creation
```

Current caveat:

* Creation validates study log ownership.
* Memory update allows `study_log_id` in the update schema, but the same ownership validation is not currently applied during update.

## Memory Relationship Diagram

```text
+---------+
| User    |
+---------+
    |
    | owns
    v
+-------------+
| StudyLog    |
+-------------+
    |
    | can generate / link to
    v
+-------------+
| Memory      |
+-------------+
    |
    | has one
    v
+------------------+
| MemoryEmbedding  |
+------------------+
```

## User Ownership Enforcement

Implemented strongly for:

* Study log create/read/update/delete
* Memory read/update/delete
* Memory creation ownership assignment
* Memory search filtering by `Memory.user_id`

Less strict areas:

* `/users` returns all users to any authenticated user.
* `/users/{user_id}` allows any authenticated user to fetch another user.
* Memory update does not revalidate changed `study_log_id`.

---

# 7. Embedding & Retrieval Architecture

## Embedding Generation Pipeline

```text
Memory created
  |
  v
Title + content combined
  |
  v
SentenceTransformer model loaded
  |
  v
Normalized embedding generated
  |
  v
Embedding stored in memory_embeddings
```

## Embedding Model Used

Model:

```text
BAAI/bge-base-en-v1.5
```

Embedding dimensions:

```text
768
```

Normalization:

* Embeddings are generated with normalized vector output.

## `MemoryEmbedding` Model

Purpose:

* Stores one vector embedding per memory.

Important properties:

* `memory_id` is unique.
* Embedding uses pgvector `Vector(768)`.
* `model_name` stores the embedding model identifier.
* `created_at` records insertion time.

## pgvector Integration

The project uses:

* PostgreSQL as primary database
* pgvector extension for vector column support
* `pgvector.sqlalchemy.Vector` for SQLAlchemy model integration
* cosine distance for retrieval

## HNSW Indexing

The project progress document states that an HNSW index named `memory_embeddings_hnsw_idx` was created using `vector_cosine_ops`.

However:

* No Alembic migration in the repository creates this index.
* No script in the repository recreates this index.
* The index may exist in the local database, but it is not reproducible from the checked-in migration history.

Recommended correction:

* Add an Alembic migration for `CREATE EXTENSION IF NOT EXISTS vector`.
* Add an Alembic migration for the HNSW index.

## Similarity Search Pipeline

```text
POST /memories/search
  |
  v
Authenticate user
  |
  v
Generate query embedding
  |
  v
Join memories to memory_embeddings
  |
  v
Filter by current_user.id
  |
  v
Order by cosine distance
  |
  v
Limit top K
  |
  v
Return memory id, title, category, distance
```

## Retrieval Flow Diagram

```text
+----------------+
| User Query     |
+----------------+
        |
        v
+----------------------------+
| BGE Embedding Generation   |
+----------------------------+
        |
        v
+----------------+
| Query Vector   |
+----------------+
        |
        v
+----------------------------+
| pgvector Cosine Search     |
+----------------------------+
        |
        v
+----------------------------+
| Filter by User Ownership   |
+----------------------------+
        |
        v
+----------------+
| Top-K Memories |
+----------------+
```

---

# 8. API Architecture

## Health

### `GET /health`

Purpose:

* Checks API and database connectivity.

Current root note:

* A root handler exists in `main.py`, but it is not decorated as an endpoint, so `GET /` is not currently registered.

## Authentication

### `POST /register`

Purpose:

* Creates a new user.
* Hashes the password.
* Prevents duplicate email and username.

### `POST /login`

Purpose:

* Authenticates user credentials.
* Returns JWT bearer token.

### `GET /me`

Purpose:

* Returns the authenticated user profile.

Protected:

* Yes

## Users

### `GET /users`

Purpose:

* Returns all users.

Protected:

* Yes

Security note:

* Any authenticated user can list all users.

### `GET /users/{user_id}`

Purpose:

* Returns a user by id.

Protected:

* Yes

Security note:

* Any authenticated user can fetch any user profile by id.

## Study Logs

### `POST /study-logs/`

Purpose:

* Creates a study log for the authenticated user.

Protected:

* Yes

### `GET /study-logs/`

Purpose:

* Returns all study logs owned by the authenticated user.

Protected:

* Yes

### `GET /study-logs/{study_log_id}`

Purpose:

* Returns one owned study log.

Protected:

* Yes

Ownership enforced:

* Yes

### `PUT /study-logs/{study_log_id}`

Purpose:

* Updates one owned study log.

Protected:

* Yes

Ownership enforced:

* Yes

### `DELETE /study-logs/{study_log_id}`

Purpose:

* Deletes one owned study log.

Protected:

* Yes

Ownership enforced:

* Yes

## Memories

### `POST /memories`

Purpose:

* Creates a user-owned memory.
* Optionally links it to a user-owned study log.
* Generates and stores an embedding.

Protected:

* Yes

### `GET /memories`

Purpose:

* Returns memories owned by the authenticated user.

Protected:

* Yes

### `GET /memories/{memory_id}`

Purpose:

* Returns one memory.

Protected:

* Yes

Ownership enforced:

* Yes

### `PUT /memories/{memory_id}`

Purpose:

* Updates one memory.

Protected:

* Yes

Ownership enforced:

* Yes

Current caveats:

* Updating memory content does not regenerate the embedding.
* Updating `study_log_id` does not revalidate study log ownership.

### `DELETE /memories/{memory_id}`

Purpose:

* Deletes one memory.

Protected:

* Yes

Ownership enforced:

* Yes

## Retrieval

### `POST /memories/search`

Purpose:

* Performs semantic memory retrieval.
* Generates a query embedding.
* Searches user-owned memory embeddings by cosine distance.
* Returns top matching memories.

Protected:

* Yes

Request fields:

* `query`
* `limit`, default `5`, minimum `1`, maximum `20`

Response fields:

* `memory_id`
* `title`
* `category`
* `distance`

---

# 9. Security Architecture

## Authentication

Implemented:

* Password hashing with bcrypt
* JWT access tokens
* OAuth2 bearer token extraction
* Protected route dependencies

## Authorization

Implemented:

* Study logs are scoped to the authenticated user.
* Memories are scoped to the authenticated user.
* Retrieval only searches memories owned by the authenticated user.

Partially implemented:

* User endpoints are authenticated but not role- or ownership-restricted.

## Ownership Validation

Strong ownership validation exists for:

* Reading study logs
* Updating study logs
* Deleting study logs
* Reading memories
* Updating memories
* Deleting memories
* Searching memories
* Linking a memory to a study log during creation

Ownership gap:

* Memory update can change `study_log_id` without validating that the new study log belongs to the current user.

## Data Isolation

Implemented isolation:

```text
User A
  -> User A study logs
  -> User A memories
  -> User A retrieval results

User B
  -> User B study logs
  -> User B memories
  -> User B retrieval results
```

Data isolation concerns:

* `/users` exposes all users to any authenticated user.
* `/users/{user_id}` exposes user profiles across accounts.
* Hardcoded JWT secret should be moved to environment configuration.
* `alembic.ini` contains a database URL with credentials.
* `.env` exists, but core JWT settings are not currently environment-driven.

---

# 10. Current Development Status

## Implemented

The repository currently implements:

* FastAPI backend application
* PostgreSQL connection setup
* SQLAlchemy ORM base and sessions
* Alembic migration infrastructure
* User model
* Study log model
* Memory model
* Memory embedding model
* Conversation model
* Usage limit model
* User registration
* User login
* JWT creation and validation
* OAuth2 bearer authentication
* Current-user dependency
* Password hashing and verification
* Protected user endpoints
* Protected study log CRUD
* Protected memory CRUD
* Study log ownership enforcement
* Memory ownership enforcement
* Study log ownership validation during memory creation
* Automatic embedding generation during memory creation
* pgvector-backed embedding storage
* Semantic search endpoint
* Cosine similarity search
* Embedding rebuild utility for existing embeddings
* Gemini integration
* LLM service layer
* Context assembly service
* RAG service
* Conversation persistence
* RAG API endpoint
* Source attribution
* Citation-aware answers
* Retrieval-Augmented Generation

## Currently Available Capabilities

The system can currently:

* Register users
* Log users in
* Issue bearer tokens
* Authenticate protected requests
* Create study logs
* Retrieve study history
* Update study logs
* Delete study logs
* Create memories
* Categorize memories
* Link memories to study logs
* Generate memory embeddings
* Store embeddings in PostgreSQL
* Search memories semantically
* Return user-scoped top-K memory matches

## Implemented but Not Yet Exposed

These models exist but do not yet have full application workflows:

* Conversations
* Usage limits

## Documented but Not Fully Reproducible From Repo

The progress file documents:

* pgvector extension installation
* HNSW index creation

But migrations do not currently reproduce:

* `CREATE EXTENSION vector`
* HNSW index creation

---# 10.1 RAG Architecture

## Overview

Phase 7 introduced Retrieval-Augmented Generation (RAG) capabilities to the Cognitive Memory Engine.

The system now supports:

* Memory-aware question answering
* Semantic retrieval
* Context assembly
* LLM-powered answer generation
* Source attribution
* Citation-aware responses
* Conversation persistence

The Cognitive Memory Engine is now capable of generating answers grounded in user-owned memories.

---

## RAG Request Flow

```text
Client
   ↓
POST /rag/ask
   ↓
JWT Authentication
   ↓
Generate Query Embedding
   ↓
pgvector Similarity Search
   ↓
Top-K Memory Retrieval
   ↓
Context Assembly
   ↓
Prompt Construction
   ↓
Gemini 2.5 Flash
   ↓
Grounded Response
   ↓
Conversation Storage
   ↓
JSON Response
```

---

## RAG Components

### LLM Service

File:

```text
backend/app/services/llm_service.py
```

Responsibilities:

* Gemini configuration
* LLM communication
* Response generation

Implemented model:

```text
Gemini 2.5 Flash
```

---

### Context Service

File:

```text
backend/app/services/context_service.py
```

Responsibilities:

* Memory formatting
* Context construction
* Prompt-ready memory conversion

Input:

```text
Memory Objects
```

Output:

```text
Structured Context String
```

---

### RAG Service

File:

```text
backend/app/services/rag_service.py
```

Responsibilities:

* Embedding generation
* Semantic retrieval
* Context assembly
* Prompt construction
* LLM invocation
* Conversation persistence
* Source collection

Pipeline:

```text
Question
    ↓
Embedding
    ↓
Retrieval
    ↓
Context
    ↓
Prompt
    ↓
Gemini
    ↓
Answer
```

---

### Conversation Persistence

File:

```text
backend/app/crud/conversation.py
```

Every successful RAG interaction stores:

```text
User Question
Assistant Response
Timestamp
User Ownership
```

into:

```text
conversations
```

table.

---

### RAG Endpoint

File:

```text
backend/app/routes/rag.py
```

Endpoint:

```http
POST /rag/ask
```

Authentication:

```text
JWT Bearer Token Required
```

---

## Context Injection

Retrieved memories are converted into structured context blocks.

Example:

```text
Memory 1
Title: Supervised Learning

Content:
Supervised learning includes classification and regression.

Memory 2
Title: SQL Joins

Content:
Inner joins combine matching rows.
```

These memories are injected into the LLM prompt before generation.

---

## Source Attribution

Responses return supporting memory references.

Example:

```json
{
  "answer": "...",
  "sources": [
    {
      "memory_id": 4,
      "title": "Machine Learning Study Session",
      "category": "AI",
      "distance": 0.22
    }
  ]
}
```

---

## Citation Support

Prompt-level citations are implemented.

Example:

```text
Supervised learning [Memory 1]

Decision trees [Memory 1], [Memory 2]
```

Citations reference the retrieved memory blocks used during answer generation.

---

## Current RAG Architecture

```text
User Question
      ↓
BGE Embedding Model
      ↓
Query Vector
      ↓
pgvector HNSW Search
      ↓
Top-K User Memories
      ↓
Context Assembly
      ↓
Prompt Construction
      ↓
Gemini 2.5 Flash
      ↓
Grounded Answer
      ↓
Memory Citations
      ↓
Conversation Storage
```

---

## Current Capabilities

The system can now:

* Register users
* Authenticate users
* Create study logs
* Create memories
* Generate embeddings
* Store embeddings in pgvector
* Retrieve memories semantically
* Answer natural-language questions
* Generate memory-grounded responses
* Return supporting source memories
* Persist conversations
* Produce citation-aware answers

The Cognitive Memory Assistant is operational.

# 11. Missing Components

## Missing RAG Components

Not yet implemented:

* Document ingestion
* File upload pipeline
* Chunking
* Document metadata model
* Context window management
* Conversation-aware retrieval
* Reranking service
* Cross-encoder reranker
* Retrieval evaluation metrics
* Recall@K / MRR benchmarking
* Hybrid search
* Query rewriting
* Memory summarization
* Memory consolidation

Note:

* `backend/app/db/temp.py` references a reranking service, but no such service exists in the repository.

## Missing Analytics Components

Not yet implemented:

* Study duration analytics
* Topic frequency analytics
* Learning streaks
* Progress trends
* Weak-area detection
* Review history
* Retention scoring
* Dashboard APIs
* Aggregated reporting tables
* Event tracking

## Missing Recommendation Components

Not yet implemented:

* Recommendation engine
* Next-topic suggestions
* Spaced repetition scheduling
* Personalized review queues
* Weak-memory resurfacing
* Goal-based learning plans
* Similar-memory clustering
* Priority scoring
* Adaptive study recommendations

## Missing Deployment Components

Not yet implemented:

* Dockerfile
* Docker Compose
* Production ASGI config
* Environment-specific settings
* CI/CD pipeline
* Cloud deployment config
* Database migration deployment workflow
* Secret management
* Observability setup
* Logging strategy
* Error monitoring
* Health/readiness split
* Test suite
* Frontend application

---

# 12. Recommended Next Phase

## Recommended Next Phase: Retrieval Quality & RAG Readiness

The best next phase is to stabilize and improve the retrieval layer before adding full RAG generation.

Why:

* The core memory, embedding, and semantic search foundation already exists.
* RAG quality depends heavily on retrieval quality.
* Current embeddings are generated on memory creation, but updates do not refresh embeddings.
* HNSW index setup is documented but not migration-backed.
* No reranking service currently exists.
* No retrieval evaluation framework exists.
* The repository already identifies Phase 6.3 as retrieval quality and reranking.

## Recommended Scope

### 1. Make Vector Infrastructure Reproducible

Add migrations for:

* pgvector extension
* HNSW index
* vector cosine operator class

### 2. Fix Embedding Lifecycle

Add embedding refresh behavior for:

* Memory content update
* Memory title update
* Missing embedding backfill
* Model version changes

### 3. Add Retrieval Quality Layer

Implement:

* Reranking service
* Two-stage retrieval
* Search result content in response
* Similarity thresholding
* Retrieval evaluation fixtures
* Recall@K and MRR measurement

### 4. Then Add RAG

After retrieval quality is stable, add:

* LLM service abstraction
* Prompt construction
* Context assembly
* Answer generation endpoint
* Conversation persistence
* Source-aware responses

## Suggested Phase Name

```text
Phase 6.3 - Retrieval Quality, Re-Ranking, and RAG Readiness
```

This phase is the natural bridge between the current semantic memory search backend and the future full cognitive/RAG system.

# 10.2 Analytics Architecture

## Overview

Phase 8 introduced the Analytics Engine Foundation.

The system now supports user-specific learning analytics derived from Study Logs.

Analytics are generated entirely from authenticated user-owned study history.

---

## Analytics Request Flow

```text
Client
   ↓
Analytics Endpoint
   ↓
JWT Authentication
   ↓
Current User Resolution
   ↓
Study Log Aggregation
   ↓
Analytics Service
   ↓
Dashboard JSON Response
```

---

## Analytics Service

File:

```text
backend/app/services/analytics_service.py
```

Responsibilities:

* Topic analytics
* Time analytics
* Consistency analytics
* Neglect detection
* Dashboard metrics

---

## Analytics Endpoints

File:

```text
backend/app/routes/analytics.py
```

Implemented endpoints:

```http
GET /analytics/overview

GET /analytics/topic-distribution
GET /analytics/most-studied-topics
GET /analytics/least-studied-topics

GET /analytics/study-hours
GET /analytics/daily-activity
GET /analytics/weekly-study-hours
GET /analytics/monthly-study-hours

GET /analytics/streak
GET /analytics/frequency
GET /analytics/consistency

GET /analytics/topic-recency
GET /analytics/neglected-topics
```

---

## Topic Analytics

Provides:

* Study hours per topic
* Session counts per topic
* Most-studied topics
* Least-studied topics

Pipeline:

```text
Study Logs
      ↓
Group By Topic
      ↓
Duration Aggregation
      ↓
Topic Rankings
```

---

## Time Analytics

Provides:

* Total study time
* Daily activity
* Weekly study totals
* Monthly study totals

Pipeline:

```text
Study Logs
      ↓
Time Aggregation
      ↓
Daily / Weekly / Monthly Metrics
```

---

## Consistency Analytics

Provides:

* Current streak
* Study frequency
* Consistency score

Current formula:

```text
Consistency Score
=
(Frequency Score × 0.7)
+
(Streak Score × 0.3)
```

---

## Neglect Detection

Provides:

* Topic recency tracking
* Days since last study
* Neglected topic ranking

Pipeline:

```text
Study Logs
      ↓
Last Study Date
      ↓
Days Since Last Study
      ↓
Neglected Topic Ranking
```

---

## Current Analytics Architecture

```text
Study Logs
      ↓
Analytics Service
      ↓
Topic Analytics
      ↓
Time Analytics
      ↓
Consistency Analytics
      ↓
Neglect Detection
      ↓
Dashboard APIs
```

---

## Current Capabilities

The system can now:

* Track learning activity
* Measure study effort
* Measure consistency
* Track streaks
* Detect neglected topics
* Generate dashboard-ready analytics
* Produce user-specific progress metrics

The Cognitive Memory Engine is now both a Memory Assistant and a Progress Intelligence System.

```
```
# 10.3 Learning Track Architecture

## Overview

Phase 8.2 introduced Learning Tracks and infrastructure stabilization.

The system now supports long-term learning journeys.

Examples:

* Machine Learning
* FastAPI
* PostgreSQL
* RAG Systems
* Deep Learning

---

## Current Learning Hierarchy

```text
User
│
├── LearningTrack
│       │
│       └── StudyLog
│               │
│               └── Memory
│                       │
│                       └── MemoryEmbedding
│
├── Conversation
│
└── Analytics
```

---

## LearningTrack Model

Table:

```text
learning_tracks
```

Columns:

```text
id
user_id
name
description
created_at
```

Relationships:

```text
User 1 --- N LearningTrack
LearningTrack 1 --- N StudyLog
```

---

## Learning Context Inheritance

The architecture intentionally stores:

```text
study_logs.learning_track_id
```

and does not store:

```text
memories.learning_track_id
```

Memories inherit their learning context through:

```text
Memory
    ↓
StudyLog
    ↓
LearningTrack
```

This design avoids redundancy and preserves consistency.

---

## Infrastructure Stabilization

The vector infrastructure is now fully reproducible.

Implemented through Alembic migrations:

* pgvector extension enablement
* HNSW index creation

New environments can recreate the complete vector infrastructure using:

```bash
alembic upgrade head
```

No manual database modifications are required.

---

## Embedding Lifecycle

Memory embeddings are automatically regenerated whenever:

* Memory title changes
* Memory content changes

This guarantees semantic retrieval quality remains consistent after updates.

---

## Ownership Validation

The system validates ownership for:

* Study Logs
* Memories
* Learning Tracks
* Memory ↔ StudyLog relationships
* StudyLog ↔ LearningTrack relationships

This guarantees complete user isolation across the platform.

---

## Updated Relationship Overview

```text
User 1 --- N LearningTrack
LearningTrack 1 --- N StudyLog
User 1 --- N StudyLog
User 1 --- N Memory
StudyLog 1 --- N Memory
Memory 1 --- 1 MemoryEmbedding
User 1 --- N Conversation
User 1 --- 1 UsageLimit
```

The Cognitive Memory Engine now functions as both:

* A Memory Assistant
* A Progress Intelligence System
* A Learning Intelligence Platform

```
```
# 10.4 Recommendation Architecture

## Overview

Phase 9 introduced the Recommendation Engine Foundation.

The system now supports personalized, user-specific learning recommendations generated from Learning Tracks, Study Logs, and analytics signals.

Recommendations are generated entirely from authenticated user-owned learning data.

---

## Recommendation Request Flow

```text
Client
   ↓
Recommendation Endpoint
   ↓
JWT Authentication
   ↓
Current User Resolution
   ↓
Recommendation Service
   ↓
Learning Data Analysis
   ↓
Recommendation Prioritization
   ↓
JSON Response
```

---

## Recommendation Service

File:

```text
backend/app/services/recommendation_service.py
```

Responsibilities:

* Neglected track detection
* Continue-learning recommendations
* Weak-area detection
* Start-learning recommendations
* Recommendation prioritization
* Daily recommendation aggregation

---

## Recommendation Endpoints

File:

```text
backend/app/routes/recommendation.py
```

Implemented endpoints:

```http
GET /recommendations/neglected
GET /recommendations/continue-learning
GET /recommendations/weak-areas
GET /recommendations/daily
```

All endpoints require JWT bearer authentication.

---

## Neglected Recommendation Engine

Detects Learning Tracks that have not been studied recently.

Pipeline:

```text
Learning Tracks
        ↓
Latest Study Log
        ↓
Days Since Last Study
        ↓
Neglected Recommendation
```

Examples:

```text
You have not studied PostgreSQL for 14 days.
```

Priority rules:

```text
14+ days inactive
        ↓
High Priority

7–13 days inactive
        ↓
Medium Priority
```

---

## Continue Learning Engine

Encourages users to continue their active learning journeys.

Pipeline:

```text
Study Logs
      ↓
Most Recent Activity
      ↓
Learning Track
      ↓
Continue Recommendation
```

Example:

```text
Continue your Machine Learning learning journey.
```

---

## Weak Area Detection Engine

Identifies under-studied Learning Tracks.

Current rules:

```text
0 study sessions
      ↓
Start Learning Recommendation

1 study session
      ↓
Weak Area Recommendation
```

Examples:

```text
Start your FastAPI learning journey.

You have studied RAG Systems only 1 time(s).
Spend more time on it.
```

---

## Daily Recommendation Engine

The unified recommendation engine aggregates multiple recommendation sources.

Pipeline:

```text
Neglected Recommendations
              ↓
Continue Recommendations
              ↓
Weak Area Recommendations
              ↓
Recommendation Aggregation
              ↓
Priority Sorting
              ↓
Daily Recommendation Feed
```

Endpoint:

```http
GET /recommendations/daily
```

This endpoint provides a single frontend-ready recommendation feed.

---

## Recommendation Prioritization

Recommendations are sorted before being returned.

Current priority hierarchy:

```text
High
   ↓
Medium
   ↓
Low
```

Examples:

```text
High:
Neglected > 14 days

Medium:
Weak areas
Neglected 7–13 days

Low:
Continue learning
Start learning
```

---

## Current Recommendation Architecture

```text
User
   ↓
LearningTrack
   ↓
StudyLog
   ↓
Analytics Signals
   ↓
Recommendation Service
   ↓
Prioritized Recommendations
   ↓
Frontend APIs
```

---

## Current Capabilities

The system can now:

* Detect neglected learning tracks
* Suggest continuation of active learning journeys
* Detect weak learning areas
* Suggest new learning journeys
* Prioritize recommendations
* Generate daily recommendation feeds
* Produce frontend-ready recommendation APIs

The Cognitive Memory Engine now functions as:

* A Memory Assistant
* A Progress Intelligence System
* A Learning Intelligence Platform
* An Intelligent Learning Coach

```
```
