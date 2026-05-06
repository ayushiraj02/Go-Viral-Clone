# Go Viral Clone

A web app that analyzes a creator post and returns a virality score with clear, actionable feedback.

## Quick start

```bash
cd go-viral-clone
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

## Project structure

- web/ - Static frontend
- backend/ - FastAPI backend
- ai-logs/ - AI conversation logs required for submission

## Notes

This project uses a transparent heuristic model (no paid APIs).
