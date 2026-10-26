"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import math
import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures ───────────────────────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies: stdev of words-per-sentence over the mean
    (the coefficient of variation), so long and short texts are comparable.

    Returns:
        A float from 0 upward. **Higher means more human** — 0.1–0.25 on the
        AI-style calibration texts, 0.38–1.2 on the human ones.

    Fewer than two sentences returns 0.0: there's no spread to measure.
    `style_signal` treats that as no evidence rather than as "perfectly even".
    """
    lengths = [n for n in (len(words(s)) for s in sentences(text)) if n]
    if len(lengths) < 2:
        return 0.0
    return round(statistics.stdev(lengths) / statistics.mean(lengths), 4)


def type_token_ratio(text: str, window: int = 50) -> float:
    """
    Unique words over total words, averaged over a sliding 50-word window.

    Returns:
        A float between 0 and 1. **Higher means more varied vocabulary.**

    Plain TTR falls as text gets longer, so a 400-word essay would look less
    varied than a 60-word one for no reason but length. Averaging over a fixed
    window (moving-average TTR) takes length out of it. Texts shorter than
    the window get plain TTR.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    if len(tokens) <= window:
        return round(len(set(tokens)) / len(tokens), 4)
    ratios = [
        len(set(tokens[i:i + window])) / window
        for i in range(len(tokens) - window + 1)
    ]
    return round(statistics.mean(ratios), 4)


# Full stops and commas are everywhere, in everyone's writing. These are the
# marks that vary between writers: ; : — – ( ) ? ! and quotes, plus "--" and a
# spaced " - " standing in for a dash.
_EXPRESSIVE = re.compile(r"[;:\u2014\u2013()?!\"\u201c\u201d]|--|(?<=\s)-(?=\s)")


def punctuation_density(text: str) -> float:
    """
    Expressive punctuation marks per 100 words.

    Returns:
        A float from 0 upward. **Higher means more human.** Every AI-style
        calibration text scored 0; the lively human ones scored 3–5.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return round(100 * len(_EXPRESSIVE.findall(text)) / len(tokens), 4)


# ── Combining them ───────────────────────────────────────────────────────────
# Each measure goes through a flipped logistic: at its midpoint it scores 0.5,
# below it heads toward 1 (AI-like), above it toward 0. `scale` is how fast.
# The midpoints sit between the AI-style and human calibration texts. They
# were fitted to six stand-in paragraphs, so Milestone 4's real calibration
# inputs should move them.

SPREAD_MIDPOINT, SPREAD_SCALE = 0.35, 0.08
TTR_MIDPOINT, TTR_SCALE = 0.78, 0.03
PUNCT_MIDPOINT, PUNCT_SCALE = 1.5, 0.6

# Spread separates best. Type-token ratio barely separates AI from human
# (~0.80 vs ~0.86) but scores plain writers as very AI-like, so it counts least.
WEIGHT_SPREAD = 0.5
WEIGHT_PUNCT = 0.3
WEIGHT_TTR = 0.2


def _ai_likeness(value: float, midpoint: float, scale: float) -> float:
    """Map a higher-is-more-human measure onto 0–1, higher = more AI-like."""
    return 1.0 / (1.0 + math.exp((value - midpoint) / scale))


def style_parts(text: str) -> dict[str, float]:
    """Each measure's contribution on the 0–1 AI-likeness scale. For debugging."""
    if len(sentences(text)) < 2:
        spread_ai = 0.5   # one sentence: no evidence either way
    else:
        spread_ai = _ai_likeness(sentence_length_spread(text), SPREAD_MIDPOINT, SPREAD_SCALE)
    return {
        "spread": round(spread_ai, 4),
        "punctuation": round(_ai_likeness(punctuation_density(text), PUNCT_MIDPOINT, PUNCT_SCALE), 4),
        "vocabulary": round(_ai_likeness(type_token_ratio(text), TTR_MIDPOINT, TTR_SCALE), 4),
    }


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    A weighted average of the three measures, each first flipped and squashed
    onto 0–1 so they point the same way and sit on the same scale:

        0.5 × spread  +  0.3 × punctuation  +  0.2 × vocabulary

    Blind spot: it can't read. A few dashes, a broken-up sentence or a pasted
    quotation move it without changing a word of substance. And a plain writer
    (even sentences, repeated everyday words, only full stops) looks AI-like on
    all three measures at once.
    """
    parts = style_parts(text)
    score = (
        WEIGHT_SPREAD * parts["spread"]
        + WEIGHT_PUNCT * parts["punctuation"]
        + WEIGHT_TTR * parts["vocabulary"]
    )
    return round(min(max(score, 0.0), 1.0), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"  as AI-likeness         {style_parts(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
