"""Test chuẩn hoá công thức để seed: gia vị cơ bản, % match, diet, lọc kcal bất thường."""

import pytest

from app.services.ingredient_matching import CatalogIngredient
from app.services.ingredient_normalizer import IngredientNormalizer
from app.services.nutrition import Nutrition
from scripts.recipe_preparation import (
    REJECT_KCAL_OUTLIER,
    REJECT_LOW_MATCH,
    Catalog,
    DietFlags,
    PreparedRecipe,
    classify_diet,
    is_diet_neutral_basic,
    is_pantry_basic,
    map_ingredients,
    prepare_recipe,
)
from scripts.ingredient_senses import guess_allergen_ids, is_non_dairy_lookalike

TOFU_ID, PORK_ID, EGG_ID, OIL_ID = 1, 2, 3, 4
MILK_ID = 5
EGG_ALLERGEN_ID, SHELLFISH_ALLERGEN_ID, DAIRY_ALLERGEN_ID, SOY_ALLERGEN_ID = 7, 8, 9, 10
ALLERGEN_SLUGS = {
    "egg": EGG_ALLERGEN_ID, "shellfish": SHELLFISH_ALLERGEN_ID, "dairy": DAIRY_ALLERGEN_ID, "soy": SOY_ALLERGEN_ID,
    "fish": 11, "wheat": 12, "peanut": 13, "tree_nuts": 14, "sesame": 15, "molluscs": 16,
}
DIET_FLAGS = {
    TOFU_ID: DietFlags(is_vegetarian=True, is_vegan=True),
    PORK_ID: DietFlags(is_vegetarian=False, is_vegan=False),
    EGG_ID: DietFlags(is_vegetarian=True, is_vegan=False),
    OIL_ID: DietFlags(is_vegetarian=True, is_vegan=True),
}
CATALOG = Catalog(
    normalizer=IngredientNormalizer([
        CatalogIngredient(id=TOFU_ID, name_vi="Đậu phụ", name_en="Tofu"),
        CatalogIngredient(id=PORK_ID, name_vi="Thịt heo", name_en="Pork"),
        CatalogIngredient(id=EGG_ID, name_vi="Trứng gà", name_en="Egg"),
        CatalogIngredient(id=OIL_ID, name_vi="Dầu ăn", name_en="Oil"),
    ]),
    diet_flags=DIET_FLAGS,
    facts={TOFU_ID: Nutrition(76, 8, 2, 4.8), OIL_ID: Nutrition(884, 0, 0, 100)},
    allergens_by_ingredient={EGG_ID: {EGG_ALLERGEN_ID}},
    allergen_id_by_slug=ALLERGEN_SLUGS,
)

CATALOG_WITH_MILK = Catalog(
    normalizer=IngredientNormalizer([
        CatalogIngredient(id=TOFU_ID, name_vi="Đậu phụ", name_en="Tofu"),
        CatalogIngredient(id=MILK_ID, name_vi="Sữa tươi", name_en="Whole milk", aliases=("Milk",)),
    ]),
    diet_flags={**DIET_FLAGS, MILK_ID: DietFlags(is_vegetarian=True, is_vegan=False)},
    facts={},
    allergens_by_ingredient={MILK_ID: {DAIRY_ALLERGEN_ID}},
    allergen_id_by_slug=ALLERGEN_SLUGS,
)


def _row(ingredients: list[str], recipe_id: str = "vifoodrec-1") -> dict[str, str]:
    return {
        "id": recipe_id, "name": "Món thử", "description": "", "minutes": "20",
        "ingredients": repr(ingredients), "steps": repr(["Bước 1", "Bước 2"]),
    }


@pytest.mark.parametrize(("name", "expected"), [
    ("nước", True), ("water", True), ("salt & freshly ground black pepper", True), ("tiêu xay", True),
    ("hạt nêm aji ngon heo", True), ("hat nêm", True), ("bột ngọt aji no moto", True),
    ("nước mắm", False), ("bell pepper", False), ("black beans", False), ("ground beef", False),
])
def test_is_pantry_basic(name: str, expected: bool) -> None:
    assert is_pantry_basic(name) is expected


def test_hat_nem_is_basic_but_not_diet_neutral() -> None:
    assert is_diet_neutral_basic("muối")
    assert not is_diet_neutral_basic("hạt nêm")


@pytest.mark.parametrize(("ids", "unmatched", "fuzzy_matched", "expected"), [
    ({TOFU_ID, OIL_ID}, [], [], "vegan"),
    ({TOFU_ID, EGG_ID}, [], [], "vegetarian"),
    ({TOFU_ID, PORK_ID}, [], [], "omnivore"),
    ({TOFU_ID}, ["bacon"], [], "omnivore"),
    ({TOFU_ID}, ["muối"], [], "vegan"),
    ({TOFU_ID}, [], ["bắp bò"], "omnivore"),  # "bắp bò" (thịt) khớp mờ nhầm sang Bắp (ngô)
    ({TOFU_ID}, [], ["lòng đỏ trứng gà"], "vegetarian"),  # có "gà" nhưng là trứng
    ({TOFU_ID}, [], ["unsalted butter"], "vegetarian"),
])
def test_classify_diet(ids: set[int], unmatched: list[str], fuzzy_matched: list[str], expected: str) -> None:
    assert classify_diet(ids, DIET_FLAGS, unmatched, fuzzy_matched) == expected


def test_pantry_basics_do_not_count_against_match_ratio() -> None:
    result = prepare_recipe(_row(["đậu phụ", "nước", "muối", "hạt nêm"]), CATALOG, {})
    assert isinstance(result, PreparedRecipe)
    # hạt nêm không map được → không dám gắn vegan
    assert result.diet_type == "omnivore"


def test_unmatched_main_ingredient_rejects_recipe() -> None:
    assert prepare_recipe(_row(["đậu phụ", "thịt khủng long"]), CATALOG, {}) == REJECT_LOW_MATCH


def test_kcal_outlier_is_rejected() -> None:
    deep_fry_oil = {"vifoodrec-1": (1, {"dầu ăn": 1000.0, "đậu phụ": 200.0})}
    assert prepare_recipe(_row(["đậu phụ", "dầu ăn"]), CATALOG, deep_fry_oil) == REJECT_KCAL_OUTLIER


def test_prepared_recipe_carries_allergens_and_nutrition() -> None:
    extras = {"vifoodrec-1": (2, {"đậu phụ": 200.0})}
    result = prepare_recipe(_row(["đậu phụ", "trứng gà"]), CATALOG, extras)
    assert isinstance(result, PreparedRecipe)
    assert result.allergen_ids == {EGG_ALLERGEN_ID}
    assert result.is_verified and result.source_url is None
    assert result.nutrition == Nutrition(kcal=76, protein_g=8, carb_g=2, fat_g=4.8)


def test_unmatched_ingredient_allergens_are_guessed_by_keyword() -> None:
    # 9/10 nguyên liệu chính map được (đủ 90%) — "tôm khô" không có trong catalog nhưng vẫn phải gắn shellfish
    result = prepare_recipe(_row(["đậu phụ"] * 9 + ["tôm khô"]), CATALOG, {})
    assert isinstance(result, PreparedRecipe)
    assert result.allergen_ids == {SHELLFISH_ALLERGEN_ID}
    assert result.raw_ingredient_names == ["tôm khô"]


def test_keyword_guess_ignores_look_alike_words() -> None:
    slugs = {"egg": 1, "shellfish": 2, "fish": 3, "sesame": 4}
    assert guess_allergen_ids(["tôm khô"], slugs) == {2}
    assert guess_allergen_ids(["cà tím", "me chua", "eggplant"], slugs) == set()


@pytest.mark.parametrize("name", [
    "sữa dừa", "sữa dừa organic ecomil", "sữa đậu nành không đường", "sữa hạt", "sữa yến mạch", "sữa gạo",
    "sữa chua đậu nành", "unsweetened almond milk", "light coconut milk",
])
def test_plant_milk_is_not_dairy(name: str) -> None:
    assert is_non_dairy_lookalike(name)
    assert DAIRY_ALLERGEN_ID not in guess_allergen_ids([name], ALLERGEN_SLUGS)


def test_plant_milk_keeps_its_own_allergen_and_real_milk_stays_dairy() -> None:
    assert guess_allergen_ids(["sữa đậu nành"], ALLERGEN_SLUGS) == {SOY_ALLERGEN_ID}
    assert guess_allergen_ids(["sữa tươi không đường"], ALLERGEN_SLUGS) == {DAIRY_ALLERGEN_ID}
    assert guess_allergen_ids(["sữa chua"], ALLERGEN_SLUGS) == {DAIRY_ALLERGEN_ID}


def test_plant_milk_is_not_fuzzy_mapped_to_cow_milk() -> None:
    # "almond milk" chứa alias "Milk" của Sữa tươi → khớp mờ 100 điểm; phải bị chặn, không mang dairy/nhãn sữa bò
    result = prepare_recipe(_row(["đậu phụ"] * 9 + ["almond milk"]), CATALOG_WITH_MILK, {})
    assert isinstance(result, PreparedRecipe)
    assert MILK_ID not in result.grams_by_ingredient
    assert result.diet_type == "vegan"
    assert result.allergen_ids == {ALLERGEN_SLUGS["tree_nuts"]}


def test_cow_milk_still_maps_and_is_dairy() -> None:
    result = prepare_recipe(_row(["đậu phụ", "milk"]), CATALOG_WITH_MILK, {})
    assert isinstance(result, PreparedRecipe)
    assert result.allergen_ids == {DAIRY_ALLERGEN_ID}
    assert result.diet_type == "vegetarian"


# --- "meat" / "orange roughy" khớp mờ sang nguyên liệu chay (docs/eval/mapping-errors.md) --------------------------
# Tên, name_en, alias lấy đúng như danh mục thật (dump 2026-11-13).
_REAL_ROWS = [  # (id, name_vi, name_en, aliases, is_vegetarian, is_vegan)
    (16, "Tỏi", "Garlic", (), True, True),
    (58, "Cam", "Orange", (), True, True),
    (59, "Chanh vàng", "Lemon", (), True, True),
    (60, "Chanh", "Lime", (), True, True),
    (66, "Cơm dừa", "Coconut meat", (), True, True),
    (101, "Trứng gà", "Chicken egg", ("Trứng", "Egg"), True, False),
    (123, "Bơ", "Butter", (), True, False),
    (124, "Phô mai cheddar", "Cheddar", ("Phô mai", "Cheese"), True, False),
    (132, "Bột mì", "Wheat flour",
     ("Flour", "All-purpose flour", "Bột mì đa dụng", "Bột chiên giòn", "Bột giòn"), True, True),
    (149, "Dầu ô liu", "Olive oil", ("Dầu olive", "Extra virgin olive oil"), True, True),
    (152, "Đường", "Sugar", (), True, True),
    (155, "Muối", "Salt", (), True, True),
    (194, "Thịt xông khói", "Bacon", ("Ba rọi xông khói", "Ba chỉ xông khói"), False, False),
]
REAL_CATALOG = Catalog(
    normalizer=IngredientNormalizer(
        CatalogIngredient(id=row[0], name_vi=row[1], name_en=row[2], aliases=row[3]) for row in _REAL_ROWS
    ),
    diet_flags={row[0]: DietFlags(is_vegetarian=row[4], is_vegan=row[5]) for row in _REAL_ROWS},
    facts={},
    allergens_by_ingredient={},
    allergen_id_by_slug=ALLERGEN_SLUGS,
)
_NAME_VI_BY_ID = {row[0]: row[1] for row in _REAL_ROWS}


def _mapped_names(source_names: list[str], title: str = "Món thử") -> set[str]:
    mapping = map_ingredients(source_names, title, {}, REAL_CATALOG)
    return {_NAME_VI_BY_ID[ingredient_id] for ingredient_id in mapping.grams_by_ingredient}


@pytest.mark.parametrize("name", ["meat", "ground meat", "minced meat", "lean ground meat", "stew meat"])
def test_meat_is_not_mapped_to_a_vegetarian_ingredient(name: str) -> None:
    mapping = map_ingredients([name], "scandinavian hash  biksemad", {}, REAL_CATALOG)
    assert mapping.grams_by_ingredient == {} and mapping.unmatched == [name]
    assert classify_diet(set(), REAL_CATALOG.diet_flags, mapping.unmatched, mapping.fuzzy_matched) == "omnivore"


@pytest.mark.parametrize("name", ["coconut meat", "Coconut meat", "young coconut meat", "cơm dừa"])
def test_coconut_meat_still_maps_to_com_dua(name: str) -> None:
    assert _mapped_names([name]) == {"Cơm dừa"}


@pytest.mark.parametrize("name", ["orange roughy", "orange roughy fillets"])
def test_orange_roughy_is_not_mapped_to_orange(name: str) -> None:
    assert _mapped_names([name], "easy baked orange roughy") == set()


@pytest.mark.parametrize(("name", "expected"), [
    ("salt", "Muối"), ("butter", "Bơ"), ("sugar", "Đường"), ("eggs", "Trứng gà"), ("garlic cloves", "Tỏi"),
    ("all-purpose flour", "Bột mì"), ("lemon juice", "Chanh vàng"), ("cheddar cheese", "Phô mai cheddar"),
    ("extra virgin olive oil", "Dầu ô liu"), ("bacon", "Thịt xông khói"), ("orange juice", "Cam"),
])
def test_common_source_names_keep_their_match(name: str, expected: str) -> None:
    assert _mapped_names([name]) == {expected}
