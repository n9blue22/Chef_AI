"""Đánh giá giai đoạn 1: chạy cases.json qua normalizer → bge-m3 → search_recipes (RPC thật), kiểm chéo dị ứng /
chế độ ăn bằng dữ liệu đọc thẳng từ bảng, đo thời gian, đo độ ổn định khi đảo thứ tự nguyên liệu.

Chỉ đọc DB. Không gọi Groq/Gemini/Cloudflare, không gọi /recipes/suggest. Cấu hình nạp qua app (app.core.config).
Kết quả: scripts/eval/out/phase1-<giờ>.jsonl, order-<giờ>.jsonl, summary-<giờ>.md (thư mục out/ bị gitignore).
Chạy (cwd = backend): venv\\Scripts\\python.exe -m scripts.eval.run_phase1
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, os.getcwd())
from supabase import AsyncClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.supabase_client import create_admin_client  # noqa: E402
from app.services.embedding.bge_m3 import BgeM3Provider  # noqa: E402
from app.services.ingredient_matching import CatalogIngredient  # noqa: E402
from app.services.ingredient_normalizer import (  # noqa: E402
    IngredientNormalizer,
    MatchStatus,
    accepted_ingredient_ids,
    load_ingredient_catalog,
)
from app.services.pantry_basics import pantry_basic_ids  # noqa: E402
from app.services.pipeline import build_query_text  # noqa: E402
from app.services.recipe_repository import SearchHit, search_recipes  # noqa: E402
from scripts.eval.phase1_checks import (  # noqa: E402
    RecipeFacts,
    allergen_leak_reasons,
    diet_violation_reasons,
    guess_slugs,
    order_agreement,
    raw_name_allergen_warnings,
    recipe_coverage,
    recipe_facts_from_row,
    slugs_of,
    user_usage,
)
from scripts.eval.phase1_report import Record, render_summary  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
CASES_PATH = EVAL_DIR / "cases.json"
OUT_DIR = EVAL_DIR / "out"
ORDER_CASE_COUNT = 20
MIN_ORDER_INGREDIENTS = 4
WARM_UP_TEXT = "Nguyên liệu: Cà chua, Tomato"  # lượt embed đầu nạp model, không tính vào số đo
INGREDIENT_ALLERGEN_COLUMNS = "id,ingredient_allergens(allergens(slug))"
RECIPE_FACT_COLUMNS = (
    "id,title,diet_type,raw_ingredient_names,recipe_allergens(allergens(slug)),"
    "recipe_ingredients(ingredient_id,is_optional,"
    "ingredients(name_vi,is_vegetarian,is_vegan,ingredient_allergens(allergens(slug))))"
)


@dataclass(frozen=True)
class EvalContext:
    """Những thứ dựng 1 lần cho cả lượt chạy."""

    admin: AsyncClient
    catalog: list[CatalogIngredient]
    normalizer: IngredientNormalizer
    embedder: BgeM3Provider
    basic_ids: list[int]
    allergens_by_ingredient: dict[int, frozenset[str]]




async def build_context() -> EvalContext:
    """Client secret key (RPC chỉ service_role gọi được), danh mục, bge-m3 đã nạp sẵn."""
    admin = await create_admin_client(get_settings())
    catalog = await load_ingredient_catalog(admin)
    rows = (await admin.table("ingredients").select(INGREDIENT_ALLERGEN_COLUMNS).execute()).data
    embedder = BgeM3Provider()
    await embedder.embed([WARM_UP_TEXT])
    return EvalContext(
        admin=admin, catalog=catalog, normalizer=IngredientNormalizer(catalog), embedder=embedder,
        basic_ids=pantry_basic_ids(catalog),
        allergens_by_ingredient={row["id"]: slugs_of(row["ingredient_allergens"]) for row in rows},
    )


async def timed_search(
    context: EvalContext, ingredient_ids: list[int], diet: str, allergens: list[str],
) -> tuple[list[SearchHit], float, float]:
    """(món, ms nhúng, ms RPC) — cùng các bước suggest_recipes làm trước khi gọi LLM."""
    started = time.perf_counter()
    [embedding] = await context.embedder.embed([build_query_text(ingredient_ids, context.catalog)])
    embedded = time.perf_counter()
    hits = await search_recipes(context.admin, embedding, diet, allergens, ingredient_ids, context.basic_ids)
    finished = time.perf_counter()
    return hits, (embedded - started) * 1000, (finished - embedded) * 1000



async def load_recipe_facts(admin: AsyncClient, recipe_ids: list[int]) -> dict[int, RecipeFacts]:
    """Đọc lại món từ bảng (không qua RPC) để kiểm chéo bộ lọc SQL."""
    if not recipe_ids:
        return {}
    rows = (await admin.table("recipes").select(RECIPE_FACT_COLUMNS).in_("id", recipe_ids).execute()).data
    return {row["id"]: recipe_facts_from_row(row) for row in rows}


def hit_record(
    hit: SearchHit, facts: RecipeFacts, case: dict[str, Any], basic_ids: set[int], user_ids: set[int],
) -> Record:
    """1 món trả về + kết quả mọi phép kiểm."""
    user_allergens = frozenset(case["allergens"])
    return {
        "recipe_id": hit.recipe_id, "title": hit.title, "score": round(hit.score, 4), "diet_type": facts.diet_type,
        "coverage": recipe_coverage(facts, user_ids, basic_ids), "user_usage": user_usage(facts, user_ids, basic_ids),
        "allergen_leaks": allergen_leak_reasons(facts, user_allergens),
        "raw_warnings": raw_name_allergen_warnings(facts, user_allergens, guess_slugs),
        "diet_violations": diet_violation_reasons(facts, case["diet"]),
    }


def match_names(case: dict[str, Any], context: EvalContext) -> tuple[list[int], list[str], list[str]]:
    """(id tự nhận, tên không chắc, tên không khớp) — như luồng quét: chỉ id tự nhận được gửi đi tìm."""
    matches = context.normalizer.normalize(case["names"])
    uncertain = [match.raw_name for match in matches if match.status is MatchStatus.UNCERTAIN]
    unmatched = [match.raw_name for match in matches if match.status is MatchStatus.REJECTED]
    return accepted_ingredient_ids(matches), uncertain, unmatched


async def evaluate_case(case: dict[str, Any], context: EvalContext) -> Record:
    """1 ca → bản ghi JSONL (chưa tìm được thì hits rỗng, searched = False)."""
    accepted_ids, uncertain, unmatched = match_names(case, context)
    name_by_id = {ingredient.id: ingredient.name_vi for ingredient in context.catalog}
    record: Record = {
        "case_id": case["id"], "diet": case["diet"], "allergens": case["allergens"], "tags": case["tags"],
        "names": case["names"], "accepted_ids": accepted_ids,
        "accepted_names": [name_by_id[ingredient_id] for ingredient_id in accepted_ids],
        "uncertain": uncertain, "unmatched": unmatched,
        "user_ingredient_allergens": sorted(set().union(
            *(context.allergens_by_ingredient.get(ingredient_id, frozenset()) for ingredient_id in accepted_ids),
        )),
        "searched": bool(accepted_ids), "embed_ms": None, "search_ms": None, "hits": [],
    }
    if not accepted_ids:
        return record
    hits, embed_ms, search_ms = await timed_search(context, accepted_ids, case["diet"], case["allergens"])
    facts = await load_recipe_facts(context.admin, [hit.recipe_id for hit in hits])
    basic_ids, user_ids = set(context.basic_ids), set(accepted_ids)
    record.update(
        embed_ms=round(embed_ms, 1), search_ms=round(search_ms, 1),
        hits=[hit_record(hit, facts[hit.recipe_id], case, basic_ids, user_ids) for hit in hits],
    )
    return record


async def evaluate_order(record: Record, context: EvalContext) -> Record:
    """Tìm lại với nguyên liệu đảo thứ tự; so top-K theo id và theo vị trí."""
    reversed_ids = list(reversed(record["accepted_ids"]))
    hits, _, _ = await timed_search(context, reversed_ids, record["diet"], record["allergens"])
    original = [hit["recipe_id"] for hit in record["hits"]]
    reordered = [hit.recipe_id for hit in hits]
    same_ids, same_ranks = order_agreement(original, reordered)
    return {
        "case_id": record["case_id"], "ingredient_count": len(reversed_ids), "original": original,
        "reversed": reordered, "same_ids": same_ids, "same_ranks": same_ranks,
    }


def write_jsonl(path: Path, records: list[Record]) -> None:
    """Mỗi bản ghi 1 dòng, giữ tiếng Việt."""
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


async def main() -> None:
    """Chạy hết 40 ca, rồi 20 ca đầu có ≥ 4 nguyên liệu đã khớp cho phép đo thứ tự; ghi out/ và in tóm tắt."""
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    context = await build_context()
    records = [await evaluate_case(case, context) for case in cases]
    order_candidates = [r for r in records if len(r["accepted_ids"]) >= MIN_ORDER_INGREDIENTS][:ORDER_CASE_COUNT]
    order_records = [await evaluate_order(record, context) for record in order_candidates]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    OUT_DIR.mkdir(exist_ok=True)
    write_jsonl(OUT_DIR / f"phase1-{stamp}.jsonl", records)
    write_jsonl(OUT_DIR / f"order-{stamp}.jsonl", order_records)
    summary = render_summary(records, order_records)
    (OUT_DIR / f"summary-{stamp}.md").write_text(summary, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định cp1252 → print tiếng Việt lỗi UnicodeEncodeError
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
