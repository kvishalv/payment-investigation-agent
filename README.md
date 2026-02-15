# Payment Investigation Agent

A 12-week journey building a production-grade AI agent for autonomous payment anomaly investigation.

## Overview

Building an AI agent that can investigate payment failures and anomalies by querying logs, checking API responses, correlating events, and generating root cause analysis reports.

## Learning Path

- **Weeks 1-2**: Foundations (Prompt engineering, LangChain basics, agent patterns)
- **Weeks 3-5**: Agent v1 (Core investigation loop with 3 tools)
- **Weeks 6-7**: Evaluation & Guardrails (Production safety and testing)
- **Weeks 8-9**: Production Grade (Observability, error handling, edge cases)
- **Weeks 10-11**: Advanced Techniques (RAG, memory, advanced prompting)
- **Week 12**: Documentation & Sharing (Blog post, demo, open source)

## Progress

See [weekly-progress.md](docs/weekly-progress.md) for detailed updates.

## Tech Stack

- Python 3.11+
- Claude (Anthropic)
- LangChain
- LangSmith (tracing)
- Streamlit (UI)

## Getting Started

Each week's folder contains its own README with specific instructions.

## Learning Journal

Daily learnings and insights in [learning-journal.md](docs/learning-journal.md)
```

**.gitignore**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
dist/
*.egg-info/

# Jupyter
.ipynb_checkpoints
*.ipynb_checkpoints

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# LangSmith
.langsmith/

# Data
*.csv
*.json
data/*
!data/.gitkeep
results/*
!results/.gitkeep

# Logs
*.log
logs/
```

**requirements.txt**
```
anthropic>=0.18.0
langchain>=0.1.0
langchain-anthropic>=0.1.0
langchain-community>=0.0.20
python-dotenv>=1.0.0
streamlit>=1.31.0
pydantic>=2.0.0
pytest>=8.0.0