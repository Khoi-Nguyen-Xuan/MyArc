# MyArc

MyArc is a multi-agent semester planning platform that helps students understand **which courses need the most attention, when workload will peak, and why**. 

Instead of acting like a LLM chatbot, MyArc uses a multi-agent team behind the scenes to analyze course syllabi, external course discussions on the internet (Reddit, RateMyProf,..), deadlines, and workload patterns, then presents the results through rankings, calendars, and evidence insights.

## Goal

MyArc is being built as a production-oriented project with a focus on real users, reliable AI reasoning, explainable recommendations, and a clean visual experience.

The goal is simple:

> **Help students see their semester before it hits them.**

## Features

- Upload and analyze multiple course syllabi
- Rank courses by difficulty, workload, and priority
- Generate a semester-wide workload calendar
- Highlight high-pressure weeks using visual indicators
- Extract exams, assignments, projects, and important deadlines
- Research external course feedback and student experiences
- Show evidence and confidence behind each recommendation
- Use multi-agent workflows for research, evaluation, and verification

## Architecture

```text
Frontend
   ↓
FastAPI Backend
   ↓
Agent Orchestration
   ├── Syllabus Agent
   ├── Research Agent
   ├── Evaluator Agent
   └── Critic Agent (planned)
   ↓
Structured JSON
   ↓
Dashboard / Rankings / Calendar
```

The system uses a hybrid approach where LLMs handle reasoning and interpretation, while traditional backend logic handles deterministic tasks such as scoring, sorting, dates, storage, and validation.

## Agents

One syllabus upload runs three agents in order: **Syllabus → Research → Evaluator**.

**Syllabus Agent** (`app/agents/syllabus/`)
Reads the PDF or .docx and extracts the course code, title, term, instructors, graded assessments (weights and dates) and key policies. Code checks every quote against the file, and the agent gets one chance to fix any problems.

**Research Agent** (`app/agents/research/`)
A LangGraph agent that searches Reddit and the web (Tavily) for what students say about the course. It returns short, cited claims, each tagged as making the course sound harder, easier or neutral, with a relevance score.

**Evaluator Agent** (`app/agents/evaluator/`)
Combines both results into six scores from 0 to 100:

| Criterion | Weight | Scored by |
|---|---|---|
| Workload | 0.25 | LLM |
| Conceptual difficulty | 0.20 | LLM |
| Deadline pressure | 0.20 | Code |
| Assessment weighting | 0.10 | Code |
| Continuous study | 0.10 | LLM |
| Student review difficulty | 0.15 | Code |

The weighted total gives the course's point and its rank: S ≥ 80, A ≥ 65, B ≥ 50, C ≥ 35, D otherwise. The LLM cites evidence by ID, so every piece of evidence shown is a real syllabus line or student post.

The full flow is in `app/services/course_analysis.py`. It runs behind `POST /courses/upload-syllabus` and saves the result to Postgres.

## Tech Stack

**Frontend**
- React
- TypeScript

**Backend**
- FastAPI
- Python
- LangGraph
- Pydantic
- SQLAlchemy

**Data**
- PostgreSQL
- pgvector

**AI**
- LLM structured outputs
- RAG
- Embeddings
- Multi-agent orchestration
- External web research
