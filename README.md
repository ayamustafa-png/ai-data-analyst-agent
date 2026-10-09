# Data Analyst Agent

[![tests](../../actions/workflows/tests.yml/badge.svg)](../../actions/workflows/tests.yml)

An AI agent that takes a CSV and a business question, then investigates the data on its own: it profiles the dataset, plans the analysis, writes and runs Python, validates the result, and explains the insights with numbers traced back to the evidence.

> Arabic version: [README.ar.md](README.ar.md)

## Why an agent, not a chatbot

The agent understands a goal, chooses its steps, uses tools, verifies its own work, and only then acts. If the code fails, it reads the error and retries. If the question cannot be answered with the available columns, it asks for clarification instead of guessing.

## Architecture

```
USER question + CSV
  -> profile_data      (tool 1: schema, nulls, duplicates, quality warnings)
  -> Planner (LLM)     (JSON plan; infeasible question -> ask user to clarify)
  -> Code generator    (LLM)
  -> Guardrails        (AST check: no os/subprocess/file IO/dunder access)
  -> run_python        (tool 2: separate process + timeout, saves charts)
  -> Validate result   (not empty / not NaN) -- fail -> retry with error feedback (max 3)
  -> Explain (LLM)
  -> Verify numbers    (every number in the text must exist in the result)
  -> export_report     (tool 3: action, gated by verification)
```

## Project requirements mapping

| Requirement | Where |
|---|---|
| Working MVP with a clean user flow | `app.py` (Streamlit) |
| At least 2 meaningful tools | `agent/tools.py`: `profile_data`, `run_python`, `export_report` |
| Clear agent state and decision flow | `agent/state.py`, `agent/agent.py`, trace shown in the UI |
| Verification / guardrails before important actions | `agent/guardrails.py`; export requires verified numbers or human confirmation |
| Short demo of a realistic scenario | see below |

## Quick start

```bash
pip install -r requirements.txt
python generate_sample_data.py          # creates sample_data/ecommerce_orders.csv
export GEMINI_API_KEY=your_key          # never commit your key
streamlit run app.py
pytest -q                               # tests run with a fake LLM, no key needed
```

The LLM is a plain callable (`llm(prompt) -> str`) in `agent/llm.py`, so swapping Gemini for another provider means editing one function.

## Demo scenario

1. Upload `ecommerce_orders.csv`. The profile flags duplicates, missing discounts and negative quantities.
2. Ask: *Which product categories have declining sales in the last 3 months?* The agent finds Electronics, draws a chart and explains.
3. Ask: *Which marketing channel has the best return on marketing cost?* Organic is highest (near-zero cost), Email is the best paid channel, Paid Social the worst.
4. Ask: *What is the average customer age?* There is no age column, so the agent asks for clarification.
5. Open **Agent trace** to see the plan, generated code and retries.

## Limitations and scaling path

- Code runs in a separate process with an AST check and a timeout, which is not a full sandbox. For production, use Docker or gVisor.
- Scale to warehouses (BigQuery/Postgres), scheduled reports, Slack alerts, and an evaluation set of fixed questions to track quality.
