from fastapi import FastAPI

from app.db.database import test_connection

from app.routes.user import router as user_router
app = FastAPI(
    title="Cognitive Memory Engine",
    version="1.0.0"
)

app.include_router(user_router)

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