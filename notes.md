# Example listings

python app.py listings --full -n 6
{
  "id": "lst_001",
  "title": "Vintage Levi's 501 Jeans \u2014 Medium Wash",
  "description": "Classic 501s in a perfect medium wash. Some light fading at the knees which adds to the vintage look. No rips or stains.",
  "category": "bottoms",
  "style_tags": [
    "vintage",
    "classic",
    "denim",
    "streetwear"
  ],
  "size": "W30 L30",
  "condition": "good",
  "price": 38.0,
  "colors": [
    "blue",
    "indigo"
  ],
  "brand": "Levi's",
  "platform": "depop"
}

{
  "id": "lst_002",
  "title": "Y2K Baby Tee \u2014 Butterfly Print",
  "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
  "category": "tops",
  "style_tags": [
    "y2k",
    "vintage",
    "graphic tee",
    "cottagecore"
  ],
  "size": "S/M",
  "condition": "excellent",
  "price": 18.0,
  "colors": [
    "white",
    "pink",
    "purple"
  ],
  "brand": null,
  "platform": "depop"
}

{
  "id": "lst_003",
  "title": "Oversized Flannel Shirt \u2014 Plaid Red/Black",
  "description": "Classic oversized flannel. Great layering piece. A few tiny pulls in the fabric but nothing visible when worn.",
  "category": "tops",
  "style_tags": [
    "grunge",
    "vintage",
    "flannel",
    "streetwear",
    "layering"
  ],
  "size": "XL (oversized)",
  "condition": "good",
  "price": 22.0,
  "colors": [
    "red",
    "black"
  ],
  "brand": "Woolrich",
  "platform": "thredUp"
}

{
  "id": "lst_004",
  "title": "90s Track Jacket \u2014 Navy/White Stripe",
  "description": "Authentic 90s track jacket with stripe detail down the sleeves. Full zip. Lightweight \u2014 great for layering.",
  "category": "outerwear",
  "style_tags": [
    "90s",
    "vintage",
    "athletic",
    "streetwear"
  ],
  "size": "M",
  "condition": "excellent",
  "price": 45.0,
  "colors": [
    "navy",
    "white"
  ],
  "brand": "Champion",
  "platform": "poshmark"
}

{
  "id": "lst_005",
  "title": "Corduroy Wide-Leg Pants \u2014 Rust",
  "description": "Beautiful rust-colored cords in a wide-leg silhouette. High-waisted. Minor pilling on the seat but otherwise great condition.",
  "category": "bottoms",
  "style_tags": [
    "vintage",
    "cottagecore",
    "70s",
    "earth tones"
  ],
  "size": "W28",
  "condition": "good",
  "price": 32.0,
  "colors": [
    "rust",
    "orange"
  ],
  "brand": null,
  "platform": "depop"
}

{
  "id": "lst_006",
  "title": "Graphic Tee \u2014 2003 Tour Bootleg Style",
  "description": "Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.",
  "category": "tops",
  "style_tags": [
    "graphic tee",
    "vintage",
    "grunge",
    "streetwear",
    "band tee"
  ],
  "size": "L",
  "condition": "good",
  "price": 24.0,
  "colors": [
    "black"
  ],
  "brand": null,
  "platform": "depop"
}

# Field names

Listing Item
1. id: str
2. title: str
3. description: str
4. category: str
5. style_tags: list[str]
6. size: str
7. price: float
8. colors: list[str]
9. brand: str
10. platform: str

Wardrobe Item
1. id: str
2. name: str
3. category: str
4. colors: list[str]
5. style_tags: list[str]
6. notes: str

# Wardrobe Shape
With a new user, wardrobe is json schema with a name and an items list nested in the name

"empty_wardrobe": {
"_note": "Use this as the starting template for a new user with no wardrobe entered yet.",
"items": []
}

