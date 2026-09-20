# AI Study Tutor

An AI-powered semester/course intelligence platform. A student uploads
syllabi for their courses and (in later milestones) gets a workload
dashboard: difficulty tiers, weekly time estimates, deadline density,
exam pressure, evidence-backed scoring, and a combined calendar --
not a chatbot.

## Milestone 1 (this commit): intake skeleton

The first slice is deliberately narrow: get syllabus files *into* the
system, structured and traceable, before any AI/RAG logic touches
them. Everything else (parsing, scoring, dashboard) hangs off this.

- **Backend** (`backend/`): FastAPI + SQLAlchemy + SQLite.
  - `Semester` -> `Course` -> `SyllabusUpload` data model.
  - Upload endpoint stores the PDF on disk and writes a new
    `SyllabusUpload` row per upload -- uploads are never overwritten,
    so the row history *is* the audit/history trail for a course.
  - `GET /api/uploads` exposes that trail across every course.
- **Frontend** (`frontend/`): React + Vite.
  - Create a semester, add courses, upload a PDF per course, see the
    upload history trail update live.
- No auth, no scoring, no RAG yet -- those are the next milestones.

## Architecture

```
frontend (React/Vite, :5173)
    |  fetch, multipart/form-data
    v
backend (FastAPI, :8000)
    |  SQLAlchemy ORM
    v
SQLite (myarc.db)          backend/storage/<course_id>/  (raw PDFs)
```

`app/main.py` wires routers together; each router
(`semesters`, `courses`, `uploads`) owns one resource. `models.py` is
the single source of truth for the schema; `schemas.py` are the
Pydantic request/response shapes, kept separate so the API can evolve
without forcing a DB migration every time.

## Roadmap (not built yet)

1. **Ingestion pipeline**: parse an uploaded syllabus (text extraction
   -> LLM structuring) into deadlines, assignments, exams, grading
   weights. `SyllabusUpload.status` already has a slot for
   `parsing` / `parsed` / `failed` to support this.
2. **Multi-agent scoring**: agents that read the parsed syllabus and
   produce the S-D tier score, workload estimate, exam pressure, etc.,
   each with cited evidence back to the source text (RAG over the
   syllabus).
3. **Dashboard**: weekly workload heatmap, combined deadline calendar,
   priority ranking that reacts to upcoming due dates.
4. Swap SQLite -> Postgres, add Alembic migrations, add auth.

## Running locally

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Then open http://localhost:5173 with the backend running on :8000.

## Why the pieces are what they are

- **SQLite for now**: zero setup for a solo milestone; the model
  layer doesn't know or care which DB engine is behind it, so moving
  to Postgres later is a config change, not a rewrite.
- **Row-per-upload instead of latest-wins**: the project explicitly
  wants explainability ("what evidence supports this score") --
  keeping every uploaded version, not just the latest, is what makes
  that traceable later.
- **Routers split by resource**: keeps each file small and makes it
  obvious where a new endpoint belongs as the API grows.
