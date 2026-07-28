# Bantay-Wika: A Cultural-Bias Benchmark for Tagalog

## Motivation

Large language models are trained overwhelmingly on English and Western text, so
their competence in other languages is uneven in ways that are not random but
systematic and cultural. In Tagalog — spoken by tens of millions of Filipinos — a
model can produce grammatically fluent output while failing the cultural
expectations that govern real communication: using the wrong register with an
elder, giving advice that ignores _utang na loob_ and _hiya_, translating a
_salawikain_ literally, or defaulting to the tired OFW / domestic-helper
stereotype. These are not edge cases; they are everyday interactions for millions
of users. Bantay-Wika ("language watchdog") makes such failures measurable, so
they can be tracked and fixed rather than assumed away.

## What it tests

The benchmark defines seven categories of cultural failure (with an optional
eighth on folk-medicine safety), authored by a fluent Tagalog speaker: respect and
register (_po/opo_, _kayo_), social-values reasoning (_utang na loob_, _hiya_,
_pakikisama_, _kapwa_), representation and stereotyping, figurative language,
Taglish code-switching, cultural and historical knowledge, and regional awareness
(that Tagalog is not the only Philippine language). Each of the [N] items pairs a
realistic Tagalog prompt with a rubric stating what a culturally competent answer
must include and must avoid.

## Method

Each answer is scored two ways. Deterministic rule checks catch mechanical
requirements — for example, the presence of _po_ where an elder is addressed. An
LLM-as-judge then scores the answer against the item's rubric on a 0.0 / 0.5 / 1.0
scale and returns a short rationale. The judge's score is final, but a hard rule
failure caps it: a fluent-sounding reply that drops required honorifics cannot earn
full marks. Two choices protect validity. The judge is a _different_ model from the
one under test, so no model grades its own blind spots, and a sample of verdicts
was checked by hand against the author's own judgment. Items that fail for
infrastructure reasons — provider rate limits or capacity errors — are excluded
from the scores and reported separately, so "the server was busy" never
masquerades as "the model is bad at Tagalog." All models are queried through
OpenRouter, so the identical suite runs unchanged across providers.

## Results

> INSERT after your full run. State which models you tested and which judge you
> used; give the overall score per model, the per-category table, and two or three
> concrete failure examples with the judge's rationale. A real finding you already
> have: on the honorifics item, [MODEL] returned a _menu_ of message options — one
> respectful, but others casually addressing a grandmother with _ka/mo_ — earning a
> 0.5. That is a subtle register failure a keyword check alone would miss, and
> exactly the kind of thing this benchmark exists to surface.

| Category       | [Model A] | [Model B] |
| -------------- | --------- | --------- |
| respeto        | [ ]       | [ ]       |
| pagpapahalaga  | [ ]       | [ ]       |
| representasyon | [ ]       | [ ]       |
| matalinghaga   | [ ]       | [ ]       |
| taglish        | [ ]       | [ ]       |
| kaalaman       | [ ]       | [ ]       |
| panrehiyon     | [ ]       | [ ]       |
| **Overall**    | [ ]       | [ ]       |

## Limitations

This is an early, deliberately narrow benchmark. The item count is modest, so
category scores are indicative rather than definitive. The LLM-judge, however
carefully prompted, may share cultural blind spots with the models it grades;
human spot-checking mitigates but does not remove this. Items were authored by a
single fluent speaker, reflecting one person's dialect and cultural vantage rather
than the full diversity of Filipino experience — and the suite covers Tagalog
specifically, not the many other Philippine languages. Finally, rubrics encode
judgment calls (is offering a casual option to an elder a partial failure?) that
reasonable Filipinos might weigh differently.

## Future work

Priorities are expanding item coverage, adding a second annotator to measure
inter-rater agreement, and probing figurative language _in use_ rather than only in
definition. The suite is open source and fully reproducible: `python3
src/run_eval.py` reruns the entire evaluation, and every model answer and judge
rationale is saved for inspection.
