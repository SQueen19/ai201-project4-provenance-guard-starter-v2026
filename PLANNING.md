# Milestone 1 — Planning

Written before building anything. The numbers marked *(calibrate in M4)* are
starting positions to test in Milestone 4. They aren't conclusions.

---

## 1. The path a submission takes

| # | Where | What it adds |
|---|---|---|
| 1 | **`POST /submit` arrives at Flask** (`app.py::submit`) | Parses the body into a dict. Nothing has been judged yet. |
| 2 | **The input gate** (in `submit`, before any scoring) | Refuses anything that can't be judged honestly: body isn't a JSON object, `text`/`creator_id` missing or not strings, fewer than 50 words, more than 10,000 characters. A refusal returns a 4xx and is written to the log with `audit.log_rejection`. It never reaches a model. |
| 3 | **Signal one — `detector.model_signal`** | Runs gpt2 over the **first 400 tokens** (~300 words) and turns perplexity into `model_score` (0–1, higher = more AI-like). |
| 4 | **Signal two — `stylometry.style_signal`** | Measures the **whole** text's shape (sentence-length spread, type-token ratio, punctuation density) and returns `style_score` (0–1, same direction). |
| 5 | **The combining rule — `scoring.combine_signals`** | Turns two scores into one `combined_score`. This step decides what happens when the signals disagree. |
| 6 | **The label — `scoring.score_to_label`** | Turns the number into a `guess` (`human` / `unsure` / `ai`) and a sentence a person can read. This is the only thing most readers will ever see. |
| 7 | **Record and reply** (`uuid4` → `audit.log_decision` → JSON response) | Gives the decision a `content_id`, appends all nine fields to `logs/audit.jsonl` with `status: "decided"`, then returns the label, both signal scores and the `content_id`. The writer needs that ID to appeal. |

The log is written **before** the response is sent. If logging fails, the
request fails, so no decision can exist without a record.

---

## 2. The two signals

### Signal one — `detector.py` (the model signal)

**What it measures.** How predictable the text is to gpt2, which is its
perplexity, squashed onto 0–1. Perplexity 45 maps to 0.5, and anything less
predictable than that scores lower.

**Why it might differ.** An LLM generates by picking likely next words, so its
output tends to be text a model finds easy to predict. Humans make odd,
specific choices that a model doesn't expect.

**What it can't see.**
- **Authorship.** It sees predictability, and plain writing is predictable too.
  I measured this on the cached gpt2:

  | Text | Perplexity | `model_signal` |
  |---|---|---|
  | Plain first-person paragraph (short sentences, common words: an ESL-style personal statement I wrote as a stand-in) | 12.1 | **0.891** |
  | The generic AI paragraph from `detector.py` | 12.5 | **0.886** |
  | Ornate human prose (rare words, one long sentence) | 247.0 | 0.062 |

  On this signal the plain writer and the machine are tied. No threshold can
  separate them.
- **Anything past ~300 words.** It truncates at 400 tokens, so the rest of the
  text never reaches it.
- **Which model wrote it.** It measures predictability *to gpt2* (2019). A
  modern model sampled at high temperature, or AI text a thesaurus pass has
  sprinkled with rare words, can look surprising and read as human.
- **Quotation and memorized text.** A pasted famous passage is extremely
  predictable because gpt2 saw it in training, so it scores as AI.

### Signal two — `stylometry.py` (the style signal)

**What it measures.** The shape of the text, without reading it:
- **sentence-length spread:** stdev ÷ mean of words per sentence. Low spread
  points to AI, so this one gets flipped.
- **type-token ratio:** unique words ÷ total words. Low variety points to AI,
  so this one gets flipped too.
- **punctuation density:** semicolons, dashes, colons, parentheses and
  question/exclamation marks per sentence. Sparse, uniform punctuation points
  to AI.

**Why it might differ.** "Most likely next word" produces even, mid-length
sentences and a safe vocabulary. Human writing is lumpier: a three-word
sentence next to a forty-word one.

**What it can't see.**
- **Meaning.** It can't read. Shape changes that leave the substance alone move
  it freely: typos, a split sentence, a pasted quotation, a few em dashes. All
  of that is cheap to do on purpose.
- **Length effects.** Type-token ratio falls as text gets longer, so length
  alone can look like a signal.
- **The same plain writer.** Short, even sentences, repeated common words and
  only full stops all read as AI-like here too. **This is the important part:
  both blind spots point the same way for the same person.** A plain writer
  isn't one signal's error that the other cancels out. Both signals make the
  same mistake about them.

---

## 3. Tracing the false positive

**The person.** Ana writes a 96-word personal statement in her second
language. She uses short sentences and words she's sure of, every sentence
ends with a full stop, and every word is her own. (The paragraph in the table
above is a stand-in for her.)

**What she scores, with the starter as it stands.**
- `model_score` = **0.891** (measured above).
- `style_score` = 0.5 while the stub is in place. Once it's built, I expect it
  to land high, roughly 0.7: her sentences are 8–12 words each, her vocabulary
  repeats, and she uses only full stops.
- `combined` at the placeholder 0.5/0.5 weights:
  - with the stub: 0.5 × 0.891 + 0.5 × 0.5 = **0.70**
  - with a working style signal: 0.5 × 0.891 + 0.5 × 0.7 = **0.80**
- `AI_THRESHOLD` is 0.65, so either way she gets **high-confidence AI**.

**What the label tells her.** Today it's a placeholder string. Once written, it
would be some version of "this was probably written by AI", attached to work
she wrote herself, and it may be shown to other people as well.

**What she can do.** Only one thing: `POST /appeal` with her `content_id` and
a reason. That moves her item to `under_review` in the log. Nothing re-scores
it, nobody is notified, and the original decision stays in the log as written.
If the response didn't show her the `content_id`, or the label didn't tell her
appealing was possible, she can do nothing at all.

**What this decides about thresholds** *(calibrate in M4)*:
1. **The model signal must never produce an AI label on its own**, because it
   can't separate Ana from a machine. Rule: `ai` requires `combined ≥ 0.80`
   **and** `style_score ≥ 0.70`, so both signals have to agree independently.
   Anything that fails either test drops to `unsure` at most.
2. **The unsure band is wide on purpose:** human ≤ 0.30, unsure 0.30–0.80,
   AI ≥ 0.80. More AI text will land in "unsure". That's the cost I'm choosing,
   because missing AI text costs the site a little and accusing Ana costs her a
   lot.
3. **This still might not save Ana**, since her style score may clear 0.70 as
   well. Milestone 4's job is to run her paragraph through the real style
   signal and find out. If she still lands on `ai`, the fix belongs upstream
   (what the style signal measures), and the threshold stays where it is.
4. **The `ai` and `unsure` labels must tell the reader the result can be
   wrong and can be appealed**, and the response must always carry the
   `content_id`.

---

## 4. The endpoint contracts

All requests and responses are JSON (`Content-Type: application/json`). Every
error has the same shape:

```json
{"error": "<machine_code>", "message": "<one sentence a person can read>"}
```

Every rejected request is logged with `audit.log_rejection`, including the
`error` code as `reason`.

### `POST /submit`

**Request body:** a JSON object. Fields it doesn't recognise are ignored.

| Field | Type | Rules |
|---|---|---|
| `text` | string | Required. After trimming spaces: at least **50 words** (counted by `stylometry.words`) and at most **10,000 characters**. |
| `creator_id` | string | Required. 1–64 characters after trimming. Not verified. It's whatever the caller says it is. |

**200 response:**

| Field | Type | Meaning |
|---|---|---|
| `content_id` | string | New `uuid4` in canonical form (`"3f2b…-…"`). New on every call, so the same text sent twice gets two IDs. Needed for `/appeal`. |
| `creator_id` | string | The trimmed `creator_id` that was sent. |
| `guess` | string | Exactly one of `"human"`, `"unsure"`, `"ai"`. **Code should branch on this field, not on `label`.** |
| `confidence` | number | The combined score, 0–1, 4 decimal places. **Higher means more AI-like, whatever the guess.** It is *not* "how sure we are of the guess". A `human` guess has a low confidence number. |
| `label` | string | The full sentence shown to a reader. The wording may change, so don't parse it. |
| `model_score` | number | Signal one, 0–1, 4 dp, higher = more AI-like. |
| `style_score` | number | Signal two, 0–1, 4 dp, higher = more AI-like. |
| `status` | string | Always `"decided"` on this endpoint. |

**Label boundaries:** `confidence ≤ HUMAN_THRESHOLD` (0.30) → `human`;
`confidence ≥ AI_THRESHOLD` (0.80) → `ai`; everything else → `unsure`. The
style-agreement rule lives in `scoring.combine_signals`: when `style_score` is
below 0.70, `confidence` is capped at 0.7999, so `ai` needs both signals to
agree. In that case `confidence` is lower than the plain average of the two
scores. All the numbers live in `config.py`.

**Errors:**

| Status | `error` | When |
|---|---|---|
| 400 | `invalid_json` | The body is missing, isn't JSON, or isn't a JSON object |
| 400 | `missing_field` | `text` or `creator_id` is missing, not a string, or empty after trimming. `message` names the field. |
| 400 | `text_too_short` | Fewer than 50 words |
| 413 | `text_too_long` | More than 10,000 characters |
| 429 | `rate_limited` | Unit 8. Shape already in `app.py`, plus a `limit` field |
| 503 | `detector_unavailable` | The model couldn't load (`DetectorUnavailable`) |

Scores come from a model, so the same text can differ in the last decimal
between machines. Don't compare scores for exact equality.

### `POST /appeal`

**Request body:**

| Field | Type | Rules |
|---|---|---|
| `content_id` | string | Required. Must match a `decided` entry in the log. |
| `reasoning` | string | Required. 1–2,000 characters after trimming. |

The `creator_id` on the appeal record is copied from the original decision. It
is never taken from the request. Anyone who holds a `content_id` can appeal it.

**200 response:**

| Field | Type | Meaning |
|---|---|---|
| `content_id` | string | Echoed back. |
| `status` | string | Always `"under_review"`. |
| `message` | string | A plain confirmation for the writer, e.g. "Your appeal has been recorded and this result is now under review." |

Appealing the same item again is allowed. Each appeal is logged and gets the
same 200, so extra reasoning is never thrown away. An appeal does not re-score
the text or change the original decision entry. The log is append-only.

**Errors:**

| Status | `error` | When |
|---|---|---|
| 400 | `invalid_json` | Same rule as `/submit` |
| 400 | `missing_field` | `content_id` or `reasoning` is missing, not a string, or empty after trimming |
| 400 | `reasoning_too_long` | More than 2,000 characters |
| 404 | `unknown_content_id` | No decision with that ID exists in the log. This is never a silent success. |

### Read-back: could someone build against this without asking me?

Questions I checked it against:
- *What does `confidence` mean for a human guess?* Answered: it's the
  AI-likeness score, not certainty in the guess.
- *What happens at exactly 0.80?* Answered: `≥` gives `ai`, provided the style
  rule also passes.
- *Are words or characters the limit?* Answered: words for the minimum,
  characters for the maximum.
- *Can I branch on `label`?* Answered: no, use `guess`.
- *Does a second appeal fail?* Answered: no, it's logged and returns 200.

One thing still open: **who acts on `under_review`?** Nothing in this system
reviews an appeal. The contract records the appeal honestly and promises
nothing beyond that, and the `/appeal` message must not promise a timeline or
an outcome.
