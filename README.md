# MyArc

MyArc is a multi-agent semester planning platform that helps students quickly see **which courses need the most attention, when their workload will peak, and why**.

Motivation: Students can already ask tools like ChatGPT, Claude, or Gemini to analyze their semester, but chatbox responses often make it difficult to see the bigger picture **quickly**. MyArc takes a different approach: instead of acting as another chatbot, it uses a team of AI agents behind the scenes to analyze course syllabi, deadlines, workload patterns, and external course discussions from sources such as Reddit and RateMyProfessors.

The results are presented visually through **course rankings, workload calendars, milestone timelines, and evidence-backed insights**, so students can understand their semester at a glance rather than digging through long conversations with AI.

**MyArc prioritizes visualization.** 

## Demo

> 🎬 Demo video coming soon.

**What the demo shows**
1. Add a course: type the course code, pick the term, upload the syllabus (PDF or .docx)
2. The agents read the syllabus and research Reddit in parallel (~20–40s)
3. The dashboard ranks every course S–D, with weekly hours, confidence and an 8-week load view
4. **Why?** opens the evidence behind a rank: six scores, each tied to a syllabus line or student post

## Goal

MyArc is being built as a production-oriented project with a focus on real users, reliable AI reasoning, explainable recommendations, and a clean visual experience.

The goal is simple:

> **Help students see their semester before it hits them.**

## Features

- Upload and analyze multiple course syllabi
- Rank courses by difficulty, workload, and priority
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

For now, tne syllabus upload runs three agents. The student types the course code, so Research doesn't have to wait for the syllabus: **Syllabus and Research run in parallel**, then the **Evaluator** combines both.

```text
syllabus file ──► Syllabus Agent ──┐
                                   ├──► Evaluator ──► rank + scores + evidence
course code ────► Research Agent ──┘
```

**Syllabus Agent** (`app/agents/syllabus/`)
Reads the PDF or .docx and extracts the course code, title, term, instructors, graded assessments (weights and dates) and key policies. Code checks every quote against the file, and the agent gets one chance to fix real problems (weights that don't add up, dates outside the term).

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

The weighted total gives the course's point and its rank: S ≥ 80, A ≥ 70, B ≥ 50, C ≥ 35, D otherwise. 

## Pipeline Speed

The first working version took about **90 seconds** per syllabus. We added timing logs to every stage first, measured, and only then changed things. Four changes brought it down to **20–40 seconds**.

| Stage | CMPUT 365 before | CMPUT 365 after | CMPUT 340 before | CMPUT 340 after |
|---|---|---|---|---|
| Syllabus Agent | 52.3s | 12.5s | 23.3s | 11.8s |
| Research Agent | 23.7s | 10.9s | 55.3s | 33.7s |
| Evaluator | 10.1s | 6.2s | 12.6s | 4.6s |
| **Total** | **86.3s** | **19.3s** (4.5× faster) | **91.9s** | **38.7s** (2.4× faster) |

After the parallel change, the Syllabus and Research rows overlap, so they no longer add up to the total.


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
