# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**  
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

A matching query only reaches a card if the parser and the search both line up
with how the listing is worded. `_parse_query` is a model call, so it can hand
search a size or price that doesn't match the listing's format. `search_listings`
only scores exact keyword overlap, so "t-shirt" can score 0 against a "tee".
Those misses come from keyword matching, not from a bug in the loop. Once search
returns something, `suggest_outfit` and `create_fit_card` have fallbacks, so a
card almost always comes out. One miss in five allows for wording. Two would mean
search is too brittle to rely on.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

Unlike criterion 1, this path doesn't depend on wording lining up. Search is
plain code, and the stop is a plain `if not session["search_results"]` check, so
the same empty list stops the loop every time. The only model step before it,
`_parse_query`, runs at temperature 0. If it ever drops the impossible constraint
and the agent goes on to `suggest_outfit`, that's a bug to fix, not variance to
allow for. That's why this path gets no slack.

---

## 3. Selected item is validated in the gap from search_listings to suggest_outfit

Given that `search_listings` succeeds and returns a non-empty list, `session["selected_item"]` is non-None on 5 out of 5 tries. Its id appears among the ids in `session["search_results"]`, and it matches exactly the id in `session["item_passed_to_suggest_outfit"]`.

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

**Why this target:** 
Nothing between the search call and the handoff touches a model. Mismatch can't be variance, it's a wiring bug. I compare ids rather than titles or whole dicts because ids are unique across listings, so there are no collisions. The search results clause is there because without it both sides of the comparison are the same expression and the criterion could never fail. Criterion 1 sits at 4 of 5 because its keyword match is fragile to phrasing; this one claims 5 of 5 because no model sits between the two points being compared.

---

## 4. The fit card always names the item's price

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

Given a run that reaches `create_fit_card` with a non-empty outfit, the returned caption contains `$` followed by the price of `session["selected_item"]`, on 5 out of 5 tries. `$18` and `$18.00` both count. A figure that doesn't match the listing price is a fail, and repeating the price is not.

**Why this target:** 
The price is a literal I pass into the prompt, so reproducing it is a copy rather than a generation, and that holds at temperature 0.9. `run_eval` turns caching off, so the five tries are five real samples and not one answer served five times. Cents are optional because `create_fit_card` is specified to read like a post rather than a product description, and every listing price is whole dollars — requiring `$18.00` would fail captions doing exactly what I asked for. The clause about matching the listing price is what makes this a check on the data reaching the card, not just on the caption containing a dollar sign. Also, for the empty wardrobe case in the second tool call, the scenario uses the example so that case never gets tested in the 5 of 5 attempts. I'm assuming that the empty wardrobe case will return general styling in the caption and still go to the `create_fit_card` tool call.

---

## 5. The price ceiling in the query reaches the search

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

Given the query `jacket under $40` and a non-empty `session["search_results"]`, `session["parsed"]["max_price"]` is 40 and every listing in `session["search_results"]` costs $40 or less, on 5 out of 5 tries. The ceiling is inclusive, so a listing at exactly $40 passes. A parsed ceiling of `None` is a fail, not a skip.

**Why this target:** 
The ceiling is stated in the query and the parse runs at `temperature=0.0`, so pulling it out is a copy rather than a judgment — the fit card stays at 0.9 because it has a different job. Caching is off during eval, so the five tries are five real extractions rather than one answer served five times. I check the parsed value and the returned prices separately because they fail in different files: a wrong `max_price` is a parsing bug in the loop, and a correct one with expensive results is a filter bug in `search_listings`. `jacket under $40` matches four listings, three of them over the ceiling including a $75 bomber, so the filter has real work to do and the criterion can actually fail. Inclusive because `tools.py` already specifies `max_price` that way and a dollar either side doesn't change a buying decision.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
