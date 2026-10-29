from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import app.models
from app.core.config import FRONTEND_ORIGINS
from app.db.database import test_connection

from app.routes.user import router as user_router
from app.routes.study_logs import router as study_log_router
from app.routes.memory import router as memory_router
from app.routes import rag
from app.routes import analytics
from app.routes.learning_track import (router as learning_track_router)
from app.routes import recommendation
from app.routes.capture import router as capture_router
from app.routes.learning import router as learning_router
from app.routes.workspace import router as workspace_router

app = FastAPI(
    title="LearnTrack",
    description="Your AI learning continuity companion.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspace_router)
app.include_router(capture_router)
app.include_router(learning_router)
app.include_router(user_router)
app.include_router(study_log_router)
app.include_router(memory_router)
app.include_router(rag.router)
app.include_router(analytics.router)
app.include_router(learning_track_router)
app.include_router(recommendation.router)

@app.get("/")
def root():
    return {
        "message": "LearnTrack API is running"
    }


@app.get("/health")
def health_check():
    try:
        test_connection()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "unavailable"
            }
        )


@app.middleware("http")
async def private_responses(request, call_next):
    response = await call_next(request)
    if request.headers.get("authorization") or request.url.path in ("/login", "/register", "/me"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Vary"] = ", ".join(filter(None, [response.headers.get("Vary"), "Authorization"]))
    return response


@app.exception_handler(RequestValidationError)
async def safe_auth_validation(request, exception):
    if request.url.path in ("/register", "/login"):
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": list(error["loc"]), "type": error["type"], "msg": "Invalid form value"}
            for error in exception.errors()
        ]})
    return await request_validation_exception_handler(request, exception)
