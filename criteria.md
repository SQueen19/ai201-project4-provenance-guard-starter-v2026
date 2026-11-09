# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. False positives on my own writing

Of 10 pieces I wrote myself (each at least 50 words), **at most 1** is
labelled high-confidence AI, **and at least 5** are labelled high-confidence
human. Both parts must hold in every one of the three trials.

**Why this target:** On a writing site, wrongly accusing someone costs that
person far more than missing a piece of AI text costs the site, so I allow
almost no wrong accusations. The second number is there because a system that
labels everything "unsure" never technically accuses anyone, yet it tells a
real writer nothing. I want it to say "a person wrote this" to most people
who did.

---

## 2. Plain writers are never accused

Of 5 human paragraphs written plainly on purpose (short sentences, everyday
words, only full stops, like the stand-in "Ana" paragraph in
`PLANNING.md`), **0** are labelled high-confidence AI in any of the three
trials.

**Why this target:** This is the writer the project is about. In Milestone 1,
signal one scored that stand-in paragraph 0.891, slightly higher than the
generic AI sample's 0.886. Both blind spots point the same way for this
person. My scoring rule (AI only when the combined score is at least 0.80
*and* the style signal is at least 0.70 on its own) exists to protect them,
so the target is zero rather than "few". Each miss here is the exact
accusation the system was built to prevent. I expect this one could fail,
and I'm leaving it at zero anyway.

---

## 3. All three labels are reachable, and AI text still gets caught

From a fixed set of 9 texts (3 I'm confident are AI-generated, 3 I'm
confident are human-written, 3 I judge borderline), **each of `human`,
`unsure` and `ai` appears at least once**, **and at least 2 of the 3 clearly
AI texts are labelled `ai`**. Both parts must hold in every one of the three
trials.

**Why this target:** My scoring rule is deliberately reluctant to say "AI",
and a reluctant rule can easily become one that never says it. A label
that's never reachable means my ranges have a gap. It would also mean
criteria 1 and 2 were passed by switching the detector off. The 2-of-3 floor
is the price I'm charging myself for being careful. It still allows one
clear AI text to slip into "unsure".

---

## 4. Every appeal changes status and leaves a record

For 5 real submissions, an appeal against each returned `content_id` gets a
**200 with `status: "under_review"` in 5 of 5 cases**. The log gains
**exactly one `event: "appeal"` entry per appeal**, with the same
`content_id`, the `creator_id` copied from the original decision, and the
reasoning I sent, and the original decision entry is unchanged. An appeal
against a made-up `content_id` gets a **404 `unknown_content_id`** and a
`rejected` log entry, **3 of 3 times**. I'll test this by hand with `curl`
and `GET /log`, because `run_eval.py` can't chain a submit into an appeal.

**Why this target:** The appeal is the only thing between a wrong accusation
and nothing at all, so "usually works" isn't good enough. It has to be 5 of
5. The made-up-ID case matters because a typo that returns success while
recording nothing is the worst possible outcome: the writer believes they've
appealed when they haven't.

---

## 5. Bad input is refused cleanly, never crashes, and is logged

Each of these 7 request bodies gets the 4xx status and `error` code
`PLANNING.md` specifies, **with zero 500s**, a response in **under 2
seconds**, and **exactly one `rejected` log entry each**, in every one of the
three trials:

| Body | Expected |
|---|---|
| `text` is `""` | 400 `missing_field` |
| `text` is only whitespace | 400 `missing_field` |
| no `text` field | 400 `missing_field` |
| `text` is `null` | 400 `missing_field` |
| no `creator_id` field | 400 `missing_field` |
| `text` is 49 words | 400 `text_too_short` |
| `text` is `"word " * 50000` (250,000 characters) | 413 `text_too_long` |

**Why this target:** A crash on bad input is one of the most common real
failures there is, and unit 8's attack set will send exactly these. The
2-second limit checks that bad input is refused *before* it reaches the
model: an enormous body that gets as far as gpt2 is slow at best. The log
entry matters because a refusal that leaves no trace is an attack I'll never
see.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 9 — criteria for the extension

The extension is two things built on top of the working service:
`GET /status/<content_id>` (one submission's decision, status and appeals) and
the run log (`runlog.py`: one timed record per request, failures included),
along with the cost measurement that reads from it. All five criteria below are
about those new parts. Criteria 1–5 above stay as they were.

Baseline numbers come from the runs on 2026-11-08:
`results/status_check_2026-11-08_1731.md` and
`results/cost_2026-11-08_1753.md`.

---

## 6. `/status` tells the truth about every submission

For the 14 submissions `run_status_check.py` sends, appealed 0, 1 or 2 times
in rotation (5, 5 and 4 of them), `GET
/status/<content_id>` reports **the right `status` in 14 of 14**
(`decided` with no appeal, `under_review` after one or more), **the right
`appeal_count` in 14 of 14**, and a `decision` block whose `guess`, `label`,
`confidence`, `model_score` and `style_score` are **exactly equal** to what
`/submit` returned for that ID. It must hold in every one of the three trials.
Measured by `run_status_check.py`.

**Why this target:** `/status` is where a writer goes to find out whether
their appeal counted. If it says `decided` after they appealed, they'll assume
they were ignored, or appeal again and inflate the count. If it shows a
different label from the one they were given, they can't trust either one.
The endpoint does no scoring; it only reads the audit log back. Nothing
random sits between the log and the answer, so anything short of 14 of 14
means a bug in how I read the log, not noise. The 0/1/2-appeal rotation is
there because "only the first appeal is counted" and "only the latest entry
is read" are both bugs a single appeal would hide.

---

## 7. A bad `/status` request is refused, never crashes, and is logged

Each of these 4 requests gets the listed status and `error` code, **with zero
500s**, **exactly one `rejected` entry in the audit log** and **exactly one
run-log record with `outcome: "refused"`** each, in every one of the three
trials:

| Request | Expected |
|---|---|
| A well-formed UUID that was never submitted | 404 `unknown_content_id` |
| A real ID with one character changed | 404 `unknown_content_id` |
| A 200-character ID | 400 `invalid_content_id` |
| A real ID with spaces around it (`%20<id>%20`) | 200, the same answer as the clean ID |

Each refused request also answers in **under 100 ms** with the audit log at its
current size (737 entries).

**Why this target:** This is the bad path for the new endpoint, and the typo
case matters most. A writer copying an ID out of an email is the most likely
person to send one, and a 200 with someone else's result, or a 500, are both
worse than a clear 404. The spaces case is the opposite mistake: refusing a
real ID because of stray whitespace looks to the writer like their result has
vanished. The 100 ms limit isn't about speed for its own sake. `/status`
reads the *whole* audit log on every call (`audit.entries_for`), so its time
grows with the log. Today it answers in 25–43 ms. If it goes past 100 ms, the
log has outgrown that approach and the lookup needs an index. I want the
criterion to tell me when that happens, not a writer.

---

## 8. Every request leaves exactly one run-log record, including the ones that fail

Across a mixed batch of 20 requests (10 good `/submit`s, 3 bad-input
`/submit`s, 1 that hits the rate limit, 2 `/status` lookups, 1 `/appeal`, 1
request to a route that doesn't exist, 1 `/ping`, and 1 `/submit` with a crash
injected into a signal), `logs/runs.jsonl` gains **exactly 20 records**. Every
record's `run_id` matches the `X-Run-Id` header of its response, and every
`outcome` matches its status class (`ok` / `refused` / `error`): **20 of 20**.
The crash record has a non-null `error.type` and `error.where`, and **0** of
the 20 responses is a dropped connection or an HTML error page. It must hold
in every one of the three trials.

**Why this target:** A failure that shows up only as an absence is one I'll
never find, so the failures are what this criterion is mostly testing. One
missing record isn't 95% good. It means some kind of failure leaves no trace,
and I can't know which kind. The count has to be exact in both directions. A
request that writes *two* records (for example, if the crash handler and the
after-request hook both wrote) would double-count failures and make the
system look worse than it is. The crash has to be injected because a healthy
service never produces a 500 on its own, and an error path that has never
run is not one I can claim works.

---

## 9. The cost number is repeatable, and the model loads once

Across **three runs of `measure_cost.py`**, each against a freshly started
service:

- the mean warm wall time per `/submit` is **under 450 ms** in every run and
  **within ±15% of 348 ms** (296–400 ms);
- gpt2 accounts for **at least 95%** of that wall time;
- **exactly 1 of the 11** `/submit` records in each run has
  `model_was_loaded: false` (the cold start). The other 10 have `true`.

**Why this target:** A cost number is only worth writing down if measuring it
again gives roughly the same answer. Within one run the spread was ±28 ms
(about 8%), so ±15% leaves room for ordinary noise on a laptop. It still
catches a real change, such as another process taking the CPU or someone
raising `DETECTOR_MAX_TOKENS`. The "loads once" part is there because the most
expensive bug this service can have is reloading gpt2 on every request. That
turns 0.35 s into 10 s per submission, about 28× the cost. The 95% share
checks my claim that the model *is* the cost. If stylometry or logging ever
takes more than a few percent, that's a regression I want to see.

---

## 10. The run log never stores anyone's writing

For the 14 texts sent by `run_status_check.py` and the text sent by
`measure_cost.py`, **0** of them appear in full in `logs/runs.jsonl`. No
`input` field holds more than **60 characters** of any submitted text, and
**every record is under 3 KB**.

**Why this target:** The run log is committed to a public repository
alongside the audit log. Writers submit their work to be judged, not
published. Copying the full text into a second file that nobody reviews
would be a quiet leak that's hard to undo once pushed. Sixty characters is
enough to recognise a submission while debugging, and the hash is enough to
match it exactly. The 3 KB cap keeps the log readable and its growth
predictable. At about 1 KB per `/submit`, 200 submissions a day (the rate
limit's daily cap per writer) is a few hundred KB, not megabytes of copied
essays.
