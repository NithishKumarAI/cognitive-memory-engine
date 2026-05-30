from fastapi import FastAPI

from app.db.database import test_connection

app = FastAPI(
    title="Cognitive Memory Engine",
    version="1.0.0"
)


@app.get("/")
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