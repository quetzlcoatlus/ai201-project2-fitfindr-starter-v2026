"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import json
import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import generate, ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "item_passed_to_suggest_outfit": None,  # what actually reached the tool — criterion 3
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "next_step": "parse",        # which step the loop runs next; "done" ends it
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # Every tool reads its inputs back out of the session, never from a local
    # carried over from the previous step — that's what keeps the state visible.
    count = 0
    while session["next_step"] != "done":
        count += 1
        trace.check_iterations(count)

        if session["next_step"] == "parse":
            session["parsed"] = _parse_query(session["query"]) or {}
            if not session["parsed"]:
                session["error"] = _PARSE_FAILED_MESSAGE
                session["next_step"] = "done"
            else:
                session["next_step"] = "search"

        elif session["next_step"] == "search":
            session["search_results"] = search_listings(
                session["parsed"]["description"],
                session["parsed"]["size"],
                session["parsed"]["max_price"],
            )
            # The branch: nothing to style means nothing to suggest.
            if not session["search_results"]:
                session["error"] = _NO_RESULTS_MESSAGE
                session["next_step"] = "done"
            else:
                session["selected_item"] = session["search_results"][0]
                session["next_step"] = "suggest"

        elif session["next_step"] == "suggest":
            session["item_passed_to_suggest_outfit"] = session["selected_item"]
            session["outfit_suggestion"] = suggest_outfit(
                session["item_passed_to_suggest_outfit"], session["wardrobe"]
            )
            session["next_step"] = "card"

        elif session["next_step"] == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            session["next_step"] = "done"

    return session


# ── query parsing ─────────────────────────────────────────────────────────────

_NO_RESULTS_MESSAGE = (
    "Nothing matched that search. Try a higher price limit, a different size, "
    "or broader words for the item (e.g. \"jacket\" instead of \"designer "
    "bomber jacket\")."
)

_PARSE_FAILED_MESSAGE = (
    "Couldn't understand that request. Try naming the item, then any size and "
    "price limit, e.g. \"graphic tee under $30, size M\"."
)

_PARSER_SYSTEM = (
    "You turn a thrift-shopping request into JSON for a search tool. "
    "Reply with only a JSON object, no markdown and no commentary."
)

_PARSER_PROMPT = """Extract three fields from the request below.

- "description": the item the user wants, in plain words (style words like
  "vintage" stay). Remove every size and price word.
- "size": the size in the format the listings use, or null if none is named.
    - letter sizes: XXS, XS, S, M, L, XL, XXL ("medium" or "med" -> "M",
      "small" -> "S", "large" -> "L", "extra large" -> "XL")
    - shoe sizes get a "US " prefix ("size 8" -> "US 8", "8.5" -> "US 8.5")
    - waist and length: "30 waist" -> "W30", "30x30" -> "W30 L30"
    - "one size" -> "One Size"
    - two sizes are joined with "/" ("small or medium" -> "S/M")
- "max_price": the price ceiling as a number ("under $30" -> 30), or null if
  none is named.

Example: "small graphic tee under $30" ->
{{"description": "graphic tee", "size": "S", "max_price": 30}}

Request: {query}"""


def _parse_query(query: str) -> dict | None:
    """
    Ask the model to split the query into description / size / max_price.

    Returns None when the reply isn't usable — the loop stops on that rather
    than searching with a guess.
    """
    reply = generate(
        _PARSER_PROMPT.format(query=query),
        system=_PARSER_SYSTEM,
        temperature=0.0,
    )

    # Models sometimes wrap JSON in a ```json fence despite being told not to.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", reply.strip())
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        return None

    size = data.get("size")
    if not isinstance(size, str) or not size.strip():
        size = None

    max_price = data.get("max_price")
    if isinstance(max_price, bool) or not isinstance(max_price, (int, float, type(None))):
        return None
    if max_price is not None:
        max_price = float(max_price)

    return {
        "description": description.strip(),
        "size": size.strip() if size else None,
        "max_price": max_price,
    }


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    # Check selected item is the same as the one passed to suggest_outfit
    print(f"  selected_item: {item['id']}")
    print(f"  item_passed_to_suggest_outfit: {session['item_passed_to_suggest_outfit']['id']}")

    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
