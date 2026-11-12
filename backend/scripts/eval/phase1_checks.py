"""Phép kiểm thuần (không I/O) cho bộ đánh giá giai đoạn 1: dị ứng lọt, sai chế độ ăn, độ phủ, độ ổn định theo thứ tự.

Dữ liệu món lấy độc lập với RPC search_recipes (đọc thẳng bảng), nên đây là kiểm tra chéo bộ lọc SQL.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from scripts.ingredient_senses import guess_allergen_ids

TOP_K = 5  # = RESULT_LIMIT của search_recipes
ALLERGEN_SLUGS = ("fish", "shellfish", "molluscs", "egg", "dairy", "peanut", "tree_nuts", "soy", "wheat", "sesame")
SLUG_IDENTITY = {slug: slug for slug in ALLERGEN_SLUGS}  # guess_allergen_ids trả "id" → dùng chính slug làm id
ALLOWED_RECIPE_DIETS: dict[str, frozenset[str]] = {
    "vegan": frozenset({"vegan"}),
    "vegetarian": frozenset({"vegetarian", "vegan"}),
    "omnivore": frozenset({"omnivore", "vegetarian", "vegan"}),
}


@dataclass(frozen=True)
class RecipeIngredientFacts:
    """1 dòng recipe_ingredients kèm cờ chay + nhãn dị ứng của nguyên liệu."""

    ingredient_id: int
    name_vi: str
    is_optional: bool
    is_vegetarian: bool
    is_vegan: bool
    allergens: frozenset[str]


@dataclass(frozen=True)
class RecipeFacts:
    """Món trả về, đọc lại từ DB: nhãn món (diet_type, recipe_allergens) và từng nguyên liệu."""

    recipe_id: int
    title: str
    diet_type: str
    label_allergens: frozenset[str]
    ingredients: tuple[RecipeIngredientFacts, ...]
    raw_ingredient_names: tuple[str, ...] = ()


def slugs_of(links: list[dict[str, Any]]) -> frozenset[str]:
    """[{allergens: {slug}}] (embed PostgREST) → tập slug."""
    return frozenset(link["allergens"]["slug"] for link in links)


def recipe_facts_from_row(row: dict[str, Any]) -> RecipeFacts:
    """1 dòng recipes kèm recipe_allergens + recipe_ingredients(ingredients(...)) → RecipeFacts."""
    return RecipeFacts(
        recipe_id=row["id"], title=row["title"], diet_type=row["diet_type"],
        label_allergens=slugs_of(row["recipe_allergens"]),
        ingredients=tuple(
            RecipeIngredientFacts(
                ingredient_id=item["ingredient_id"], name_vi=item["ingredients"]["name_vi"],
                is_optional=item["is_optional"], is_vegetarian=item["ingredients"]["is_vegetarian"],
                is_vegan=item["ingredients"]["is_vegan"], allergens=slugs_of(item["ingredients"]["ingredient_allergens"]),
            )
            for item in row["recipe_ingredients"]
        ),
        raw_ingredient_names=tuple(row["raw_ingredient_names"] or ()),
    )


def guess_slugs(names: list[str]) -> set[str]:
    """Dò dị ứng theo từ khoá trên tên gốc — cùng hàm seed dùng (scripts.ingredient_senses)."""
    return guess_allergen_ids(names, SLUG_IDENTITY)


def allergen_leak_reasons(recipe: RecipeFacts, user_allergens: frozenset[str]) -> list[str]:
    """Lý do món dính dị ứng của user, theo nhãn món VÀ theo nhãn từng nguyên liệu; rỗng = sạch."""
    reasons = [f"nhãn món: {slug}" for slug in sorted(recipe.label_allergens & user_allergens)]
    for item in recipe.ingredients:
        reasons += [f"nguyên liệu {item.name_vi}: {slug}" for slug in sorted(item.allergens & user_allergens)]
    return reasons


def raw_name_allergen_warnings(
    recipe: RecipeFacts, user_allergens: frozenset[str], guess_slugs: Callable[[list[str]], set[str]],
) -> list[str]:
    """Nghi vấn theo tên gốc chưa map (dò từ khoá) — chỉ cảnh báo, không tính là lọt (từ khoá có thể bắt nhầm)."""
    warnings = []
    for name in recipe.raw_ingredient_names:
        warnings += [f"tên gốc '{name}': {slug}" for slug in sorted(guess_slugs([name]) & user_allergens)]
    return warnings


def diet_violation_reasons(recipe: RecipeFacts, user_diet: str) -> list[str]:
    """Lý do món sai chế độ ăn, theo nhãn diet_type VÀ theo cờ chay của từng nguyên liệu (kể cả tuỳ chọn)."""
    reasons = []
    if recipe.diet_type not in ALLOWED_RECIPE_DIETS[user_diet]:
        reasons.append(f"nhãn món: {recipe.diet_type}")
    for item in recipe.ingredients:
        if user_diet == "vegan" and not item.is_vegan:
            reasons.append(f"nguyên liệu {item.name_vi}: không thuần chay")
        elif user_diet == "vegetarian" and not item.is_vegetarian:
            reasons.append(f"nguyên liệu {item.name_vi}: không chay")
    return reasons


def recipe_coverage(recipe: RecipeFacts, user_ids: set[int], pantry_basic_ids: set[int]) -> float | None:
    """Như SQL: phần nguyên liệu bắt buộc của MÓN (bỏ tuỳ chọn + gia vị cơ bản) mà user có; None nếu không có."""
    required = [
        item.ingredient_id for item in recipe.ingredients
        if not item.is_optional and item.ingredient_id not in pantry_basic_ids
    ]
    if not required:
        return None
    return sum(ingredient_id in user_ids for ingredient_id in required) / len(required)


def user_usage(recipe: RecipeFacts, user_ids: set[int], pantry_basic_ids: set[int]) -> float | None:
    """Chiều ngược lại: phần nguyên liệu của USER (bỏ gia vị cơ bản) mà món dùng; None nếu user chỉ có gia vị."""
    own = user_ids - pantry_basic_ids
    if not own:
        return None
    used = {item.ingredient_id for item in recipe.ingredients}
    return len(own & used) / len(own)


def order_agreement(original: list[int], reordered: list[int]) -> tuple[float, float]:
    """(tỉ lệ id trùng, tỉ lệ vị trí trùng) giữa 2 top-K; cả hai rỗng = giống hệt (1.0, 1.0)."""
    size = max(len(original), len(reordered))
    if size == 0:
        return 1.0, 1.0
    same_ids = len(set(original) & set(reordered)) / size
    same_ranks = sum(a == b for a, b in zip(original, reordered)) / size
    return same_ids, same_ranks


def percent(part: int, whole: int) -> str:
    """'3/20 (15%)'; whole = 0 thì '0/0'."""
    return f"{part}/{whole} ({round(100 * part / whole)}%)" if whole else "0/0"
