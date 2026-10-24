"""Version 1 public listing search text; display/user text is never rewritten."""

import re
import unicodedata

ALIASES = {
    "اوضه": "غرفه",
    "اوضة": "غرفه",
    "غرفة": "غرفه",
    "غرف": "غرفه",
    "room": "غرفه",
    "rooms": "غرفه",
    "اسانسير": "مصعد",
    "اسانصير": "مصعد",
    "elevator": "مصعد",
    "واي فاي": "wifi",
    "واى فاى": "wifi",
    "وايفاي": "wifi",
    "انترنت": "wifi",
    "furnished": "مفروش",
    "مفروشه": "مفروش",
    "مفروشة": "مفروش",
    "apartment": "شقه",
    "شقة": "شقه",
    "bed": "سرير",
    "air conditioning": "تكييف",
}
AMENITIES = {
    "wifi": "has_wifi",
    "مصعد": "has_elevator",
    "مفروش": "is_furnished",
    "تكييف": "has_air_conditioning",
    "بلكونه": "has_balcony",
    "جراج": "has_garage",
    "امن": "has_security",
    "مترو": "near_metro",
    "غاز": "has_natural_gas",
}
STOP = {
    "عايز",
    "عاوز",
    "اريد",
    "في",
    "فيها",
    "به",
    "بها",
    "مع",
    "علي",
    "من",
    "اللي",
    "يكون",
    "a",
    "an",
    "with",
    "and",
    "the",
    "in",
}


def normalize(text):
    text = "".join(
        c
        for c in unicodedata.normalize("NFKC", str(text)).casefold()
        if not unicodedata.combining(c)
    )
    text = text.translate(
        str.maketrans("أإآٱىة٠١٢٣٤٥٦٧٨٩", "اااايه0123456789")
    ).replace("ـ", "")
    text = re.sub(r"[^\w\s]", " ", text)
    for source, target in ALIASES.items():
        source = source.translate(str.maketrans("أإآٱىة", "اااايه"))
        text = re.sub(r"(?<!\w)" + re.escape(source) + r"(?!\w)", target, text)
    return " ".join(text.split())


def document(prop):
    parts = [
        prop.title,
        prop.description,
        prop.district,
        prop.street,
        prop.city.name,
        prop.governorate.name,
        prop.property_type.name,
    ]
    parts += [word for word, field in AMENITIES.items() if getattr(prop, field, False)]

    def user_text(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"name", "description", "rules", "scope"} and isinstance(
                    item, str
                ):
                    parts.append(item)
                elif isinstance(item, (dict, list)):
                    user_text(item)
        elif isinstance(value, list):
            for item in value:
                user_text(item)

    user_text(prop.rental_inventory or {})
    return normalize(" ".join(str(part or "") for part in parts))
