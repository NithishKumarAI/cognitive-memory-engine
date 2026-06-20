from fastapi import FastAPI
import app.models
from app.db.database import test_connection

from app.routes.user import router as user_router
from app.routes.study_logs import router as study_log_router
from app.routes.memory import router as memory_router
from app.routes import rag
from app.routes import analytics
from app.routes.learning_track import (router as learning_track_router)
from app.routes import recommendation

app = FastAPI(
    title="Cognitive Memory Engine",
    version="1.0.0"
)

app.include_router(user_router)
app.include_router(study_log_router)
app.include_router(memory_router)
app.include_router(rag.router)
app.include_router(analytics.router)
app.include_router(learning_track_router)
app.include_router(recommendation.router)

def root():
    return {
        "message": "Cognitive Memory Engine API is running"
    }


@app.get("/health")
def health_check():
    try:
        test_connection()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }