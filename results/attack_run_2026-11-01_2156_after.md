# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-01 21:56
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `dc6824bf-fda5-44e4-b1ca-28a92d962e06` | unsure | 0.386 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `9e20664d-6ae6-4630-9c29-dea910e465d2` | unsure | 0.307 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `2e770a4a-06d1-4d76-91ab-824cd6aa91d8` | unsure | 0.396 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `3d5b5171-8bb4-4a54-b307-0dc6ab17dd29` | unsure | 0.606 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `530e08aa-bd0a-4660-92d5-210636c98c49` | human | 0.264 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `50b4419f-9edc-47db-aa1d-0a81b1017887` | unsure | 0.370 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `59ddf049-f5d2-43fa-9e06-db6b4d2ebefc` | unsure | 0.428 |  |
| EV08 | evasion | signal one: text below the token window | 400 | `—` | — | — |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `c287cdf9-4ab1-48ea-b34b-45be6d421504` | unsure | 0.474 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `91925943-7a41-4578-9b0e-1dacac2189fb` | unsure | 0.756 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `6aaa4a7f-573e-4bfb-a9d8-8a172b2ea251` | unsure | 0.465 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `4f2a9503-a7aa-4998-86ea-f00a9dc4809f` | unsure | 0.702 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `71a72278-ff64-4a34-9d3e-7204aeb064f5` | unsure | 0.641 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `9ee306df-bdce-448a-bd9e-cfb670f79fd4` | unsure | 0.624 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `b8da1a7b-fb92-4f02-9a17-bd12e696d121` | unsure | 0.753 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `ab95e151-a3b7-4e5e-a8c9-c5eb4fb64250` | unsure | 0.612 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `8c1497b7-147e-448f-b886-2759229800ae` | unsure | 0.618 |  |
| FP08 | false_positive | very short genuine human submission | 400 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 400 | `—` | — | — |  |
| PI02 | prompt_injection | instruction disguised as a system message | 400 | `—` | — | — |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `65fbc8d8-0048-43c8-9619-27da79d9fd5c` | unsure | 0.428 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `dfdaf6b9-7aae-4922-8bb4-6028465746a4` | unsure | 0.349 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 400 | `—` | — | — |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `bc870e23-4f32-4559-8cf8-ba48e6af59c7` | unsure | 0.438 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 400 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 400 | `—` | — | — |  |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 400 | `—` | — | — |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 400 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 400 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 400 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "dc6824bf-fda5-44e4-b1ca-28a92d962e06",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.3858,
  "model_score": 0.1635,
  "style_score": 0.6081,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "9e20664d-6ae6-4630-9c29-dea910e465d2",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.307,
  "model_score": 0.5943,
  "style_score": 0.0196,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "2e770a4a-06d1-4d76-91ab-824cd6aa91d8",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.3962,
  "model_score": 0.6662,
  "style_score": 0.1261,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "3d5b5171-8bb4-4a54-b307-0dc6ab17dd29",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.6062,
  "model_score": 0.6114,
  "style_score": 0.601,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "530e08aa-bd0a-4660-92d5-210636c98c49",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.2636,
  "model_score": 0.3212,
  "style_score": 0.2061,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "50b4419f-9edc-47db-aa1d-0a81b1017887",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.3705,
  "model_score": 0.5727,
  "style_score": 0.1683,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "59ddf049-f5d2-43fa-9e06-db6b4d2ebefc",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.4283,
  "model_score": 0.5862,
  "style_score": 0.2703,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_EV08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "c287cdf9-4ab1-48ea-b34b-45be6d421504",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.4745,
  "model_score": 0.7042,
  "style_score": 0.2447,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "91925943-7a41-4578-9b0e-1dacac2189fb",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.7561,
  "model_score": 0.9792,
  "style_score": 0.5331,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "6aaa4a7f-573e-4bfb-a9d8-8a172b2ea251",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.4648,
  "model_score": 0.6175,
  "style_score": 0.3122,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "4f2a9503-a7aa-4998-86ea-f00a9dc4809f",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.7024,
  "model_score": 0.7387,
  "style_score": 0.666,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "71a72278-ff64-4a34-9d3e-7204aeb064f5",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.6407,
  "model_score": 0.8051,
  "style_score": 0.4762,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "9ee306df-bdce-448a-bd9e-cfb670f79fd4",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.6237,
  "model_score": 0.8329,
  "style_score": 0.4145,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "b8da1a7b-fb92-4f02-9a17-bd12e696d121",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.7531,
  "model_score": 0.8005,
  "style_score": 0.7057,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "ab95e151-a3b7-4e5e-a8c9-c5eb4fb64250",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.6116,
  "model_score": 0.8814,
  "style_score": 0.3418,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "8c1497b7-147e-448f-b886-2759229800ae",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.6179,
  "model_score": 0.8816,
  "style_score": 0.3542,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_PI01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_PI02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "65fbc8d8-0048-43c8-9619-27da79d9fd5c",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.4285,
  "model_score": 0.5943,
  "style_score": 0.2628,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "dfdaf6b9-7aae-4922-8bb4-6028465746a4",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.3486,
  "model_score": 0.4998,
  "style_score": 0.1973,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_PI05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "bc870e23-4f32-4559-8cf8-ba48e6af59c7",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.4376,
  "model_score": 0.5583,
  "style_score": 0.317,
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
