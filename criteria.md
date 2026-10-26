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
