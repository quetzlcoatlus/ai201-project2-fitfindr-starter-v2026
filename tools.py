"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

_STOPWORDS = {
    "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about",
    "a", "an", "i", "im", "me", "my", "is", "are", "it", "its", "of", "that",
    "this", "some", "any", "something", "anything", "want", "need", "looking",
    "find", "show", "get", "like", "would", "could", "please", "just", "really",
    "very", "under", "around", "less", "than", "size", "price", "dollars",
}

def _singular(word: str) -> str:
    """Crude plural stripping so "jeans" matches "jean". Words with digits are left alone."""
    if any(c.isdigit() for c in word) or len(word) <= 3:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"      # accessories -> accessory
    if word.endswith("sses"):
        return word[:-2]            # dresses -> dress
    if word.endswith("s") and not word.endswith(("ss", "us")):
        return word[:-1]            # shorts -> short
    return word

def _keywords(text: str) -> set[str]:
    """Lowercase, singular words worth matching; punctuation, bare numbers and stopwords removed."""
    cleaned = re.sub(r"['’]", "", (text or "").lower())  # "levi's" -> "levis"
    words = re.sub(r"[^a-z0-9]+", " ", cleaned).split()
    return {
        _singular(word) for word in words
        if word not in _STOPWORDS and not word.isdigit()
    }

_MEASUREMENT = re.compile(r"[WL]\d+(\.\d+)?")

def _size_tokens(size: str) -> set[str]:
    """Convert a size string into a set of normalized tokens."""
    cleaned = re.sub(r"\([^)]*\)", "", size or "")
    tokens = set()
    for part in cleaned.upper().split("/"):
        words = part.split()
        # "W30 L30" -> {"W30", "L30"}, so waist and length match on their own
        if words and all(_MEASUREMENT.fullmatch(w) for w in words):
            tokens.update(words)
        elif part.strip():
            tokens.add(" ".join(words))
    return tokens

_UNSEARCHED_FIELDS = {"id", "price", "size", "description"}

def _listing_keywords(listing: dict) -> set[str]:
    """Keywords from every searchable field of a listing, skipping None values."""
    words = set()
    for field, value in listing.items():
        if field in _UNSEARCHED_FIELDS or value is None:
            continue
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        words |= _keywords(str(value))
    return words

def _is_one_size(size: str) -> bool:
    """True when a size string includes "One Size"."""
    return any(token.startswith("ONE SIZE") for token in _size_tokens(size))

def _size_matches(wanted: str, listing_size: str) -> bool:
    """Check if a wanted size matches a listing's size string."""
    if not wanted:
        return True
    if _is_one_size(listing_size):
        return True
    return bool(_size_tokens(wanted) & _size_tokens(listing_size))


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    # Load all listings from the data source
    listings = load_listings()

    # Filter by max_price and size respectively when provided
    if max_price is not None:
        listings = [l for l in listings if l.get("price", float("inf")) <= max_price]

    if size is not None:
        listings = [l for l in listings if _size_matches(size, l.get("size", ""))]

    # When a specific size was asked for, one-size items rank after sized ones
    # on ties. 0 = normal, 1 = pushed down.
    demote_one_size = bool(size) and not _is_one_size(size)
    def one_size_rank(listing: dict) -> int:
        return int(demote_one_size and _is_one_size(listing.get("size", "")))

    # No usable keywords: skip scoring and return the filtered listings in
    # data order (sorted() is stable, so only one-size items move)
    wanted = _keywords(description)
    if not wanted:
        listings = sorted(listings, key=one_size_rank)
        return listings[:config.SEARCH_RESULT_LIMIT]

    # Score by distinct keyword overlap with description, dropping zeros
    scored = []
    for listing in listings:
        score = len(wanted & _listing_keywords(listing))
        if score > 0:
            scored.append((score, listing))

    # Highest score first; on ties, sized before one-size, then cheaper first
    scored.sort(key=lambda pair: (
        -pair[0],
        one_size_rank(pair[1]),
        pair[1].get("price", float("inf")),
    ))
    return [listing for _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

# create_fit_card checks for this text, so keep the two in sync through here
_OUTFIT_FALLBACK = "Couldn't generate outfit ideas for {title} right now."

_STYLIST_SYSTEM = (
    "You are a practical stylist who helps people wear secondhand clothes. "
    "Be specific and brief."
)

def _format_value(value) -> str:
    """Lists become comma-separated text; everything else is str()."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)

def _describe_item(listing: dict) -> str:
    """Every known field of a listing except its id, skipping None values."""
    lines = []
    for field, value in listing.items():
        if field == "id" or value is None:
            continue
        if field == "price":
            value = f"${value:.2f}"
        lines.append(f"{field}: {_format_value(value)}")
    return "\n".join(lines)

def _describe_wardrobe_item(item: dict) -> str:
    """One wardrobe piece on one line; notes only when present."""
    parts = [
        item.get("name", "unnamed item"),
        f"category: {item.get('category', 'unknown')}",
        f"colors: {_format_value(item.get('colors') or [])}",
        f"style: {_format_value(item.get('style_tags') or [])}",
    ]
    if item.get("notes"):
        parts.append(f"notes: {item['notes']}")
    return "- " + " | ".join(parts)

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    # A missing or malformed wardrobe is treated the same as an empty one
    items = (wardrobe or {}).get("items") or []
    item_text = _describe_item(new_item)

    if not items:
        prompt = (
            "The user is considering this thrifted item but hasn't added their "
            "wardrobe yet.\n\n"
            f"{item_text}\n\n"
            "Give a few sentences of general styling tips for it: the vibe it "
            "gives off and what kinds of pieces it pairs well with. Plain text, "
            "no markdown, no outfit labels."
        )
    else:
        wardrobe_text = "\n".join(_describe_wardrobe_item(i) for i in items)
        prompt = (
            "The user is considering this thrifted item:\n\n"
            f"{item_text}\n\n"
            "Their wardrobe:\n"
            f"{wardrobe_text}\n\n"
            "Suggest one or two outfits. Each outfit uses the new item plus "
            "only pieces from the wardrobe above, named exactly as written. Do "
            "not suggest anything they don't own. Format each outfit on its own "
            "line as:\n"
            "Outfit N: <the new item and the wardrobe pieces>. <One sentence on "
            "why it works.>\n"
            "Plain text, no markdown."
        )

    response = generate(prompt, system=_STYLIST_SYSTEM)
    if not response.strip():
        return _OUTFIT_FALLBACK.format(title=new_item.get("title", "this item"))
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

_CAPTION_SYSTEM = (
    "You write short, casual social media captions about thrifted clothes. "
    "You sound like a real person posting, never like a store listing."
)

_OUTFIT_FALLBACK_PATTERN = re.compile(
    re.escape(_OUTFIT_FALLBACK).replace(re.escape("{title}"), ".*")
)

def _is_outfit_fallback(outfit: str) -> bool:
    """True when `outfit` is suggest_outfit's "couldn't generate" message."""
    return bool(_OUTFIT_FALLBACK_PATTERN.fullmatch(outfit.strip()))

def _no_outfit_message(listing: dict) -> str:
    """Fixed description of the find for when there's no outfit to caption."""
    find = listing.get("title", "this item")
    if listing.get("price") is not None:
        find += f", ${listing['price']:.2f}"
    if listing.get("platform"):
        find += f" on {listing['platform']}"
    return f"No outfit to build a fit card from yet. The find: {find}."

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    title = new_item.get("title", "this item")

    # No real outfit (blank, or suggest_outfit's own fallback): describe the
    # find without calling the model
    if not (outfit or "").strip() or _is_outfit_fallback(outfit):
        return _no_outfit_message(new_item)

    prompt = (
        "Write a caption for a social media post about this thrifted find.\n\n"
        f"The item:\n{_describe_item(new_item)}\n\n"
        f"How I'm styling it:\n{outfit.strip()}\n\n"
        "Rules:\n"
        "- Two to four sentences, first person, as the person who found it.\n"
        "- Read like a real post, not a product description.\n"
        "- Mention the item, its price, and the platform once each.\n"
        "- Write the price with a dollar sign and digits, like $38, never in "
        "words.\n"
        "- The platform is where I found and bought the item, not where I'm "
        "selling it.\n"
        "- Mention the brand only if one is listed above.\n"
        "- Be specific about the vibe of the styling.\n"
        "- Emojis are fine. No hashtags. Plain text, no markdown."
    )

    response = generate(prompt, system=_CAPTION_SYSTEM)
    if not response.strip():
        return f"Couldn't write a fit card for {title} right now."
    return response
