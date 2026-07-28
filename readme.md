# Bantay-Wika

_A cultural-bias benchmark that audits large language models for systematic failures in Tagalog and Filipino cultural contexts._

Bantay-Wika ("language watchdog") tests whether models — which learn mostly from English and Western text — handle Tagalog the way a culturally aware Filipino speaker would: using proper honorifics, reasoning within Filipino relational values, avoiding stereotypes, and recognizing that Tagalog is not the only Philippine language. It is an open-source evaluation suite: a dataset of Tagalog test items, a runner that queries any model through OpenRouter, and a hybrid grader.

Built for the OpenAI Research grant _"Open-Source Eval: A Cultural Bias Benchmark in a Language You Speak."_

## Why it matters

Tens of millions of people use AI in Tagalog. When a model flattens honorifics, gives culturally tone-deaf advice, or defaults to the OFW / domestic-helper stereotype, the harm is real: disrespect, bad guidance, and erasure. An open, reproducible benchmark lets developers _measure_ these failures instead of assuming they don't exist.

## What it tests

Seven categories of cultural failure (full definitions and examples in [`taxonomy.md`](taxonomy.md)):

1. **Paggalang at Rehistro** — respect & register (_po/opo_, _kayo_, kinship address)
2. **Pagpapahalagang Panlipunan** — social values (_utang na loob_, _hiya_, _pakikisama_, _kapwa_)
3. **Representasyon at Estereotipo** — representation & stereotyping
4. **Wikang Matalinghaga** — figurative language (_salawikain_)
5. **Taglish / code-switching**
6. **Kaalamang Kultural** — cultural & historical knowledge
7. **Kamalayang Panrehiyon** — regional & linguistic awareness

## Repo structure

```
bantay-wika/
├── data/items.json     # the test items (prompt + rubric per item)
├── src/
│   ├── models.py       # OpenRouter + offline Mock providers
│   ├── grader.py       # deterministic rule checks + LLM-as-judge
│   └── run_eval.py     # loads items, runs a model, grades, writes a report
├── runs/               # timestamped results (results.json + report.md)
├── taxonomy.md         # category definitions
├── writeup.md          # findings
└── requirements.txt
```

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repo root with an OpenRouter key (from openrouter.ai):

```
OPENROUTER_API_KEY=sk-or-v1-...
```

## Running

Offline plumbing test — no key, no cost, confirms the pipeline works:

```bash
python3 src/run_eval.py --provider mock --no-judge
```

Real run against a model, graded by an independent judge:

```bash
python3 src/run_eval.py --model "MODEL_UNDER_TEST" --judge-model "JUDGE_MODEL"
```

Useful flags: `--limit N` (first N items only), `--no-judge` (rule checks only, halves API calls), `--provider mock` (offline fake). To compare two models, run twice with different `--model` values and diff the two reports.

Results are written to `runs/<timestamp>/`:

- `report.md` — readable scoreboard, per-category scores, and a list of failing items with the judge's reasoning.
- `results.json` — every model answer and judge rationale in full.

## How scoring works

Each answer gets two signals. **Rule checks** are deterministic regex tests from the item (e.g. is _po_ present when an elder is addressed). The **LLM-as-judge** scores the answer against the item's rubric on a 0.0 / 0.5 / 1.0 scale and returns a short rationale. The judge's score is used, but a hard rule failure caps it — a fluent answer that drops required honorifics cannot score full marks.

Two design choices protect validity:

- **Independent judge.** The judge should be a _different_ model from the one under test, so a model never grades its own blind spots.
- **Errors are excluded.** Items that fail for infrastructure reasons (provider rate limits or capacity errors) are reported separately and left out of the scores, so "the server was busy" never counts as "the model is bad at Tagalog."

## Models

Any model on OpenRouter works — pass its ID to `--model`. Free model IDs rotate often; check the Free filter at openrouter.ai/models before a big run. Cultural-nuance judging benefits from a strong, ideally multilingual judge.

## License

_(Add a license file — MIT or Apache-2.0 is recommended for an open-source eval.)_

## Acknowledgements

Test items were authored and vetted by a fluent Tagalog speaker; authenticity of the items is central to the benchmark's purpose.
