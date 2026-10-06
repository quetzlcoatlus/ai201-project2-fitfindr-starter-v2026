# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

This is an agent-powered application that helps you find your next "fit". A user fills our their wardrobe and asks the system for a new item. The system takes the user prompt and looks at their wardrobe before checking a set of listings. They get back a set of listings to check out with a caption written a caption. You stay in control of what to purchase next, the system helps with the tedium involved with comparing clothes across N different platforms. 

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Takes a description and searches listings data for items matching a size and price ceiling
- **Inputs:** <!-- name and type each: `max_price` (float), not "a price" --> `description` (str), `size` (str, optional — `None` skips size filtering), `max_price` (float, optional — `None` skips price filtering)
- **Returns:** A list of listing dictionaries, best match first
- **When it has nothing:** Returns an empty list

**What's sent in (assumptions about the parsed query):**
- `description` is the item the user wants, in plain words, with size and price words already removed by the parser. "small graphic tee under $30" arrives as `description="graphic tee"`, `size="S"`, `max_price=30.0`. Any filler words or stray numbers left over are removed by the tool.
- `size` is already in the format the data uses (`M`, `W30`, `W30 L30`, `US 8`, `One Size`), or `None` when the user didn't name one. The tool doesn't do any natural language processing, so the parser does the conversion:
  - "medium" or "med" → `M`
  - shoe sizes get the `US` prefix every shoe listing uses ("size 8" → `US 8`). Non-US sizes are converted in the listings size attribute.
  - two sizes are joined with a forward slash ("small or medium" → `S/M`)
- `max_price` is a float, or `None` when the user didn't give a price.

**Decisions and intent:**
- **Size matching is by token, not substring.** Sizes are split on `/`, notes in brackets are dropped (`XL (oversized)` → `XL`), and case is ignored. `"S"` never matches `"US 9"` and `"L"` never matches `"XL"`.
  - Waist and length match on their own: `W30` and `L30` each match `W30 L30`. `L30` is a length and never matches letter size `L`.
  - Asking for two sizes (`S/M`) matches listings with either or both.
  - One-size listings match every size.
- **Price filter** is inclusive (`price <= max_price`).
- **Keywords** are lowercased, with punctuation, bare numbers (`30`) and filler words removed. Plurals match singulars (`jeans` ↔ `jean`). Tokens that mix letters and digits (`90s`, `y2k`, `501s`) are kept as-is.
- **Fields searched:** everything except `id`, `price`, `size` and `description`. Descriptions are skipped because passing mentions ("layering under a graphic tee") ranked unrelated items as high as real matches. `brand` is `None` for most listings and is skipped safely.
- **Score** is the number of distinct query keywords a listing matches. Listings that score zero are dropped.
- **Order:** highest score first. On ties, when a specific size (not `One Size`) was requested, sized listings come before one-size listings, then cheaper first. At most `config.SEARCH_RESULT_LIMIT` results are returned.
- **No usable keywords** (e.g. "something under 30"): scoring is skipped and the size- and price-filtered listings come back in data order. One-size items go last when a size was requested.

### `suggest_outfit`

- **What it does:** Takes a thrifted item and the user's wardrobe to suggest one or two outfits they can make
- **Inputs:** `new_item` (dict), `wardrobe` (dict)
- **Returns:** A non-empty string with outfit suggestions.
- **When it has nothing:** On empty wardrobe, returns general stying advice

**What's sent in (assumptions about the inputs):**
- `new_item` is one listing dict, the first result from `search_listings`, with the fields listed in `data/listings.json`. Any field may be `None` (usually `brand`).
- `wardrobe` is a dict with an `items` list in the `data/wardrobe_schema.json` format: each piece has `name`, `category`, `colors`, `style_tags`, and an optional `notes` that may be `null`. A wardrobe that is `None`, has no `items` key, or has an empty `items` list is treated as empty.

**Decisions and intent:**
- **Item details in the prompt:** every field of the listing except `id`, including description, condition, price, brand and platform. Fields that are `None` are left out, so a missing brand never shows up as a blank.
- **Wardrobe details in the prompt:** one line per piece with name, category, colors and style tags. `notes` is included only when present, and wardrobe ids are left out because the model names pieces by name.
- **Wardrobe has items:** the model suggests one or two outfits (it picks how many). Each outfit uses the new item plus only pieces the user owns, named exactly as they appear in the wardrobe. Nothing they don't own is suggested.
- **Format:** one plain-text line per outfit, with no markdown: `Outfit N: <the new item and wardrobe pieces>. <One sentence on why it works.>`
- **Empty wardrobe:** a few sentences of general styling tips: the vibe the item gives off and the kinds of pieces it pairs with. No outfit labels.
- **Blank model reply:** returns a fixed message, `Couldn't generate outfit ideas for <title> right now.`, so the result is never empty.
- **Model unreachable:** `generate()` raises `ModelUnavailable`. `suggest_outfit` doesn't catch it, so the error reaches the handler in `agent.py::run_agent`.

### `create_fit_card`

- **What it does:** Writes a short caption someone would post about the find
- **Inputs:** `outfit` (str), `new_item` (dict) 
- **Returns:** A two-to-four sentence caption about the find
- **When it has nothing:** With no outfit, returns a descriptive message about the thrifted item

**What's sent in (assumptions about the inputs):**
- `outfit` is the string `suggest_outfit` returned: one or two `Outfit N:` lines, general styling tips (empty wardrobe), or its fallback message. It may also be empty, whitespace, or `None`.
- `new_item` is the same listing dict that went into `suggest_outfit`. Any field may be `None` (usually `brand`).

**Decisions and intent:**
- **No real outfit:** if `outfit` is empty, whitespace, `None`, or `suggest_outfit`'s `Couldn't generate outfit ideas for <title> right now.` message, the model isn't called. A fixed message describes the find instead: `No outfit to build a fit card from yet. The find: <title>, $<price> on <platform>.` Price and platform are left out of it if they're missing.
  - The fallback text lives in one constant (`_OUTFIT_FALLBACK`) shared by both tools, so changing the message can't break the check.
- **Item details in the prompt:** every field of the listing except `id`, with `None` fields left out (same as `suggest_outfit`).
- **Outfit in the prompt:** the whole suggestion. When there are two outfits, the caption can draw on both.
- **Caption rules:**
  - 2–4 sentences, first person, as the person who found it. Reads like a real post, not a product description.
  - Mentions the item, price and platform once each.
  - Price is written with a dollar sign and digits (`$38`), never in words.
  - The platform is where the item was found and bought, not where it's being sold.
  - Mentions the brand only when one is listed.
  - Specific about the vibe. Emojis allowed, no hashtags, no markdown.
- **Variety:** captions for the same item differ between runs because `config.TEMPERATURE` is 0.9. Caching follows config: answers are reused while building, and evaluation runs turn the cache off with `AI201_CACHE=0`.
- **Blank model reply:** returns `Couldn't write a fit card for <title> right now.`, which is separate from the no-outfit message.
- **Model unreachable:** `generate()` raises `ModelUnavailable`. `create_fit_card` doesn't catch it, so the error reaches the handler in `agent.py::run_agent`.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If search_listings returns an empty list, put a message in the session and stop. Otherwise, take the first result and go to suggest_outfit.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->Asking the model. Interprets maximum value and size from natural language in the query for robustness. Using temperature 0.0 for parsing.

**What moves through the session:**
- "query": query,              # what the user typed
- "parsed": {},                # description / size / max_price you pulled out of it
- "search_results": [],        # everything search_listings returned
- "selected_item": None,       # the one you chose — goes into suggest_outfit
- "item_passed_to_suggest_outfit": None,  # what actually reached the tool — criterion 3
- "wardrobe": wardrobe,        # the user's wardrobe
- "outfit_suggestion": None,   # what suggest_outfit returned
- "fit_card": None,            # what create_fit_card returned
- "error": None,               # set when the run ended early

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says mediumbut fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphictee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on thechest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; ..."
Outfit 1: Vintage Levi's 501 Jeans — Medium Wash, White ribbed tank top, Black cropped zip hoodie, Chunky white sneakers, Black crossbody bag. The cropped hoodie balances the straight-leg vintage fit while keeping the streetwear vibe sharp.

Outfit 2: Vintage Levi's 501 Jeans — Medium Wash, Oversized grey crewneck sweatshirt, Brown leather belt, Black combat boots. The brown belt adds a polished contrast to the cozy oversized crewneck and rugged boots.
```

```
$ python -c "from tools import create_fit_card; ..."
Found these vintage Levi's 501 jeans thrifting the other day and I am obsessed with the knee fading. They were only $38 on depop and fit like an absolute dream. Just threw them on with my beat-up white sneakers for the ultimate effortless running errandsvibe.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
