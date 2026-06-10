from app.db.database import Base, engine

# Import all models
import app.models

Base.metadata.create_all(bind=engine)

print("Tables created successfully")