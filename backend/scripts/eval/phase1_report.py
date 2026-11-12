"""Gộp bản ghi JSONL của run_phase1 thành bảng Markdown (thuần, không I/O) — dán vào docs/eval/phase1.md."""

import statistics
from collections.abc import Iterable
from typing import Any

from scripts.eval.phase1_checks import ALLERGEN_SLUGS, TOP_K, percent

DIETS = ("omnivore", "vegetarian", "vegan")
Record = dict[str, Any]


def leaked_hits(record: Record) -> list[Record]:
    """Món của 1 ca dính dị ứng (theo nhãn món hoặc nguyên liệu)."""
    return [hit for hit in record["hits"] if hit["allergen_leaks"]]


def allergen_table(records: list[Record]) -> list[str]:
    """Theo từng loại dị ứng: số ca, số ca có nguyên liệu gây dị ứng, số món, món lọt, nghi vấn tên gốc."""
    lines = [
        "| Dị ứng | Ca | Ca có nguyên liệu gây dị ứng | Món trả về | Món lọt | Nghi vấn tên gốc |",
        "|---|---|---|---|---|---|",
    ]
    for slug in ALLERGEN_SLUGS:
        cases = [record for record in records if slug in record["allergens"]]
        with_trigger = sum(slug in record["user_ingredient_allergens"] for record in cases)
        hits = [hit for record in cases for hit in record["hits"]]
        leaks = sum(any(reason.endswith(f": {slug}") for reason in hit["allergen_leaks"]) for hit in hits)
        warnings = sum(any(warning.endswith(f": {slug}") for warning in hit["raw_warnings"]) for hit in hits)
        lines.append(f"| {slug} | {len(cases)} | {with_trigger} | {len(hits)} | {leaks} | {warnings} |")
    return lines


def leak_details(records: list[Record]) -> list[str]:
    """Từng món lọt kèm lý do; không có thì 1 dòng xác nhận 0."""
    lines = [
        f"- **{record['case_id']}** ({', '.join(record['allergens'])}): #{hit['recipe_id']} {hit['title']} — "
        + "; ".join(hit["allergen_leaks"])
        for record in records for hit in leaked_hits(record)
    ]
    return lines or ["Không có món nào lọt (0)."]


def raw_warning_details(records: list[Record]) -> list[str]:
    """Món có tên gốc chưa map khớp từ khoá dị ứng của user (nghi vấn, cần người xem)."""
    lines = [
        f"- {record['case_id']}: #{hit['recipe_id']} {hit['title']} — " + "; ".join(hit["raw_warnings"])
        for record in records for hit in record["hits"] if hit["raw_warnings"]
    ]
    return lines or ["Không có."]


def diet_table(records: list[Record]) -> list[str]:
    """Theo chế độ ăn: số ca, số món, món sai chế độ (nhãn hoặc nguyên liệu)."""
    lines = ["| Chế độ ăn | Ca | Món trả về | Món sai chế độ |", "|---|---|---|---|"]
    for diet in DIETS:
        hits = [hit for record in records if record["diet"] == diet for hit in record["hits"]]
        wrong = sum(bool(hit["diet_violations"]) for hit in hits)
        lines.append(f"| {diet} | {sum(record['diet'] == diet for record in records)} | {len(hits)} | {wrong} |")
    return lines


def diet_details(records: list[Record]) -> list[str]:
    """Từng món sai chế độ kèm lý do."""
    lines = [
        f"- **{record['case_id']}** ({record['diet']}): #{hit['recipe_id']} {hit['title']} — "
        + "; ".join(hit["diet_violations"])
        for record in records for hit in record["hits"] if hit["diet_violations"]
    ]
    return lines or ["Không có món nào sai chế độ ăn (0)."]


def short_result_table(records: list[Record]) -> list[str]:
    """Ca trả ít hơn TOP_K món, kèm nguyên liệu đã khớp và tên chưa khớp."""
    lines = ["| Ca | Món | Chế độ / dị ứng | Nguyên liệu đã khớp | Không chắc / chưa khớp |", "|---|---|---|---|---|"]
    for record in records:
        if len(record["hits"]) >= TOP_K:
            continue
        constraint = " + ".join([record["diet"], *record["allergens"]])
        unsure = ", ".join(record["uncertain"] + record["unmatched"]) or "—"
        lines.append(
            f"| {record['case_id']} | {len(record['hits'])} | {constraint} | "
            f"{', '.join(record['accepted_names']) or '—'} | {unsure} |"
        )
    return lines


def mean_of(values: Iterable[float | None]) -> str:
    """Trung bình bỏ None, 2 chữ số; không có giá trị thì '—'."""
    present = [value for value in values if value is not None]
    return f"{statistics.mean(present):.2f}" if present else "—"


def coverage_lines(records: list[Record]) -> list[str]:
    """Trung bình số món, độ phủ phía món và phần nguyên liệu của user được dùng."""
    hits = [hit for record in records for hit in record["hits"]]
    searched = [record for record in records if record["searched"]]
    return [
        f"- Ca được tìm (có ít nhất 1 nguyên liệu khớp): {percent(len(searched), len(records))}",
        f"- Món trung bình mỗi ca được tìm: {mean_of(len(record['hits']) for record in searched)}",
        f"- Độ phủ phía món (như SQL, trung bình trên {len(hits)} món): {mean_of(hit['coverage'] for hit in hits)}",
        f"- Phần nguyên liệu của user được món dùng (trung bình): {mean_of(hit['user_usage'] for hit in hits)}",
    ]


def timing_table(records: list[Record]) -> list[str]:
    """Trung vị / p95 / max thời gian nhúng và tìm (ms)."""
    lines = ["| Giai đoạn | n | Trung vị (ms) | p95 (ms) | Max (ms) |", "|---|---|---|---|---|"]
    for label, key in (("Nhúng (bge-m3)", "embed_ms"), ("search_recipes (RPC)", "search_ms")):
        values = sorted(record[key] for record in records if record["searched"])
        if not values:
            continue
        p95 = values[min(len(values) - 1, round(0.95 * (len(values) - 1)))]
        lines.append(f"| {label} | {len(values)} | {statistics.median(values):.0f} | {p95:.0f} | {values[-1]:.0f} |")
    return lines


def render_summary(records: list[Record]) -> str:
    """Toàn bộ phần số liệu của báo cáo."""
    sections = [
        ("Dị ứng theo loại", allergen_table(records)),
        ("Món lọt dị ứng", leak_details(records)),
        ("Nghi vấn theo tên gốc chưa map", raw_warning_details(records)),
        ("Chế độ ăn", diet_table(records) + [""] + diet_details(records)),
        (f"Ca trả ít hơn {TOP_K} món", short_result_table(records)),
        ("Số món và độ phủ", coverage_lines(records)),
        ("Thời gian phía backend", timing_table(records)),
    ]
    return "\n\n".join(f"### {title}\n\n" + "\n".join(lines) for title, lines in sections) + "\n"
