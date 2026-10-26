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



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

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
