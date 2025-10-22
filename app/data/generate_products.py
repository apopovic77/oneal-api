#!/usr/bin/env python3
"""
Generate 100 realistic O'Neal products with picsum.photos images
"""
import json
import random

# Product templates by category
HELMETS = {
    "MX": ["Airframe", "Matrix", "Defender", "Fury", "Warp", "Sierra"],
    "MTB": ["3 Series", "Pike", "Sonus", "Blade"],
    "BMX": ["Dirt Lid", "Backflip"],
    "Street": ["Volt"]
}

JERSEYS = {
    "MX": ["Element", "Mayhem Lite", "Hardwear", "Ultra Lite", "Threat"],
    "MTB": ["Pin It", "Stormrider"],
    "BMX": ["Threat"]
}

PANTS = {
    "MX": ["Element", "Mayhem Lite", "Hardwear", "Ultra Lite"],
    "MTB": ["Pin It", "Stormrider"],
    "BMX": ["Threat"]
}

GLOVES = ["Matrix", "Element", "Mayhem", "Hardwear", "Revolution"]

PROTECTION = {
    "Chest": ["Peewee", "Holeshot", "Pro"],
    "Knee": ["Dirt", "Pro III", "Sinner"],
    "Elbow": ["Dirt", "Pro III"],
    "Neck": ["Tron", "NX1"]
}

BOOTS = ["Rider Pro", "RSX", "RMX", "Element", "Shorty"]

GOGGLES = ["B-50", "B-30", "B-20", "B-10", "B-Zero"]

# Color variations
COLORS = [
    ["Black", "White", "Red"],
    ["Blue", "Yellow", "Black"],
    ["Green", "Black", "White"],
    ["Red", "Blue", "White"],
    ["Orange", "Black", "Gray"],
    ["Purple", "Yellow", "Black"],
    ["Teal", "Orange", "White"],
    ["Black", "Gray", "Red"],
    ["White", "Blue", "Yellow"],
    ["Red", "White", "Black"]
]

# Size ranges
SIZES_HELMET = ["XS", "S", "M", "L", "XL", "XXL"]
SIZES_APPAREL = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
SIZES_GLOVES = ["XS", "S", "M", "L", "XL", "XXL"]
SIZES_PROTECTION = ["S/M", "L/XL", "XXL"]
SIZES_BOOTS = ["39", "40", "41", "42", "43", "44", "45", "46", "47"]
SIZES_GOGGLES = ["One Size"]

# Materials
MATERIALS_HELMET = ["ABS Shell", "Polycarbonate", "Carbon Fiber", "Fiberglass"]
MATERIALS_APPAREL = ["Polyester", "Mesh", "Spandex"]
MATERIALS_PROTECTION = ["EVA Foam", "Hard Shell", "D3O", "Soft Foam"]

# Certifications
CERT_HELMET = ["ECE 22.06", "DOT", "AS/NZS 1698"]
CERT_PROTECTION = ["CE EN 1621-1", "CE EN 1621-2"]

def generate_id(category_prefix, index):
    """Generate product ID"""
    return f"{category_prefix}-2026-{str(index).zfill(3)}"

def generate_sku(category, name, variant):
    """Generate SKU"""
    clean_name = name.replace(" ", "").replace("'", "").upper()[:6]
    return f"ONL-{category[:2].upper()}-{clean_name}-{variant}"

def get_picsum_url(width, height, seed):
    """Generate picsum.photos URL with seed for consistency"""
    return f"https://picsum.photos/seed/{seed}/{width}/{height}"

def generate_media(product_id, num_detail=2, num_lifestyle=1):
    """Generate media array with picsum images"""
    media = []

    # Hero image
    media.append({
        "id": f"{product_id}-hero",
        "role": "hero",
        "src": get_picsum_url(800, 800, product_id),
        "alt": "Product hero image",
        "featured": True
    })

    # Detail images
    for i in range(num_detail):
        media.append({
            "id": f"{product_id}-detail-{i+1}",
            "role": "detail",
            "src": get_picsum_url(800, 800, f"{product_id}-d{i}"),
            "alt": f"Product detail view {i+1}"
        })

    # Lifestyle images
    for i in range(num_lifestyle):
        media.append({
            "id": f"{product_id}-lifestyle-{i+1}",
            "role": "lifestyle",
            "src": get_picsum_url(1200, 800, f"{product_id}-l{i}"),
            "alt": f"Product lifestyle image {i+1}",
            "caption": f"In action - {product_id}"
        })

    return media

def generate_helmet(category, series, variant_index, product_index):
    """Generate helmet product"""
    product_id = generate_id("HLM", product_index)
    colors = random.choice(COLORS)
    tier = random.choice(["entry", "mid", "premium"])

    price_ranges = {"entry": (129, 179), "mid": (199, 299), "premium": (349, 499)}
    price = random.randrange(*price_ranges[tier], 10)

    variant_names = ["Solid", "Slick", "Nova", "Carbon", "Fidlock", "Graphic"]
    variant = variant_names[variant_index % len(variant_names)]

    return {
        "id": product_id,
        "sku": generate_sku("Helmet", series, variant),
        "name": f"{series} {category} {variant}",
        "brand": "O'Neal",
        "category": ["Helmets", category],
        "season": 2026,
        "status": "active",
        "description": {
            "short": f"High-performance {category} helmet with advanced ventilation and safety features.",
            "long": f"The {series} {variant} is engineered for {category.lower()} riders who demand the best. Featuring a lightweight {random.choice(MATERIALS_HELMET)} shell, multi-density EPS liner, and optimized ventilation system. The helmet offers superior protection while maintaining excellent comfort during long rides."
        },
        "tier": tier,
        "series_id": f"series-{series.lower().replace(' ', '-')}",
        "series_name": series,
        "key_features": [
            f"Lightweight {random.choice(MATERIALS_HELMET)} construction",
            "Multi-density EPS liner",
            "Advanced ventilation system",
            "Moisture-wicking interior",
            "Emergency release cheek pads"
        ],
        "certifications": random.sample(CERT_HELMET, k=random.randint(1, 2)),
        "materials": random.sample(MATERIALS_HELMET, k=random.randint(1, 2)),
        "colors": colors,
        "sizes": SIZES_HELMET,
        "price": {
            "currency": "EUR",
            "value": float(price),
            "formatted": f"€{price}.00"
        },
        "specifications": {
            "weight": random.randint(1100, 1450),
            "shell_material": random.choice(MATERIALS_HELMET),
            "liner_material": "Multi-density EPS"
        },
        "media": generate_media(product_id, num_detail=2, num_lifestyle=2),
        "datasheets": [
            {
                "title": "Product Specifications",
                "url": f"https://www.oneal.eu/media/pdf/{product_id}-specs.pdf",
                "type": "pdf"
            }
        ]
    }

def generate_jersey(category, series, variant_index, product_index):
    """Generate jersey product"""
    product_id = generate_id("JER", product_index)
    colors = random.choice(COLORS)
    tier = random.choice(["entry", "mid", "premium"])

    price_ranges = {"entry": (39, 49), "mid": (59, 79), "premium": (89, 129)}
    price_base = random.randrange(*price_ranges[tier], 10)
    price = price_base + 0.99

    variant_names = ["Solid", "Camo", "Graphic", "Race", "Factory"]
    variant = variant_names[variant_index % len(variant_names)]

    return {
        "id": product_id,
        "sku": generate_sku("Jersey", series, variant),
        "name": f"{series} {category} Jersey {variant}",
        "brand": "O'Neal",
        "category": ["Apparel", "Jerseys", category],
        "season": 2026,
        "status": "active",
        "description": {
            "short": f"Lightweight, breathable {category} jersey designed for maximum performance.",
            "long": f"The {series} {variant} jersey combines cutting-edge fabric technology with rider-focused design. Constructed from moisture-wicking materials with strategic ventilation zones, this jersey keeps you cool and comfortable in the most demanding conditions."
        },
        "tier": tier,
        "series_id": f"series-{series.lower().replace(' ', '-')}",
        "series_name": series,
        "key_features": [
            "Moisture-wicking fabric",
            "Strategic ventilation panels",
            "Sublimated graphics",
            "Extended back hem",
            "Raglan sleeves for freedom of movement"
        ],
        "materials": ["Polyester", "Mesh", "Spandex"],
        "colors": colors,
        "sizes": SIZES_APPAREL,
        "price": {
            "currency": "EUR",
            "value": price,
            "formatted": f"€{price:.2f}"
        },
        "media": generate_media(product_id, num_detail=2, num_lifestyle=2)
    }

def generate_pants(category, series, variant_index, product_index):
    """Generate pants product"""
    product_id = generate_id("PNT", product_index)
    colors = random.choice(COLORS)
    tier = random.choice(["entry", "mid", "premium"])

    price_ranges = {"entry": (99, 129), "mid": (149, 189), "premium": (199, 249)}
    price = random.randrange(*price_ranges[tier], 10) + 0.99

    variant_names = ["Solid", "Camo", "Graphic", "Race", "Factory"]
    variant = variant_names[variant_index % len(variant_names)]

    return {
        "id": product_id,
        "sku": generate_sku("Pants", series, variant),
        "name": f"{series} {category} Pants {variant}",
        "brand": "O'Neal",
        "category": ["Apparel", "Pants", category],
        "season": 2026,
        "status": "active",
        "description": {
            "short": f"Durable {category} pants with reinforced knees and adjustable fit.",
            "long": f"The {series} {variant} pants are built to withstand the toughest conditions. Featuring heavy-duty construction with reinforced high-wear areas, ventilation zones, and a comfortable athletic fit that moves with you."
        },
        "tier": tier,
        "series_id": f"series-{series.lower().replace(' ', '-')}",
        "series_name": series,
        "key_features": [
            "Reinforced knees and seat",
            "Leather heat shield panels",
            "Adjustable waist closure",
            "Pre-curved leg design",
            "Multiple ventilation zones"
        ],
        "materials": ["600D Polyester", "Mesh", "Leather"],
        "colors": colors,
        "sizes": SIZES_APPAREL,
        "price": {
            "currency": "EUR",
            "value": price,
            "formatted": f"€{price:.2f}"
        },
        "media": generate_media(product_id, num_detail=2, num_lifestyle=2)
    }

def generate_gloves(series, variant_index, product_index):
    """Generate gloves product"""
    product_id = generate_id("GLV", product_index)
    colors = random.choice(COLORS)
    tier = random.choice(["entry", "mid", "premium"])

    price_ranges = {"entry": (19, 29), "mid": (34, 44), "premium": (49, 69)}
    price = random.randrange(*price_ranges[tier], 5) + 0.99

    variant_names = ["Solid", "Graphic", "Camo"]
    variant = variant_names[variant_index % len(variant_names)]

    return {
        "id": product_id,
        "sku": generate_sku("Gloves", series, variant),
        "name": f"{series} Gloves {variant}",
        "brand": "O'Neal",
        "category": ["Apparel", "Gloves"],
        "season": 2026,
        "status": "active",
        "description": {
            "short": "Durable gloves with excellent grip and protection.",
            "long": f"The {series} {variant} gloves provide the perfect balance of protection, comfort, and bar feel. Featuring reinforced palms, flexible knuckle protection, and touchscreen-compatible fingertips."
        },
        "tier": tier,
        "series_id": f"series-{series.lower()}",
        "series_name": series,
        "key_features": [
            "Reinforced palm with silicone print",
            "Flexible TPR knuckle protection",
            "Touchscreen compatible",
            "Hook and loop wrist closure",
            "Perforated for ventilation"
        ],
        "materials": ["Polyester", "Synthetic Leather", "TPR"],
        "colors": colors,
        "sizes": SIZES_GLOVES,
        "price": {
            "currency": "EUR",
            "value": price,
            "formatted": f"€{price:.2f}"
        },
        "media": generate_media(product_id, num_detail=1, num_lifestyle=1)
    }

def generate_protection(category, series, variant_index, product_index):
    """Generate protection gear product"""
    product_id = generate_id("PRT", product_index)
    tier = random.choice(["entry", "mid", "premium"])

    price_ranges = {"entry": (59, 89), "mid": (99, 149), "premium": (159, 229)}
    price = random.randrange(*price_ranges[tier], 10) + 0.99

    return {
        "id": product_id,
        "sku": generate_sku(category, series, "BLK"),
        "name": f"{series} {category} Guard",
        "brand": "O'Neal",
        "category": ["Protection", category],
        "season": 2026,
        "status": "active",
        "description": {
            "short": f"High-impact {category.lower()} protection with comfortable fit.",
            "long": f"The {series} {category} Guard offers comprehensive protection without compromising mobility. Featuring shock-absorbing foam, hard shell construction, and adjustable straps for a secure fit."
        },
        "tier": tier,
        "series_id": f"series-{series.lower()}",
        "series_name": series,
        "key_features": [
            "CE certified protection",
            "Impact-absorbing foam",
            "Moisture-wicking liner",
            "Adjustable straps",
            "Lightweight construction"
        ],
        "certifications": random.sample(CERT_PROTECTION, k=random.randint(1, 2)),
        "materials": random.sample(MATERIALS_PROTECTION, k=2),
        "colors": ["Black"],
        "sizes": SIZES_PROTECTION,
        "price": {
            "currency": "EUR",
            "value": price,
            "formatted": f"€{price:.2f}"
        },
        "media": generate_media(product_id, num_detail=2, num_lifestyle=1)
    }

def generate_boots(series, variant_index, product_index):
    """Generate boots product"""
    product_id = generate_id("BOT", product_index)
    tier = random.choice(["mid", "premium"])

    price_ranges = {"mid": (199, 299), "premium": (349, 499)}
    price = random.randrange(*price_ranges[tier], 10) + 0.99

    colors_boot = [["Black"], ["Black", "White"], ["Black", "Red"]]
    colors = random.choice(colors_boot)

    return {
        "id": product_id,
        "sku": generate_sku("Boots", series, "STD"),
        "name": f"{series} MX Boots",
        "brand": "O'Neal",
        "category": ["Footwear", "Boots", "MX"],
        "season": 2026,
        "status": "active",
        "description": {
            "short": "Professional-grade MX boots with maximum protection and comfort.",
            "long": f"The {series} boots combine race-proven protection with all-day comfort. Featuring a rigid chassis, flexible joint system, and a secure closure mechanism that provides precise fit and support."
        },
        "tier": tier,
        "series_id": f"series-{series.lower().replace(' ', '-')}",
        "series_name": series,
        "key_features": [
            "Rigid thermoplastic shell",
            "Four aluminum buckle closure",
            "Steel shank sole",
            "Replaceable toe cap",
            "Gaiter system"
        ],
        "certifications": ["CE EN 13634"],
        "materials": ["Thermoplastic", "Aluminum", "Steel"],
        "colors": colors,
        "sizes": SIZES_BOOTS,
        "price": {
            "currency": "EUR",
            "value": price,
            "formatted": f"€{price:.2f}"
        },
        "specifications": {
            "weight": random.randint(2200, 2800),
            "dimensions": "EU 40-47"
        },
        "media": generate_media(product_id, num_detail=2, num_lifestyle=1)
    }

def generate_goggles(series, variant_index, product_index):
    """Generate goggles product"""
    product_id = generate_id("GOG", product_index)
    tier = random.choice(["entry", "mid", "premium"])

    price_ranges = {"entry": (29, 39), "mid": (49, 69), "premium": (79, 99)}
    price = random.randrange(*price_ranges[tier], 10) + 0.99

    colors_frame = [["Black"], ["White"], ["Blue"], ["Red"], ["Orange"]]
    colors = random.choice(colors_frame)

    lens_types = ["Clear", "Tinted", "Mirror Blue", "Mirror Gold", "Photochromic"]
    lens = lens_types[variant_index % len(lens_types)]

    return {
        "id": product_id,
        "sku": generate_sku("Goggles", series, lens[:3]),
        "name": f"{series} Goggles {lens}",
        "brand": "O'Neal",
        "category": ["Eyewear", "Goggles"],
        "season": 2026,
        "status": "active",
        "description": {
            "short": "High-performance goggles with superior optics and comfort.",
            "long": f"The {series} goggles feature a wide field of vision, anti-fog coating, and a flexible frame that conforms to your face. The {lens.lower()} lens provides optimal visibility in various conditions."
        },
        "tier": tier,
        "series_id": f"series-{series.lower()}",
        "series_name": series,
        "key_features": [
            f"{lens} lens with anti-fog coating",
            "100% UV protection",
            "Triple-layer face foam",
            "Wide silicone strap",
            "Tear-off compatible"
        ],
        "materials": ["Polycarbonate", "TPU", "Silicone"],
        "colors": colors,
        "sizes": SIZES_GOGGLES,
        "price": {
            "currency": "EUR",
            "value": price,
            "formatted": f"€{price:.2f}"
        },
        "media": generate_media(product_id, num_detail=1, num_lifestyle=1)
    }

def main():
    products = []
    product_index = 1

    # Generate Helmets (30 products)
    for category, series_list in HELMETS.items():
        for series in series_list:
            for variant_idx in range(random.randint(1, 2)):
                products.append(generate_helmet(category, series, variant_idx, product_index))
                product_index += 1
                if len(products) >= 30:
                    break
            if len(products) >= 30:
                break
        if len(products) >= 30:
            break

    # Generate Jerseys (20 products)
    jersey_count = 0
    for category, series_list in JERSEYS.items():
        for series in series_list:
            for variant_idx in range(random.randint(1, 2)):
                products.append(generate_jersey(category, series, variant_idx, product_index))
                product_index += 1
                jersey_count += 1
                if jersey_count >= 20:
                    break
            if jersey_count >= 20:
                break
        if jersey_count >= 20:
            break

    # Generate Pants (20 products)
    pants_count = 0
    for category, series_list in PANTS.items():
        for series in series_list:
            for variant_idx in range(random.randint(1, 2)):
                products.append(generate_pants(category, series, variant_idx, product_index))
                product_index += 1
                pants_count += 1
                if pants_count >= 20:
                    break
            if pants_count >= 20:
                break
        if pants_count >= 20:
            break

    # Generate Gloves (10 products)
    for idx, series in enumerate(GLOVES * 2):  # Repeat to get 10
        products.append(generate_gloves(series, idx, product_index))
        product_index += 1
        if len(products) >= 80:  # 30+20+20+10
            break

    # Generate Protection (10 products)
    protection_count = 0
    for category, series_list in PROTECTION.items():
        for series in series_list:
            products.append(generate_protection(category, series, 0, product_index))
            product_index += 1
            protection_count += 1
            if protection_count >= 10:
                break
        if protection_count >= 10:
            break

    # Generate Boots (5 products)
    for idx, series in enumerate(BOOTS):
        products.append(generate_boots(series, idx, product_index))
        product_index += 1

    # Generate Goggles (5 products)
    for idx, series in enumerate(GOGGLES):
        products.append(generate_goggles(series, idx, product_index))
        product_index += 1

    # Ensure we have exactly 100 products
    while len(products) < 100:
        # Add more variants of existing series
        products.append(generate_helmet("MX", "Airframe", len(products), product_index))
        product_index += 1

    # Save to JSON
    output = products[:100]  # Limit to exactly 100

    print(f"Generated {len(output)} products")
    print(f"\nBreakdown:")
    categories = {}
    for p in output:
        cat = p['category'][0]
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    return output

if __name__ == "__main__":
    products = main()
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print("\n✅ products.json created!")
