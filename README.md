# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

Provenance Guard takes a piece of writing and tells a reader, in plain words,
whether it was probably written by a person, probably by AI, or whether it
can't tell. Every decision is logged, and a writer can appeal.

1. **`POST /submit` arrives** (`app.py::submit`). Flask parses the JSON body
   into a dict. Nothing has been judged yet.
2. **The input gate.** Text that can't be judged honestly is refused before
   any scoring: a body that isn't a JSON object, a missing or empty `text` or
   `creator_id`, fewer than 50 words, or more than 10,000 characters. Each
   refusal gets a 4xx with an error code and is logged with
   `audit.log_rejection`.
3. **Signal one** (`detector.model_signal`). gpt2, running locally, measures
   how predictable the first ~300 words are. This becomes `model_score`, 0–1,
   higher = more AI-like.
4. **Signal two** (`stylometry.style_signal`). Measures the whole text's
   shape (sentence-length spread, vocabulary variety, expressive punctuation)
   without reading it. This becomes `style_score`, on the same scale.
5. **The combining rule** (`scoring.combine_signals`). A 50/50 average, except
   that "AI" needs the style signal to agree. This produces `confidence`.
6. **The label** (`scoring.score_to_label`). Turns the score into a guess
   (`human` / `unsure` / `ai`) and the sentence a reader actually sees.
7. **Record and reply.** The decision gets a new `content_id`, all nine
   fields are appended to `logs/audit.jsonl` (before the reply goes out, so
   no decision exists without a record), and the response returns the label,
   both signal scores and the `content_id`. A writer who disagrees sends that
   ID to `POST /appeal`, which logs the appeal beside the original decision
   and moves the item to `under_review`.

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to gpt2, running locally.
Its perplexity is squashed onto 0–1 (`detector.model_signal`): perplexity 45
scores 0.5, and lower perplexity scores higher. Only the first 400 tokens
(~300 words) are read.

**Why that might differ between human and AI writing:** A language model
writes by choosing likely next words, so text a model produced is text a model
finds easy to predict. People make odd, specific choices a model doesn't see
coming.

**What it can't see:** Who wrote the text. Plain writing is predictable too: a
plainly written human paragraph (short sentences, everyday words) scored
**0.891**, level with the generic AI paragraph's **0.886**. It also can't see:
- anything past ~300 words
- text from newer models sampled to be less predictable
- famous quotations, which gpt2 has memorized and so finds very predictable

### Signal two — the style signal

**What it measures:** The shape of the text, without reading it
(`stylometry.style_signal`). It uses three measures:
- **sentence-length spread:** stdev ÷ mean of words per sentence
- **vocabulary variety:** unique words ÷ total words, averaged over a 50-word
  sliding window so text length doesn't skew it
- **expressive punctuation:** `; : — ( ) ? !` and quotes per 100 words

Each measure is flipped and squashed onto 0–1 (higher = more AI-like), then
weighted 0.5 / 0.3 / 0.2.

**Why that might differ between human and AI writing:** Choosing the most
likely next word produces even, mid-length sentences, safe vocabulary and
plain punctuation. People's writing is lumpier.

**What it can't see:** Meaning. Typos, a split sentence or a few dashes move
it without changing a word of substance. And any writer who is *even* on
purpose looks AI-like on all three measures at once. That includes the plain
writer, and it also includes formal writing: a formal committee-report
paragraph scored **0.770**, more AI-like than signal one rated it.

### The combining rule

**The rule:** An even weighted average of the two signals, with one exception.
The model signal can't get a text labelled AI on its own. Unless the style
signal independently reaches 0.70, the combined score is capped just below the
AI threshold, so the worst such a text can get is "unsure". I wrote this down
before coding it (`PLANNING.md` §3) because signal one couldn't tell the plain
human paragraph from machine text.

**The numbers** (all in `config.py`):

| Setting | Value |
|---|---|
| `WEIGHT_MODEL_SIGNAL` / `WEIGHT_STYLE_SIGNAL` | 0.5 / 0.5 |
| `STYLE_AGREEMENT` | 0.70 (below it, combined is capped at 0.7999) |
| `HUMAN_THRESHOLD` | 0.30 (combined ≤ 0.30 → human) |
| `AI_THRESHOLD` | 0.80 (combined ≥ 0.80 → AI) |

**Where it lives:** `scoring.py::combine_signals`

**The four test inputs** (run through `POST /submit`, all in `logs/audit.jsonl`):

| Input | model | style | combined | guess |
|---|---|---|---|---|
| Clearly AI (generic "framework" paragraph) | 0.894 | 0.802 | 0.848 | ai |
| Clearly human (casual, bus-in-the-rain) | 0.393 | 0.012 | 0.203 | human |
| Formal human (committee report) | 0.705 | **0.770** | 0.738 | unsure |
| Lightly edited AI | 0.824 | 0.697 | 0.760 | unsure |

I wrote these texts as stand-ins for calibration, so they still need checking
against real writing.

The last two are the ones that matter:
- **Formal human:** lands in "unsure" by a margin of only 0.06. When I printed
  the parts, it was the *style* signal that was off: sentence spread 0.278
  (even, like AI), no expressive punctuation. Because style clears 0.70, the
  agreement cap doesn't protect this writer. Only the 0.80 threshold does. A
  formal writer whose model score reached ~0.83 would be labelled AI.
- **Lightly edited AI:** gets through as "unsure". That's the cost I chose:
  missing AI text costs the site a little, and accusing a writer costs them a
  lot.

**A case where my two signals split, and what my rule does with it:** The
plainly written paragraph: model **0.891** (AI-like), style **0.672**
(leaning AI, but below agreement). The average, 0.781, already sits under
0.80, so it's "unsure" and the cap doesn't have to act. The cap is there for a
plain text that predicts even better: model 0.98 with style 0.65 averages to
0.815, which the cap brings down to 0.7999, "unsure". With style at 0.70 the
same text scores 0.84 and is labelled AI. In other words, an AI label needs
both signals to agree.

---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 – 0.30 | We think this was probably written by a person. |
| unsure | 0.30 – 0.80 | We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review. |
| high-confidence AI | 0.80 – 1.00 | Our check suggests this was probably written by AI. It's an automated estimate, not proof, and it can be wrong — especially about plain or formal writing. If you wrote this yourself, you can ask for a review. |

The boundaries belong to the less severe label: exactly 0.30 is human, and
0.80 is the first score that reads AI. The ranges come from
`scoring.label_ranges()`, so they can't drift from `config.py`. I submitted
text that produced each of the three:

| Text | combined | label |
|---|---|---|
| Generic "framework" paragraph | 0.8476 | high-confidence AI |
| Lightly edited AI | 0.7604 | unsure |
| Casual bus-in-the-rain paragraph | 0.2025 | high-confidence human |

**Why I worded the "unsure" one this way:** The person most likely to read it
is the plain writer from my false-positive trace, who wrote every word
themselves. So it says what we *couldn't* do, and doesn't hint at what they
might have done. It says out loud that this isn't a judgement against them,
and it gives a reason they'd believe: lots of people's own writing lands here.
It ends with something they can do. It doesn't promise an outcome or a
timeline, because nothing in this system reviews an appeal yet. The AI label
names plain and formal writing specifically, because those are the two cases
where I measured my signals going wrong.

---

## Sample Run

**A submission**

The plainly written stand-in paragraph from `PLANNING.md`. Signal one alone
rates it 0.891, but the style signal doesn't agree, so it lands in "unsure"
and isn't accused.

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "My name is Ana and I came to this city three years ago. At first it was hard for me. I did not know many people and my English was not good. I worked in a restaurant in the morning and I went to class in the evening. My teacher was very kind. She helped me with my writing and she told me to read every day. Now I can read books and I can talk with my neighbors. I am proud of this. I want to study nursing next year because I like to help people.", "creator_id": "sydelle"}'
```

```json
{
  "confidence": 0.7813,
  "content_id": "d6a3bbf5-fd9c-4519-ab3a-817fdf1f7a04",
  "creator_id": "sydelle",
  "guess": "unsure",
  "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
  "model_score": 0.891,
  "status": "decided",
  "style_score": 0.6717
}
```

**A refused submission** (fewer than 50 words)

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "some writing", "creator_id": "sydelle"}'
```

```json
{
  "error": "text_too_short",
  "message": "Text needs at least 50 words to judge fairly."
}
```

HTTP 400.

**An appeal**

Against the `content_id` above. The reasoning is role-played as the writer in
the stand-in.

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "d6a3bbf5-fd9c-4519-ab3a-817fdf1f7a04", "reasoning": "I wrote this myself for my nursing application. I write in short sentences because English is my second language."}'
```

```json
{
  "content_id": "d6a3bbf5-fd9c-4519-ab3a-817fdf1f7a04",
  "message": "Your appeal has been recorded and this result is now under review.",
  "status": "under_review"
}
```

HTTP 200. An appeal against an ID that doesn't exist fails loudly instead of
silently:

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "not-a-real-id", "reasoning": "testing a typo"}'
```

```json
{
  "error": "unknown_content_id",
  "message": "We couldn't find a result with that ID. Check it and try again."
}
```

HTTP 404.

**What the log shows afterwards**

The original decision is untouched. The appeal sits right after it with
`status: "under_review"`, and the rejected typo leaves its own trace.

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json
{
  "count": 3,
  "entries": [
    {
      "combined_score": 0.7813,
      "content_id": "d6a3bbf5-fd9c-4519-ab3a-817fdf1f7a04",
      "creator_id": "sydelle",
      "guess": "unsure",
      "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer \u2014 a lot of people's own writing lands here. If this is your work, you can ask for a review.",
      "model_score": 0.891,
      "status": "decided",
      "style_score": 0.6717,
      "timestamp": "2026-10-26T02:07:22+00:00"
    },
    {
      "content_id": "d6a3bbf5-fd9c-4519-ab3a-817fdf1f7a04",
      "creator_id": "sydelle",
      "event": "appeal",
      "reasoning": "I wrote this myself for my nursing application. I write in short sentences because English is my second language.",
      "status": "under_review",
      "timestamp": "2026-10-26T02:07:23+00:00"
    },
    {
      "creator_id": "unknown",
      "event": "rejected",
      "http_status": 404,
      "reason": "unknown_content_id",
      "status": "rejected",
      "timestamp": "2026-10-26T02:07:23+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* For the Milestone 1 plan, I asked Claude (Claude Code)
  to trace a submission through the service, name each signal's blind spot,
  follow a falsely accused writer through it, and write the two endpoint
  contracts.
- *What came back:* `PLANNING.md`. Instead of only repeating the blind spot
  the starter describes, it ran gpt2 on a plainly written paragraph and a
  generic AI paragraph. They scored **0.891** and **0.886**: the model signal
  couldn't tell them apart at all.
- *What I changed:* That measurement changed my scoring design. I dropped the
  starter's 0.35 / 0.65 thresholds for a wider unsure band (0.30 / 0.80), and
  added a rule that "AI" needs the style signal to agree (≥ 0.70) so the
  model signal can't accuse anyone on its own. I also wrote criterion 2 in
  `criteria.md` with a target of zero accusations for plain writers.

**Moment 2**

- *What I asked for:* To test the combining rule with four chosen inputs:
  clearly AI, clearly human, formal human writing and lightly edited AI.
- *What came back:* The formal human paragraph scored **0.770** on the
  *style* signal, more AI-like than the model signal's 0.705. Printing the
  three style measures separately showed why: even sentence lengths (spread
  0.278) and no expressive punctuation. So my agreement rule doesn't protect
  formal writers. Only the 0.80 threshold does, by a margin of 0.06.
- *What I changed:* I wrote that weakness into the README instead of tuning
  it away on one example, and I worded the AI label to say the check "can be
  wrong — especially about plain or formal writing", because those are the
  two cases where I'd measured it going wrong. The other thing I didn't take
  on trust: every calibration text in these tests was written by the AI as a
  stand-in, so the README marks them that way, and they still need replacing
  with real writing.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day
15 submissions as 'flood_tester' against http://127.0.0.1:5000
The first one is slow while the model loads.

  [ 1/15] 400
  [ 2/15] 400
  [ 3/15] 400
  [ 4/15] 400
  [ 5/15] 400
  [ 6/15] 400
  [ 7/15] 400
  [ 8/15] 400
  [ 9/15] 400
  [10/15] 400
  [11/15] 429
  [12/15] 429
  [13/15] 429
  [14/15] 429
  [15/15] 429

============================================================
400 400 400 400 400 400 400 400 400 400 429 429 429 429 429

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

56 attacks from `results/attack_run_2026-11-01_2120.md` (`run_attacks.py::main`
against `app.py::submit`, 2026-11-01 21:20). **46 held, 10 broke.**

How I marked them, by what each family was going for:

- **Evasion** (AI-written text): broke if it wasn't labelled `ai`. AI writing
  that comes back "unsure" or "human" got through.
- **False positive** (human-written text): broke if it was labelled `ai`.
  "Unsure" says outright that it isn't a judgement against the writer.
- **Prompt injection:** broke if the instruction changed the outcome.
- **Malformed and flood:** broke on a 5xx, a crash or no response, or if the
  flood never got a 429.

Before reading the evasion rows: **the plain AI paragraph most of them are
built from already scores 0.702, "unsure"** (model 0.669, style 0.735; I ran it
through the two signals directly). So most evasions broke without having to do
anything. The miss is in the baseline, not the edit. The last column says which
attacks actually moved a signal.

| Family | Attacks | Held | Broke |
|---|---|---|---|
| `evasion` | 10 | 1 | 9 |
| `false_positive` | 8 | 7 | 1 |
| `prompt_injection` | 6 | 6 | 0 |
| `malformed` | 20 | 20 | 0 |
| `flood_same_creator` | 12 | 12 | 0 |
| **Total** | **56** | **46** | **10** |

| ID | Targeting | Status | Guess | Score (model / style) | Verdict | What happened |
|---|---|---|---|---|---|---|
| EV01 | signal two: typos raise word variety | 200 | unsure | 0.4494 (0.1635 / 0.7353) | BROKE | Not called AI. The typos hit signal one (model 0.669 → 0.164); style didn't move (0.735). |
| EV02 | signal two: broken-up sentences raise length spread | 200 | unsure | 0.307 (0.5943 / 0.0196) | BROKE | Not called AI. "Really." crushed signal two (style 0.735 → 0.020); 0.007 off a *human* label. |
| EV03 | signal two: a pasted quotation changes the shape | 200 | unsure | 0.3962 (0.6662 / 0.1261) | BROKE | Not called AI. The quotation dropped style to 0.126. |
| EV04 | signal one: unusual words raise perplexity | 200 | unsure | 0.6699 (0.6114 / 0.7283) | BROKE | Not called AI, but the attack did nothing: 0.670 vs 0.702 for the plain paragraph. |
| EV05 | both signals: heavy human editing pass | 200 | human | 0.2636 (0.3212 / 0.2061) | BROKE | Called **human**. The only evasion that went all the way. |
| EV06 | signal two: one very long sentence and one very short | 200 | unsure | 0.4341 (0.5727 / 0.2956) | BROKE | Not called AI. Style dropped to 0.296. |
| EV07 | signal two: padding with punctuation | 200 | unsure | 0.4283 (0.5862 / 0.2703) | BROKE | Not called AI. Style dropped to 0.270. |
| EV08 | signal one: text below the token window | 400 | — | — | HELD | Refused at the gate (10 words). Never reached signal one. |
| EV09 | both: AI text with a human opening paragraph bolted on | 200 | unsure | 0.5381 (0.7042 / 0.372) | BROKE | Not called AI. The human opener pulled style to 0.372. |
| EV10 | signal two: repeated stanza structure | 200 | unsure | 0.7999 (0.9792 / 0.6603) | BROKE | Not called AI by 0.0001. Model 0.979, but style 0.660 is under the 0.70 agreement bar, so the score was capped at 0.7999. |
| FP01 | plain, clear human writing with no flourishes | 200 | unsure | 0.5285 (0.6175 / 0.4395) | HELD | Unsure, not accused. |
| FP02 | human writing in a formal register | 200 | unsure | 0.766 (0.7387 / 0.7932) | HELD | Unsure, but 0.766 is 0.034 from an accusation. |
| FP03 | a non-native English speaker writing carefully | 200 | unsure | 0.7043 (0.8051 / 0.6035) | HELD | Unsure (0.704). Model 0.805 on its own would have accused. |
| FP04 | a student essay written to a rubric | 200 | unsure | 0.6873 (0.8329 / 0.5417) | HELD | Unsure (0.687). Model 0.833. |
| FP05 | technical documentation written by a person | 200 | ai | 0.8167 (0.8005 / 0.833) | BROKE | **Called AI.** A person's instructions, accused. Both signals agreed (0.801 / 0.833), so the agreement rule didn't help. |
| FP06 | a person imitating a formal template | 200 | unsure | 0.6752 (0.8814 / 0.469) | HELD | Unsure (0.675). Model 0.881. |
| FP07 | human writing that repeats a phrase deliberately | 200 | unsure | 0.6815 (0.8816 / 0.4814) | HELD | Unsure (0.682). Model 0.882. |
| FP08 | very short genuine human submission | 400 | — | — | HELD | Refused (8 words), not accused, though the writer gets no answer at all. |
| PI01 | instruction to ignore the check | 400 | — | — | HELD | Refused as too short (45 words). Held by the word count, not because anything recognised the instruction. |
| PI02 | instruction disguised as a system message | 400 | — | — | HELD | Refused as too short (42 words). Same as PI01. |
| PI03 | instruction wrapped in the writer's voice | 200 | unsure | 0.4285 (0.5943 / 0.2628) | HELD | Unsure, not human. The note isn't obeyed, but it still moved the score: 0.702 → 0.429. |
| PI04 | attempt to make the label text hostile | 200 | unsure | 0.3486 (0.4998 / 0.1973) | HELD | The label is fixed text; the `<script>` is never echoed back. |
| PI05 | attempt to inject into the audit log | 400 | — | — | HELD | Refused as too short. The log writer escapes quotes anyway (`json.dumps`). |
| PI06 | instruction plus real human text | 200 | unsure | 0.5012 (0.5583 / 0.4442) | HELD | Unsure 0.501; the same text without the instruction scores 0.529. No effect. |
| MF01 | text is only whitespace | 400 | — | — | HELD | 400 `missing_field` (whitespace strips to empty). |
| MF02 | text is a single character | 400 | — | — | HELD | 400 `text_too_short`, no crash. |
| MF03 | text is control characters | 400 | — | — | HELD | 400 `text_too_short`, no crash. |
| MF04 | text is only punctuation | 400 | — | — | HELD | 400 `text_too_short`, no crash. |
| MF05 | text is a very long single word | 400 | — | — | HELD | 400 `text_too_short`, no crash. |
| MF06 | text is emoji only | 400 | — | — | HELD | 400 `text_too_short`, no crash. |
| MF07 | text is right-to-left script | 400 | — | — | HELD | 400, no crash. But the reason is wrong: Arabic counts as **0 words**, so any Arabic text, however long, is refused as "too short". |
| MF08 | text is 60,000 characters | 413 | — | — | HELD | 413 at the gate. |
| RQ01 | no text field at all | 400 | — | — | HELD | 400 `missing_field`. |
| RQ02 | no creator_id | 400 | — | — | HELD | 400; logged as creator `unknown`. |
| RQ03 | text is a number | 400 | — | — | HELD | 400 `missing_field`. |
| RQ04 | text is a list | 400 | — | — | HELD | 400 `missing_field`. |
| RQ05 | text is null | 400 | — | — | HELD | 400 `missing_field`. |
| RQ06 | creator_id is an object | 400 | — | — | HELD | 400; the object creator_id is logged as `unknown`. |
| RQ07 | body is a JSON array, not an object | 400 | — | — | HELD | 400 `invalid_json`. |
| RQ08 | body is unparseable JSON | 400 | — | — | HELD | 400 `invalid_json`. |
| RQ09 | body is empty | 400 | — | — | HELD | 400 `invalid_json`. |
| RQ10 | body is form-encoded, not JSON | 400 | — | — | HELD | 400 `invalid_json`. |
| RQ11 | body is JSON claiming to be plain text | 400 | — | — | HELD | 400 `invalid_json`. |
| RQ12 | deeply nested JSON | 400 | — | — | HELD | 400 `missing_field`. |
| FL01_01 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_02 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_03 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_04 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_05 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_06 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_07 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_08 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_09 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_10 | 20 rapid submissions from one creator | 400 | — | — | HELD | 400 `text_too_short`, but it still counts toward the limit. |
| FL01_11 | 20 rapid submissions from one creator | 429 | — | — | HELD | **429**, logged as `rate_limited`. |
| FL01_12 | 20 rapid submissions from one creator | 429 | — | — | HELD | **429**, logged as `rate_limited`. |

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

Eleven entries, exactly as they are in `logs/audit.jsonl` (also returned by
`GET /log`), in this order:

1. **FP05**: the false accusation.
2. **FP02**: formal human writing, 0.034 from being accused.
3. **FP03**: a non-native writer. Signal one alone (0.805) would have
   accused them; the style signal kept it at unsure.
4. **EV10**: three copies of one AI paragraph. Signal one is sure (0.979), but
   style is 0.660, under the 0.70 agreement bar, so the score is capped at
   0.7999, one ten-thousandth under "AI".
5. **EV02**: one word ("Really.") after every sentence takes the style
   signal from 0.735 to 0.020.
6. **EV05**: AI text with a heavy human edit, labelled human.
7. **EV01**: aimed at signal two with typos, but signal one is what broke
   (0.164). gpt2 finds misspellings unpredictable.
8. **PI03**: the instruction wasn't followed, but a chatty note at the top
   still dropped the score from 0.702 to 0.429.
9. **PI01** (rejected): an injection that held only because it was 45 words.
10. **MF07** (rejected): Arabic text refused as "too short" because the word
    counter only counts `a-z`.
11. **The flood** (rejected, 429): the limiter cutting in at the 11th request.

```json
{"timestamp": "2026-11-02T03:20:46+00:00", "content_id": "f300f53a-7e10-439d-bfba-00a4e14eb6af", "creator_id": "attacker_FP05", "guess": "ai", "model_score": 0.8005, "style_score": 0.833, "combined_score": 0.8167, "label": "Our check suggests this was probably written by AI. It's an automated estimate, not proof, and it can be wrong — especially about plain or formal writing. If you wrote this yourself, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:45+00:00", "content_id": "26c39a93-dd19-458b-b86a-7559f5492b6c", "creator_id": "attacker_FP02", "guess": "unsure", "model_score": 0.7387, "style_score": 0.7932, "combined_score": 0.766, "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:45+00:00", "content_id": "635cc29e-b4b7-4d68-b501-ed9b62b0b252", "creator_id": "attacker_FP03", "guess": "unsure", "model_score": 0.8051, "style_score": 0.6035, "combined_score": 0.7043, "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:45+00:00", "content_id": "c17d1354-35cd-4fb7-b0a7-5574643bb4b7", "creator_id": "attacker_EV10", "guess": "unsure", "model_score": 0.9792, "style_score": 0.6603, "combined_score": 0.7999, "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:43+00:00", "content_id": "5130f796-c332-48e4-984d-88b71a18b262", "creator_id": "attacker_EV02", "guess": "unsure", "model_score": 0.5943, "style_score": 0.0196, "combined_score": 0.307, "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:44+00:00", "content_id": "2f113904-ecef-4c73-b805-138818343a62", "creator_id": "attacker_EV05", "guess": "human", "model_score": 0.3212, "style_score": 0.2061, "combined_score": 0.2636, "label": "We think this was probably written by a person.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:43+00:00", "content_id": "617c9bb0-15af-49d9-a201-b6840ada4bab", "creator_id": "attacker_EV01", "guess": "unsure", "model_score": 0.1635, "style_score": 0.7353, "combined_score": 0.4494, "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:46+00:00", "content_id": "3439ab68-bea1-4a5f-92f3-1266d1b93b38", "creator_id": "attacker_PI03", "guess": "unsure", "model_score": 0.5943, "style_score": 0.2628, "combined_score": 0.4285, "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.", "status": "decided"}
{"timestamp": "2026-11-02T03:20:46+00:00", "content_id": null, "creator_id": "attacker_PI01", "guess": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "status": "rejected", "event": "rejected", "reason": "text_too_short", "http_status": 400}
{"timestamp": "2026-11-02T03:20:47+00:00", "content_id": null, "creator_id": "attacker_MF07", "guess": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "status": "rejected", "event": "rejected", "reason": "text_too_short", "http_status": 400}
{"timestamp": "2026-11-02T03:20:47+00:00", "content_id": null, "creator_id": "attacker_flood", "guess": null, "model_score": null, "style_score": null, "combined_score": null, "label": null, "status": "rejected", "event": "rejected", "reason": "rate_limited", "limit": "10 per 1 minute"}
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

**FP05: technical documentation written by a person, labelled "probably
written by AI" (0.817).** It's the only accusation in the run, and it landed on
a person. Good instructions are meant to be plain: short, even sentences, the
same few words reused ("the service", "the port") so nobody gets confused. Both
of my signals read that as AI. gpt2 found it predictable (0.801), and the style
signal found it even and repetitive (0.833). My one safeguard against a false
accusation is that "AI" needs the style signal to agree. Here it agreed,
because both signals share the same blind spot for plain writing, so the
safeguard did nothing. And the writer can't edit their way out: the clearer
they make the instructions, the more AI-like they look.


---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Own writing isn't accused | ≤1 of 10 `ai` **and** ≥5 of 10 `human` | 0 ai, 0 human | 0 ai, 0 human | 0 ai, 0 human | **Missed.** Nobody accused, but 0 of 10 reach `human` (target 5) |
| 2. Plain writers are never accused | 0 of 5 `ai` | 0 ai | 0 ai | 0 ai | **Met** |
| 3. All labels reachable, AI still caught | `human`, `unsure`, `ai` each ≥1 **and** ≥2 of 3 AI texts `ai` | only `unsure`; 0/3 AI | only `unsure`; 0/3 AI | only `unsure`; 0/3 AI | **Missed** on both parts |
| 4. Every appeal changes status and is logged | 5/5 appeals → 200 `under_review` + one log entry; fake ID → 404, 3/3 | not run | not run | not run | **Not tested yet.** `run_eval.py` can't chain a submit into an appeal, so this is a by-hand test with `curl`. The Sample Run shows one appeal working, not the full 5 + 3 |
| 5. Bad input refused cleanly | 7 bodies → expected status and error code, 0 × 5xx, < 2 s, one `rejected` log entry each | 7/7 status, 7/7 code + log entry, 0 × 5xx | same | same | **Met on everything measured.** The 2-second limit wasn't measured (see below) |

**About this table.** `run_eval.py` writes this table with Target, Run and
Verdict left blank on purpose: it sends the requests and records what came
back, but it doesn't know my criteria, so it can't decide what passed. I filled
in each cell by checking every trial in `results/run_2026-11-01_2144_before.md`
against `criteria.md`. Two gaps in what it records:

- **It doesn't record the `error` code.** For criterion 5, I matched each
  refusal to its `rejected` entry in `logs/audit.jsonl` instead. All 21
  (7 bodies × 3 trials) have the expected `reason` and `http_status`.
- **It doesn't record response time,** so the "under 2 seconds" part of
  criterion 5 is unmeasured, not met.

**Why the three trials are identical.** The scores match to four decimal
places in every trial. gpt2 runs in `eval()` mode with no sampling, and the
style signal is arithmetic, so the same text always gets the same score. Three
trials here show the scores are stable, not that the model varies.

**After the fix** (`results/run_2026-11-01_2157_after.md`), every verdict is the
same, but the scores moved: my own pieces went from 0.49–0.75 to 0.43–0.69,
closer to `human` without reaching it.

Two more files in `results/`, `run_2026-11-01_2149_before.md` and
`run_2026-11-01_2153_before.md`, are labelled `before` but were run *after*
the fix (piece 1's style score is 0.4433, the fixed value, not 0.5706).
This is the terminal output from the 21:53 one:

```
Bad starting point  (criterion 1)
  trial 1: unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure
  trial 2: unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure
  trial 3: unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure

plain writers  (criterion 2)
  trial 1: unsure, unsure, unsure, unsure, unsure
  trial 2: unsure, unsure, unsure, unsure, unsure
  trial 3: unsure, unsure, unsure, unsure, unsure

label coverage  (criterion 3)
  trial 1: unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure
  trial 2: unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure
  trial 3: unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure, unsure

bad input  (criterion 5)
  trial 1: —, —, —, —, —, —, —
  trial 2: —, —, —, —, —, —, —
  trial 3: —, —, —, —, —, —, —

Wrote results\run_2026-11-01_2153_before.md
```

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

From `results/run_2026-11-01_2144_before.md`, written by `run_eval.py::main`
(scored by `scoring.py::combine_signals`): criterion 3, trial 1, the three
clearly AI texts. None reaches `ai`. Text 3 (0.5947) scores lower than 7 of my
own 10 pieces.

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.7468,
    "model_score": 0.8017,
    "style_score": 0.6919,
    "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.",
    "sent": "Effective time management is a crucial skill that empowers individuals"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.7498,
    "model_score": 0.9362,
    "style_score": 0.5633,
    "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.",
    "sent": "Climate change represents one of the most pressing challenges facing h"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5947,
    "model_score": 0.7227,
    "style_score": 0.4666,
    "label": "We couldn't tell whether this was written by a person or by AI. That isn't a judgement against the writer — a lot of people's own writing lands here. If this is your work, you can ask for a review.",
    "sent": "Reading offers numerous benefits that extend far beyond simple enterta"
  }
]
```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
