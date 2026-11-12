"""Bộ đánh giá giai đoạn 1 (scripts/eval): phép kiểm thuần + bảng tóm tắt, chỉ dữ liệu giả."""

import json
from pathlib import Path

from scripts.eval.phase1_checks import (
    ALLERGEN_SLUGS,
    RecipeFacts,
    RecipeIngredientFacts,
    allergen_leak_reasons,
    diet_violation_reasons,
    guess_slugs,
    order_agreement,
    raw_name_allergen_warnings,
    recipe_coverage,
    recipe_facts_from_row,
    user_usage,
)
from scripts.eval.phase1_report import render_summary

CASES_PATH = Path(__file__).resolve().parents[1] / "scripts" / "eval" / "cases.json"
FISH_SAUCE = RecipeIngredientFacts(157, "Nước mắm", False, False, False, frozenset({"fish"}))
TOFU = RecipeIngredientFacts(140, "Đậu phụ", False, True, True, frozenset({"soy"}))
TOMATO = RecipeIngredientFacts(7, "Cà chua", False, True, True, frozenset())
EGG = RecipeIngredientFacts(101, "Trứng gà", True, True, False, frozenset({"egg"}))
BASIC_IDS = {157}


def make_recipe(*ingredients: RecipeIngredientFacts, diet: str = "omnivore", labels: frozenset[str] = frozenset(),
                raw: tuple[str, ...] = ()) -> RecipeFacts:
    return RecipeFacts(1, "Món giả", diet, labels, ingredients, raw)


def test_leak_found_by_ingredient_even_when_recipe_label_missing() -> None:
    recipe = make_recipe(TOMATO, FISH_SAUCE)
    assert allergen_leak_reasons(recipe, frozenset({"fish"})) == ["nguyên liệu Nước mắm: fish"]


def test_leak_found_by_recipe_label_and_clean_recipe_has_none() -> None:
    assert allergen_leak_reasons(make_recipe(TOMATO, labels=frozenset({"soy"})), frozenset({"soy"})) == [
        "nhãn món: soy",
    ]
    assert allergen_leak_reasons(make_recipe(TOMATO, TOFU), frozenset({"fish", "egg"})) == []


def test_raw_name_warning_uses_keywords_only_for_user_allergens() -> None:
    recipe = make_recipe(TOMATO, raw=("cá lóc", "lá lốt"))
    assert raw_name_allergen_warnings(recipe, frozenset({"fish"}), guess_slugs) == ["tên gốc 'cá lóc': fish"]
    assert raw_name_allergen_warnings(recipe, frozenset({"soy"}), guess_slugs) == []


def test_diet_checks_label_and_every_ingredient_including_optional() -> None:
    vegan_label_with_egg = make_recipe(TOMATO, EGG, diet="vegan")
    assert diet_violation_reasons(vegan_label_with_egg, "vegan") == ["nguyên liệu Trứng gà: không thuần chay"]
    assert diet_violation_reasons(vegan_label_with_egg, "vegetarian") == []
    assert diet_violation_reasons(make_recipe(FISH_SAUCE, diet="omnivore"), "vegetarian") == [
        "nhãn món: omnivore", "nguyên liệu Nước mắm: không chay",
    ]
    assert diet_violation_reasons(make_recipe(FISH_SAUCE), "omnivore") == []


def test_coverage_matches_sql_rule_and_user_usage_is_the_other_direction() -> None:
    recipe = make_recipe(TOMATO, TOFU, FISH_SAUCE, EGG)  # bắt buộc (bỏ gia vị + tuỳ chọn): cà chua, đậu phụ
    assert recipe_coverage(recipe, {7, 106}, BASIC_IDS) == 0.5
    assert user_usage(recipe, {7, 106, 157}, BASIC_IDS) == 0.5  # cá thu không được dùng, nước mắm không tính
    assert recipe_coverage(make_recipe(FISH_SAUCE), {7}, BASIC_IDS) is None
    assert user_usage(recipe, {157}, BASIC_IDS) is None


def test_order_agreement_by_id_and_by_rank() -> None:
    assert order_agreement([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == (1.0, 1.0)
    assert order_agreement([1, 2, 3, 4, 5], [2, 1, 3, 4, 5]) == (1.0, 0.6)
    assert order_agreement([1, 2, 3, 4, 5], [1, 2, 3, 9]) == (0.6, 0.6)  # chia cho list dài hơn
    assert order_agreement([], []) == (1.0, 1.0)


def test_recipe_facts_from_postgrest_row() -> None:
    row = {
        "id": 9, "title": "Đậu sốt cà", "diet_type": "vegan", "raw_ingredient_names": None,
        "recipe_allergens": [{"allergens": {"slug": "soy"}}],
        "recipe_ingredients": [{"ingredient_id": 140, "is_optional": False, "ingredients": {
            "name_vi": "Đậu phụ", "is_vegetarian": True, "is_vegan": True,
            "ingredient_allergens": [{"allergens": {"slug": "soy"}}],
        }}],
    }
    assert recipe_facts_from_row(row) == RecipeFacts(9, "Đậu sốt cà", "vegan", frozenset({"soy"}), (TOFU,), ())


def fake_record(case_id: str, hits: list[dict], allergens: list[str], diet: str = "omnivore") -> dict:
    return {
        "case_id": case_id, "diet": diet, "allergens": allergens, "user_ingredient_allergens": allergens,
        "accepted_names": ["Cà chua"], "uncertain": [], "unmatched": ["lá lốt"], "searched": True,
        "embed_ms": 40.0, "search_ms": 120.0, "hits": hits,
    }


def fake_hit(recipe_id: int, leaks: tuple[str, ...] = (), diet_violations: tuple[str, ...] = ()) -> dict:
    return {
        "recipe_id": recipe_id, "title": f"Món {recipe_id}", "coverage": 0.5, "user_usage": 1.0,
        "allergen_leaks": list(leaks), "raw_warnings": [], "diet_violations": list(diet_violations),
    }


def test_summary_prints_every_leak_with_reason_and_short_cases() -> None:
    records = [
        fake_record("c01", [fake_hit(1, ("nguyên liệu Nước mắm: fish",))] + [fake_hit(i) for i in range(2, 6)], ["fish"]),
        fake_record("c02", [fake_hit(7, diet_violations=("nhãn món: omnivore",))], [], diet="vegan"),
    ]
    order = [{"case_id": "c01", "ingredient_count": 4, "original": [1, 2], "reversed": [2, 1],
              "same_ids": 1.0, "same_ranks": 0.0}]
    summary = render_summary(records, order)
    assert "| fish | 1 | 1 | 5 | 1 | 0 |" in summary
    assert "**c01** (fish): #1 Món 1 — nguyên liệu Nước mắm: fish" in summary
    assert "**c02** (vegan): #7 Món 7 — nhãn món: omnivore" in summary
    assert "| c02 | 1 | vegan | Cà chua | lá lốt |" in summary
    assert "cùng thứ hạng (mọi vị trí): 0/1 (0%)" in summary


def test_summary_states_zero_leaks_explicitly() -> None:
    summary = render_summary([fake_record("c01", [fake_hit(1)], ["egg"])], [])
    assert "Không có món nào lọt (0)." in summary


def test_cases_file_meets_phase1_coverage_rules() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert len(cases) == 40 and len({case["id"] for case in cases}) == 40
    assert {case["diet"] for case in cases} == {"omnivore", "vegetarian", "vegan"}
    for slug in ALLERGEN_SLUGS:
        with_trigger = [c for c in cases if slug in c["allergens"] and "allergen-ingredient" in c["tags"]]
        assert len(with_trigger) >= 2, slug
    assert sum(len(case["names"]) >= 4 for case in cases) >= 20
    assert any("few" in case["tags"] for case in cases) and any("unmatched" in case["tags"] for case in cases)
