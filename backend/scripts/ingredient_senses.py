"""Nghĩa của tên nguyên liệu theo từ khoá: thịt/cá, sản phẩm động vật, dị ứng, và các từ tiếng Việt đa nghĩa.

Là lưới an toàn cho lớp validation 2 khi fuzzy match không đáng tin: thà gắn thừa dị ứng / bỏ nhãn chay
còn hơn để lọt món có tôm cho người dị ứng tôm, hay món có cá cho người ăn chay.
Các cụm đa nghĩa dưới đây đều lấy từ dữ liệu thật (foodcom_filtered.csv, vifoodrec_processed.csv).
"""

import re

from app.services.ingredient_matching import normalize_exact

ALLERGEN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "egg": ("trứng", "egg", "mayonnaise", "mayo"),
    "dairy": (
        "sữa", "bơ", "phô mai", "kem", "milk", "cheese", "butter", "cream", "yogurt", "buttermilk",
        "nutella",
    ),
    "wheat": (
        "bột mì", "bánh mì", "mì", "bột chiên", "bột bánh bao", "flour", "bread", "breadcrumb", "pasta", "noodle",
        "tortilla", "macaroni", "spaghetti", "penne", "crouton", "cracker",
    ),
    "soy": ("đậu nành", "đậu hũ", "đậu phụ", "tàu hũ", "tương", "chao", "soy", "tofu", "miso", "nutella"),
    "peanut": ("đậu phộng", "lạc", "peanut"),
    "tree_nuts": (
        "hạt điều", "óc chó", "hạnh nhân", "almond", "walnut", "pecan", "cashew", "hazelnut", "pistachio",
        "nut", "nutella",  # "nut" khớp cả "nuts" (pattern cho phép -s); không khớp peanut/coconut/nutmeg
    ),
    "sesame": ("mè", "vừng", "sesame", "tahini", "hummus"),
    "fish": ("cá", "mắm", "fish", "anchovy", "anchovies", "salmon", "tuna"),
    "shellfish": (
        "tôm", "cua", "ghẹ", "tép", "shrimp", "prawn", "crab", "lobster",
        "mắm ruốc", "ruốc biển",  # không dùng "ruốc" trơn: miền Bắc "ruốc" = chà bông thịt
    ),
    "molluscs": ("mực", "nghêu", "sò", "hàu", "ốc", "hến", "dầu hào", "squid", "clam", "oyster", "mussel", "scallop"),
}
DAIRY_SLUG = "dairy"
MEAT_KEYWORDS = (
    "thịt", "bò", "heo", "lợn", "gà", "vịt", "ngan", "dê", "cừu", "cá", "tôm", "tép", "mực", "cua", "ghẹ", "nghêu",
    "sò", "hàu", "ốc", "hến", "mắm", "xương", "sườn", "giò", "chả", "lạp xưởng", "pate", "huyết", "lòng",
    "beef", "pork", "chicken", "turkey", "duck", "lamb", "bacon", "ham", "sausage", "fish", "salmon", "tuna",
    "shrimp", "prawn", "crab", "anchovy", "anchovies", "gelatin", "lard",
    # "meat" khớp mờ sang Cơm dừa (name_en "Coconut meat"); "orange roughy" sang Cam. Xem docs/eval/mapping-errors.md.
    "meat", "ground meat", "minced meat", "roughy", "haddock", "sea bass",
)
ANIMAL_DERIVED_KEYWORDS = (
    "trứng", "sữa", "bơ", "phô mai", "kem", "mật ong", "egg", "milk", "cheese", "butter", "cream", "honey", "yogurt",
)

# --- Từ đa nghĩa -------------------------------------------------------------------------------------------
# "lòng đỏ trứng", "trứng gà": có chữ lòng/gà/vịt nhưng là trứng, không phải thịt/lòng (nội tạng).
_EGG_PHRASE = re.compile(r"\b(?:lòng (?:đỏ|trắng) )?trứng(?: (?:gà|vịt|cút|muối))?\b")
# "coconut meat" là cơm dừa, không phải thịt — phải vẫn khớp được Cơm dừa.
_NON_MEAT_LOOKALIKE = re.compile(r"\bcoconut meat\b")
# "tỏi tép", "tép cam": tép = tép tỏi / múi cam, không phải con tép.
_SEGMENT_TEP = re.compile(r"\btỏi tép\b|\btép (?:tỏi|cam|bưởi|chanh|quýt)\b")
# Không phải sữa bò: sữa/kem thực vật, bơ hạt (peanut butter), quả bơ (avocado).
_NON_DAIRY_LOOKALIKE = re.compile(
    r"\b(?:sữa chua đậu nành|sữa (?:dừa|đậu nành|hạt|hạnh nhân|óc chó|điều|yến mạch|gạo)"
    r"|(?:coconut|soy|soya|almond|cashew|oat|rice) (?:milk|cream|yogurt)"
    r"|bơ (?:đậu phộng|lạc|hạnh nhân|điều|hạt|mè|sáp|chín)|(?:trái|quả) bơ"
    r"|(?:peanut|almond|cashew|cocoa|apple|sunflower|nut) butter)\b"
)
# "bơ" đứng riêng là butter, trừ khi tên món cho thấy là quả bơ (sinh tố, chè, kem... bơ; món trái cây).
AMBIGUOUS_BO = "bơ"
AVOCADO_NAME = "quả bơ"
_AVOCADO_DISH = re.compile(r"\b(?:sinh tố|chè|kem|cheesecake|quả|trái) bơ\b|\bbơ viên\b|\btrái cây\b")
# "spaghetti squash" là bí, không phải mì.
_NON_WHEAT_LOOKALIKE = re.compile(r"\bspaghetti squash\b")
# Theo từng slug: cụm "trông giống mà không phải", bỏ đi trước khi dò.
# Chỉ bỏ khi dò đúng slug đó — "sữa đậu nành" vẫn phải ra soy, "bơ đậu phộng" ra peanut.
_LOOKALIKE_BY_SLUG = {DAIRY_SLUG: _NON_DAIRY_LOOKALIKE, "wheat": _NON_WHEAT_LOOKALIKE}
# "nuts", "mixed nuts", "chopped nuts": không rõ loại hạt, có thể là đậu phộng → gắn thêm peanut (tree_nuts đã khớp "nut").
# Tên có loại hạt cụ thể ("pine nuts", "macadamia nuts"...) thì không.
PEANUT_SLUG = "peanut"
_GENERIC_NUTS = re.compile(
    r"(?<!pine )(?<!macadamia )(?<!brazil )(?<!cashew )(?<!pistachio )(?<!pecan )(?<!almond )(?<!betel )\bnuts?\b"
)
# "dầu hào chay", "vegetarian worcestershire sauce": bản chay của sản phẩm động vật.
_VEGETARIAN_VERSION = re.compile(r"\b(?:chay|vegetarian|vegan)\b")


def _keyword_pattern(keywords: tuple[str, ...]) -> re.Pattern[str]:
    """Khớp nguyên từ/cụm từ (cho phép số nhiều tiếng Anh "-s")."""
    return re.compile(rf"\b(?:{'|'.join(map(re.escape, keywords))})s?\b")


_ALLERGEN_PATTERNS = {slug: _keyword_pattern(keywords) for slug, keywords in ALLERGEN_KEYWORDS.items()}
_MEAT_PATTERN = _keyword_pattern(MEAT_KEYWORDS)
_ANIMAL_DERIVED_PATTERN = _keyword_pattern(ANIMAL_DERIVED_KEYWORDS)


def _without_segment_tep(name: str) -> str:
    return _SEGMENT_TEP.sub(" ", normalize_exact(name))


def is_non_dairy_lookalike(name: str) -> bool:
    """Sữa dừa, sữa đậu nành, almond milk, bơ đậu phộng, quả bơ... — nghe như sữa/bơ nhưng không phải sữa bò."""
    return bool(_NON_DAIRY_LOOKALIKE.search(normalize_exact(name)))


def is_vegetarian_version(name: str) -> bool:
    """Tên có chữ "chay" ("dầu hào chay") — không được map về bản động vật."""
    return bool(_VEGETARIAN_VERSION.search(normalize_exact(name)))


def mentions_meat(name: str) -> bool:
    """Tên nhắc tới thịt/cá/hải sản (đã loại "trứng gà", "tỏi tép", "coconut meat"...)."""
    without_lookalikes = _NON_MEAT_LOOKALIKE.sub(" ", _EGG_PHRASE.sub(" ", _without_segment_tep(name)))
    return bool(_MEAT_PATTERN.search(without_lookalikes))


def mentions_animal_derived(name: str) -> bool:
    """Tên nhắc tới trứng/sữa/bơ/mật ong (đã loại sữa thực vật, bơ hạt, quả bơ)."""
    return bool(_ANIMAL_DERIVED_PATTERN.search(_NON_DAIRY_LOOKALIKE.sub(" ", normalize_exact(name))))


def resolve_ambiguous_name(name: str, dish_title: str) -> str:
    """ "bơ" trong "Sinh Tố Bơ" → "quả bơ"; các trường hợp khác giữ nguyên."""
    if normalize_exact(name) == AMBIGUOUS_BO and _AVOCADO_DISH.search(normalize_exact(dish_title)):
        return AVOCADO_NAME
    return name


def guess_allergen_ids(names: list[str], allergen_id_by_slug: dict[str, int]) -> set[int]:
    """Dị ứng dò theo từ khoá trên tên gốc (dùng cho tên không map được hoặc chỉ khớp mờ)."""
    allergen_ids: set[int] = set()
    for name in names:
        text = _without_segment_tep(name)
        for slug, pattern in _ALLERGEN_PATTERNS.items():
            lookalike = _LOOKALIKE_BY_SLUG.get(slug)
            searched = lookalike.sub(" ", text) if lookalike else text
            if pattern.search(searched):
                allergen_ids.add(allergen_id_by_slug[slug])
        if _GENERIC_NUTS.search(text):
            allergen_ids.add(allergen_id_by_slug[PEANUT_SLUG])
    return allergen_ids
