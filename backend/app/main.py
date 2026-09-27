import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

# Show the agents' progress ("Reading syllabus...", "Researching...") in the uvicorn console
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(name)s  %(message)s", datefmt="%H:%M:%S")
for noisy in ("httpx", "openai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

app = FastAPI(title="MyArc API")

# allows the Vite dev server (localhost:5173) to call this API from the
# browser; add your deployed frontend's origin here too once you have one
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
