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
   └── Critic Agent
   ↓
Structured JSON
   ↓
Dashboard / Rankings / Calendar
```

The system uses a hybrid approach where LLMs handle reasoning and interpretation, while traditional backend logic handles deterministic tasks such as scoring, sorting, dates, storage, and validation.

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
