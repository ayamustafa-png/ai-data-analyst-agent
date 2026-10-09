# Data Analyst Agent

Agent بيستقبل CSV وسؤال business، ويحقق في الداتا بنفسه: يعمل profile، يخطط، يكتب كود Python وينفذه، يتحقق من النتيجة، ويشرح الـ insights بأرقام مثبتة.

## التشغيل

```bash
pip install -r requirements.txt
python generate_sample_data.py        # creates sample_data/ecommerce_orders.csv
export GEMINI_API_KEY=your_key
streamlit run app.py
pytest -q                              # tests (no API key needed)
```

## Architecture

```
USER question + CSV
  → profile_data      (tool 1: schema, nulls, duplicates, warnings)
  → Planner (LLM)     (JSON plan; if infeasible → asks the user to clarify)
  → Code generator    (LLM)
  → Guardrails        (AST check: no os/subprocess/file IO/dunder)
  → run_python        (tool 2: separate process + timeout, saves charts)
  → Validate result   (not empty / not NaN) ── fail → retry with error feedback (max 3)
  → Explain (LLM)
  → Verify numbers    (every number in the text must exist in the result)
  → export_report     (tool 3: action, gated by verification)
```

## تحقيق شروط الـ brief

| الشرط | فين في الكود |
|---|---|
| Working MVP + clean flow | `app.py` |
| 2+ meaningful tools | `agent/tools.py`: `profile_data`, `run_python`, `export_report` |
| Agent state + decision flow | `agent/state.py` + `agent/agent.py` + trace في الـ UI |
| Verification / guardrails | `agent/guardrails.py` (code safety, columns, result, numbers) + human confirm قبل export لو فيه أرقام مش متحققة |
| Demo | السيناريو تحت |

## Demo scenario (3 دقايق)

1. ارفعي `ecommerce_orders.csv`: الـ profile هيحذر من duplicates و missing discounts و quantities سالبة.
2. اسألي: **"Which product categories have declining sales in the last 3 months?"** ← هيطلع Electronics + chart + insights.
3. اسألي: **"Which marketing channel has the best return on marketing cost?"** ← Organic الأعلى (تكلفته شبه صفر)، وEmail أفضل قناة مدفوعة، وPaid Social الأسوأ.
4. اسألي: **"What is the average customer age?"** ← الـ agent هيرفض ويطلب توضيح لأن مفيش عمود age (guardrail).
5. افتحي **Agent trace** عشان تورّي الـ plan، الكود، والـ retries.

## Limitations & Scaling path

- التنفيذ في process منفصل + AST check + timeout، لكنه مش sandbox كامل. للـ production استخدمي Docker/gVisor.
- Scale: ربطه بـ warehouse (BigQuery/Postgres)، scheduled reports، Slack alerts، وتقييم الجودة بمجموعة أسئلة ثابتة (eval set).
