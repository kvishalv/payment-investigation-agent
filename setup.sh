#!/bin/bash

# Create main directories
mkdir -p docs shared/config shared/common

# Create week 1-2 structure
mkdir -p week-01-02-foundations/{day-01-prompt-engineering,day-02-tool-use,day-03-structured-outputs,day-04-langchain-basics,day-05-first-agent,day-06-react-pattern,day-07-memory,day-08-multi-tool,day-09-tracing,day-10-guardrails,weekend-ui}

# Create week 3-5 structure
mkdir -p week-03-05-agent-v1/{src/{tools,prompts,utils},tests,data,notebooks}

# Create week 6-7 structure
mkdir -p week-06-07-evaluation/{evaluation,guardrails,results}

# Create week 8-9 structure
mkdir -p week-08-09-production/{src/{observability,error_handling,edge_cases},tests/{integration,e2e}}

# Create week 10-11 structure
mkdir -p week-10-11-advanced/{rag,memory,experiments}

# Create week 12 structure
mkdir -p week-12-documentation/{demo,open-source-prep/examples}

# Create .gitkeep files
touch week-03-05-agent-v1/data/.gitkeep
touch week-06-07-evaluation/results/.gitkeep

echo "Folder structure created!"