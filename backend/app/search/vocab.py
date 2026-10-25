"""Words the search understands. Shared by the rule parser and the result filters."""

CATEGORY_SYNONYMS = {
    "tshirt": ["t-shirt", "t-shirts", "t shirt", "t shirts", "tshirt", "tshirts", "tee", "tees", "henley", "henleys"],
    "shirt": ["shirt", "shirts", "button-down", "button down", "button-up"],
    "polo": ["polo", "polos", "polo shirt", "polo shirts", "polo t-shirt"],
    "hoodie": ["hoodie", "hoodies", "hoody", "sweatshirt", "sweatshirts"],
    "jacket": ["jacket", "jackets", "blazer", "blazers", "bomber", "bombers", "coat", "coats"],
    "kurta": ["kurta", "kurtas", "kurti", "kurtis"],
    "top": ["top", "tops", "blouse", "blouses", "tank top", "tank", "tanks", "cami"],
    "jeans": ["jeans", "jean", "denims"],
    "trousers": ["trousers", "trouser", "pants", "pant", "chinos", "chino", "slacks", "formals"],
    "joggers": ["joggers", "jogger", "trackpants", "track pants", "trackpant", "sweatpants", "lowers"],
    "shorts": ["shorts", "bermudas"],
    "dress": ["dress", "dresses", "gown", "gowns", "maxi dress", "midi dress"],
}

GENDER_WORDS = {
    "men": ["men", "mens", "men's", "man", "male", "guy", "guys", "boys", "gents", "him", "husband", "dad"],
    "women": ["women", "womens", "women's", "woman", "female", "ladies", "lady", "girls", "her", "wife", "mom"],
    "unisex": ["unisex"],
}

# Query word -> product colours it should match.
COLOR_GROUPS = {
    "black": ["black", "charcoal"],
    "white": ["white", "cream"],
    "off white": ["cream", "white", "beige"],
    "cream": ["cream", "beige"],
    "beige": ["beige", "cream"],
    "grey": ["grey", "charcoal"],
    "gray": ["grey", "charcoal"],
    "charcoal": ["charcoal"],
    "blue": ["navy", "indigo", "sky blue", "light blue", "teal"],
    "navy": ["navy"],
    "navy blue": ["navy"],
    "dark blue": ["navy", "indigo"],
    "light blue": ["light blue", "sky blue"],
    "sky blue": ["sky blue", "light blue"],
    "indigo": ["indigo"],
    "teal": ["teal"],
    "green": ["olive", "sage", "teal"],
    "olive": ["olive"],
    "sage": ["sage"],
    "red": ["maroon", "rust"],
    "maroon": ["maroon"],
    "rust": ["rust"],
    "orange": ["rust", "mustard"],
    "brown": ["brown", "rust"],
    "yellow": ["mustard"],
    "mustard": ["mustard"],
    "pink": ["pink"],
    "purple": ["lavender"],
    "lavender": ["lavender"],
}

MATERIALS = [
    "linen", "cotton", "denim", "wool", "fleece", "khadi", "rayon", "silk", "polyester",
    "modal", "viscose", "corduroy", "jersey", "terry", "flannel",
]

FIT_WORDS = {
    "relaxed": ["loose", "relaxed", "oversized", "baggy", "roomy", "comfort fit", "comfortable fit", "boxy"],
    "snug": ["slim", "slim fit", "fitted", "snug", "skinny", "tight", "body fit"],
    "regular": ["regular fit", "classic fit", "normal fit"],
}

TAG_WORDS = {
    "tall": ["tall", "long length", "extra long"],
    "petite": ["petite", "short height"],
    "plus-size": ["plus size", "plus-size", "big size", "big sizes", "extended size", "extended sizes", "large size"],
    "big-and-tall": ["big and tall", "big & tall"],
}

STOPWORDS = {
    "a", "an", "the", "for", "with", "and", "or", "in", "of", "on", "to", "me", "my", "i", "im", "i'm", "need",
    "want", "looking", "find", "show", "some", "something", "any", "size", "sizes", "fit", "fits", "fitting",
    "that", "which", "who", "has", "have", "is", "are", "be", "please", "good", "nice", "best", "buy", "get",
    "like", "can", "you", "around", "about", "budget", "rs", "inr", "price", "cost", "cheap", "affordable", "under",
    "below", "above", "over", "between", "upto", "up", "max", "min", "less", "more", "than", "within", "cm",
    "inch", "inches", "ft", "feet", "tall", "height", "body", "chest", "waist", "hips", "hip", "bust", "inseam",
    "shoulder", "shoulders", "wear", "wearing", "clothes", "clothing", "outfit", "options", "option", "new",
    "x", "by", "from", "at", "it", "its", "this", "these", "those", "big", "large", "small", "extra", "plus",
    "very", "really", "am", "m", "needs", "needed", "wants", "wanted", "searching", "suggest", "recommend",
    "should", "would", "will", "dont", "not", "also", "only", "just", "someone", "person", "people",
}

# Inch values below these are read as inches when the query gives no unit.
INCH_THRESHOLD = {"chest": 70, "waist": 66, "hips": 72, "shoulder": 30, "inseam": 50}
