from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import semesters, courses, uploads

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Study Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(semesters.router)
app.include_router(courses.router)
app.include_router(uploads.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
