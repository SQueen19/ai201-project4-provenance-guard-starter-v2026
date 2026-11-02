"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

# Names matter beyond the report: run_eval.py builds each creator_id from the
# first 12 characters of the name, so no two may share those 12 characters or
# their submissions count against the same rate limit.

# The 49-word body for criterion 5. One word short of MIN_TEXT_WORDS in app.py.
FORTY_NINE_WORDS = (
    "I started keeping a notebook last spring because I kept forgetting the "
    "small things that happened during the week. At first I wrote a line "
    "or two each night. Now it is half a page, and reading it back "
    "reminds me how much I would have lost without it."
)

SCENARIOS = [
    {
        "name": "Bad starting point",
        "criterion": 1,
        # ⚠️ PUT YOUR OWN WRITING HERE. Not AI text, not a sample from the web —
        # things you actually wrote. This is the criterion that matters most and
        # it's meaningless with someone else's prose.
        #
        # Target: at most 1 of 10 labelled `ai`, at least 5 of 10 labelled
        # `human`, in every trial. Each piece needs 50+ words or the gate
        # refuses it before it's judged.
        "texts": [
            "I missed the bus by less than a minute this morning. The driver saw me "
            "running but kept going, which was annoying at the time. I stood at the "
            "stop and checked the schedule twice, even though I already knew the "
            "next bus would not come for twenty minutes. A neighbor arrived a few "
            "minutes later and we ended up sharing a ride downtown.",
            "The old mug has a crack near the handle, but I still use it every day. "
            "It was a gift from my sister when I moved into my first apartment. "
            "The kitchen in that place was tiny and the windows did not close all "
            "the way. We drank coffee on the floor while unpacking boxes, and that "
            "is probably why the mug feels more valuable than the newer ones.",
            "I tried to fix the loose cabinet door after dinner. The first screwdriver "
            "I found was too small, and the second one slipped whenever I turned it. "
            "Eventually I took the hinge off and discovered that one of the screws "
            "had been replaced with a shorter one. I used a spare from the toolbox, "
            "and the door has stayed straight since then.",
            "My dog refuses to walk past the blue recycling bin on the corner. I do "
            "not know whether it is the color, the noise it makes in the wind, or "
            "something that happened before I adopted her. She will cross the street "
            "without a problem, then hurry back as soon as we pass the bin. The "
            "route takes longer, but the detour has become part of our routine.",
            "Last Saturday I cleaned out the drawer where I keep batteries, tape, "
            "and random cables. I found three chargers for devices I no longer own "
            "and a receipt from a restaurant that closed years ago. I almost threw "
            "everything away, then kept one cable because it might fit an old lamp. "
            "This is how the drawer becomes crowded again after every cleaning.",
            "The rain started just as I finished carrying the groceries from the car. "
            "I left the last bag on the driveway and went back for an umbrella, but "
            "the umbrella was in the same bag. By the time I brought it inside, the "
            "bread was damp and one of the paper bags had torn. Nothing was ruined, "
            "although I did spend the next hour wiping water from the hallway floor.",
            "I called my grandmother because I had not spoken with her all week. She "
            "asked about the weather, then reminded me that she used to walk to "
            "school in snow much deeper than anything we get here. We talked about "
            "her garden for a while. Before hanging up, she asked me to send a "
            "picture of the tomatoes, even though she had already seen them twice.",
            "The first version of my presentation was much too long. I wanted to "
            "explain every detail, so I kept adding slides whenever I remembered "
            "another example. During practice I reached the final section with only "
            "a minute left. I removed several slides and moved the explanation into "
            "the notes. The shorter version felt less impressive, but it was easier "
            "to follow.",
            "I found a quiet table at the library near the window. A child in the "
            "next aisle was whispering questions to his father, and someone nearby "
            "kept turning pages loudly. It was not completely silent, but the noise "
            "was steady enough to ignore. I finished the chapter I had been avoiding "
            "and wrote down three questions before packing up to leave.",
            "When I started cooking, I realized I had forgotten to buy onions. I "
            "considered walking back to the store, but the sauce was already heating "
            "and I did not want to leave the stove. I used extra garlic instead and "
            "added a little more pepper than usual. The result tasted different from "
            "the recipe, though not in a bad way, so I wrote down what I changed.",
        ],
    },
    {
        "name": "plain writers",
        "criterion": 2,
        # Human writing that is plain on purpose: short sentences, everyday
        # words, only full stops. Target: 0 of 5 labelled `ai`, every trial.
        "texts": [
            # The Ana stand-in from PLANNING.md and the README's sample run.
            "My name is Ana and I came to this city three years ago. At first "
            "it was hard for me. I did not know many people and my English was "
            "not good. I worked in a restaurant in the morning and I went to "
            "class in the evening. My teacher was very kind. She helped me with "
            "my writing and she told me to read every day. Now I can read books "
            "and I can talk with my neighbors. I am proud of this. I want to "
            "study nursing next year because I like to help people.",
            # attack_set FP03: a non-native English speaker writing carefully.
            "I want to describe my experience of the first month in this "
            "country. The weather was very different from my home. I did not "
            "expect the rain to continue for so many days. My colleagues were "
            "kind and they helped me to find an apartment. I am still learning "
            "the words that people use in the office. Sometimes I do not "
            "understand the jokes. But I am happy that I came here and I think "
            "it was a good decision for my family.",
            # attack_set FP01: plain, clear human writing with no flourishes.
            "We got to the campsite about four. The pitch was fine, a bit "
            "sloped, but there was a tap nearby and the toilets were clean "
            "enough. Putting the tent up took longer than it should have "
            "because I had forgotten how the poles went. The weather held until "
            "Saturday night. Then it rained hard and kept raining. We stayed in "
            "the tent and played cards and ate most of the food we had brought "
            "for Sunday. On Sunday we packed up wet and drove home early. It was "
            "not the weekend we planned but the kids enjoyed it and we would go "
            "back.",
            # attack_set FP07: human writing that repeats a phrase deliberately.
            "It rained on Monday. It rained on Tuesday. It rained on Wednesday "
            "and it rained on Thursday and by Friday I had stopped looking out "
            "of the window altogether. The forecast said it would clear. The "
            "forecast said that on Monday, and on Tuesday, and on Wednesday. I "
            "have stopped believing the forecast. I have started believing the "
            "window.",
            # attack_set FP06: a person imitating a formal template.
            "Dear Sir or Madam, I am writing to enquire about the position "
            "advertised on your website. I have five years of relevant "
            "experience and I believe I would be a strong fit for the role. I "
            "have attached my curriculum vitae for your consideration. I am "
            "available for interview at your convenience. Thank you for your "
            "time. I look forward to hearing from you.",
        ],
    },
    {
        "name": "label coverage",
        "criterion": 3,
        # 3 clearly AI, 3 clearly human, 3 borderline. Target: every label
        # appears at least once, and at least 2 of the first 3 are `ai`, in
        # every trial. Keep this order: the report lists results by position.
        "texts": [
            # 1–3: clearly AI. Generated by Claude for this test, unedited.
            "Effective time management is a crucial skill that empowers "
            "individuals to achieve their goals and maintain a healthy work-life "
            "balance. By prioritizing tasks, setting clear objectives, and "
            "minimizing distractions, people can significantly enhance their "
            "productivity. Additionally, leveraging tools such as calendars and "
            "task management applications can streamline daily workflows. "
            "Ultimately, mastering time management not only boosts efficiency "
            "but also reduces stress, fostering a greater sense of "
            "accomplishment and overall well-being.",
            "Climate change represents one of the most pressing challenges "
            "facing humanity today. Rising global temperatures, driven primarily "
            "by greenhouse gas emissions, are contributing to more frequent and "
            "severe weather events. To address this issue, it is essential for "
            "governments, businesses, and individuals to work together. "
            "Transitioning to renewable energy sources, improving energy "
            "efficiency, and promoting sustainable practices are key steps "
            "toward a more resilient and sustainable future for generations to "
            "come.",
            "Reading offers numerous benefits that extend far beyond simple "
            "entertainment. Engaging with books regularly can enhance "
            "vocabulary, improve concentration, and strengthen critical thinking "
            "skills. Moreover, reading fiction has been shown to foster empathy "
            "by allowing readers to experience diverse perspectives. In today's "
            "fast-paced digital world, setting aside dedicated time for reading "
            "can serve as a valuable opportunity for relaxation, personal "
            "growth, and lifelong learning.",
            # 4–6: clearly human. Own writing, the same as criterion 1's
            # pieces 4, 7 and 9.
            "My dog refuses to walk past the blue recycling bin on the corner. "
            "I do not know whether it is the color, the noise it makes in the "
            "wind, or something that happened before I adopted her. She will "
            "cross the street without a problem, then hurry back as soon as we "
            "pass the bin. The route takes longer, but the detour has become "
            "part of our routine.",
            "I called my grandmother because I had not spoken with her all "
            "week. She asked about the weather, then reminded me that she used "
            "to walk to school in snow much deeper than anything we get here. "
            "We talked about her garden for a while. Before hanging up, she "
            "asked me to send a picture of the tomatoes, even though she had "
            "already seen them twice.",
            "I found a quiet table at the library near the window. A child in "
            "the next aisle was whispering questions to his father, and someone "
            "nearby kept turning pages loudly. It was not completely silent, "
            "but the noise was steady enough to ignore. I finished the chapter "
            "I had been avoiding and wrote down three questions before packing "
            "up to leave.",
            # 7–9: borderline.
            # attack_set FP02: human writing in a formal register.
            "This report sets out the findings of the working group. The group "
            "met four times between January and March. Its remit was to review "
            "the current arrangements and to recommend changes where these were "
            "warranted. The group found that the existing arrangements are "
            "broadly sound. Three areas were identified where improvement is "
            "possible. These are set out in section four, together with an "
            "indicative timetable. The group recommends that the committee "
            "adopt the proposals in full.",
            # attack_set FP04: a student essay written to a rubric.
            "There are three main causes of the conflict. The first cause is "
            "economic. Trade between the two regions had declined significantly "
            "in the preceding decade. The second cause is political. Neither "
            "government was able to control its own border provinces "
            "effectively. The third cause is social. Population movements had "
            "created communities on both sides with divided loyalties. In "
            "conclusion, the conflict cannot be explained by any single factor.",
            # attack_set EV09: AI text with a human opening paragraph bolted on.
            "Right, so. I've been thinking about this since the meeting on "
            "Thursday and I still don't have a neat answer, but here's roughly "
            "where I've landed.\n\nThe importance of effective communication in "
            "the workplace cannot be overstated. Teams that communicate clearly "
            "are better positioned to achieve their objectives and avoid costly "
            "misunderstandings. There are several strategies organisations can "
            "adopt to improve this. First, establishing regular check-ins "
            "ensures that information flows consistently between team members. "
            "Second, documenting decisions provides a reference point that "
            "reduces ambiguity. Finally, encouraging an environment where "
            "questions are welcomed helps surface issues early. Implementing "
            "these approaches can lead to meaningful improvements in team "
            "performance and overall satisfaction.",
        ],
    },
    # Criterion 4 (the appeal path) isn't here. It needs a submission first
    # and then an appeal against the content_id that came back, which
    # run_eval.py can't chain. It's tested by hand with curl and GET /log.
    {
        "name": "bad input",
        "criterion": 5,
        # Raw request bodies, sent exactly as written. Expected status and
        # error code from PLANNING.md on each line.
        "bodies": [
            {"text": "", "creator_id": "eval_bad_empty"},             # 400 missing_field
            {"text": "   \n\t  ", "creator_id": "eval_bad_space"},    # 400 missing_field
            {"creator_id": "eval_bad_missing"},                       # 400 missing_field
            {"text": None, "creator_id": "eval_bad_null"},            # 400 missing_field
            {"text": FORTY_NINE_WORDS},                               # 400 missing_field (no creator_id)
            {"text": FORTY_NINE_WORDS, "creator_id": "eval_bad_49"},  # 400 text_too_short
            {"text": "word " * 50000, "creator_id": "eval_bad_huge"}, # 413 text_too_long
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
