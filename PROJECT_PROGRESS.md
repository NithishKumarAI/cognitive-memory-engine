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
