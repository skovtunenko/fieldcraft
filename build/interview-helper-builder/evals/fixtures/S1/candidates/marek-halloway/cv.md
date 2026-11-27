# Marek Halloway

Lead AI Engineer - Remote (EU)

## Summary

AI engineer and technical lead with nine years of production ML and three
years of LLM agent work in insurance and logistics. Designs agentic workflows
end to end, from tool contracts to evaluation and release, and leads small
delivery teams.

## Skills

- **Languages:** Python, SQL, some Go
- **LLM:** LangGraph, OpenAI and Anthropic APIs, pgvector, OpenSearch
- **Backend:** FastAPI, PostgreSQL, Redis, Celery, pytest
- **Cloud and ops:** AWS (ECS, Lambda, S3), Docker, Terraform, Grafana

## Experience

### AI Tech Lead - Tessaline Software

03.2021 - present

- Lead a team of five engineers delivering LLM features for insurance and
  logistics clients.
- **Claims-triage assistant** for a mid-size insurer: LangGraph agent with six
  tools (policy lookup, coverage check, fraud-score API, document OCR, human
  handoff, notes writer). Processes about 3,000 claims per day.
- **Built the evaluation harness for the triage assistant from scratch:** a
  420-case golden set labelled with claims adjusters, per-release tracking of
  faithfulness, escalation precision and recall, and tool-call success rate.
  Releases were blocked automatically on any regression above 2 points.
- Retrieval over 18,000 policy documents: section-aware chunking, per-tenant
  access filtering at query time, nightly re-index.
- Wrote the process specification for first-notice-of-loss intake together
  with the client's operations team.
- Introduced design reviews and a Python code standard (type hints, pytest,
  85% coverage gate) across three client teams.

### Senior ML Engineer - Corvid Analytics

06.2017 - 02.2021

- Demand-forecasting models for a regional grocery chain; reduced stock-outs
  by 11% in the pilot stores.
- FastAPI model-serving layer and Airflow retraining pipelines.
- Mentored two junior engineers.

### ML Engineer - Brindle Labs

09.2014 - 05.2017

- Computer-vision defect detection for packaging lines (PyTorch, OpenCV).

## Education

MSc Computer Science, 2014

## Languages

English (fluent), German (intermediate)
