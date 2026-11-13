-- Đợt sửa 2, theo bản dump chỉ-đọc 2026-11-13 (xem docs/eval/label-fixes-proof.md mục 1 và 3).
-- (a) #1041: thêm nhãn fish (món cho chọn trứng HOẶC cá ngừ; đợt 1 bỏ sót).
-- (b) đổi diet_type vegetarian → omnivore cho món chắc chắn có cá/thịt: #120, #625, #1295 (orange roughy → Cam),
--     #1628 (`meat` → Cơm dừa; thêm sau khi rà docs/eval/diet-audit.md),
--     #1041 (bước 1 nguồn: "flake the tuna"; giữ nhãn fish ở (a)), #1274 (nguồn có `meat`; anh duyệt 2026-11-13).
--     Diet cũ lấy từ dump: cả 6 món đều 'vegetarian' (không món nào 'vegan').
--     Schema: recipes.diet_type là text + CHECK (diet_type in ('omnivore', 'vegetarian', 'vegan'))
--     (supabase/migrations/20260924151448_create_core_schema.sql). Không có giá trị "pescatarian":
--     món có cá/thịt chỉ được là 'omnivore'.
-- Mọi dòng đối chiếu id + tên món (+ diet_type cũ với (b)). Lệch số dòng kỳ vọng là huỷ cả giao dịch.
-- Số dòng kỳ vọng: INSERT recipe_allergens = 1, UPDATE recipes = 6.
-- Chạy lại sau khi đã áp: số dòng = 0 → báo lỗi và huỷ (không đổi gì).
-- Hoàn tác: docs/eval/label-fixes-2-rollback.sql. Kiểm trước/sau: docs/eval/label-fixes-2-verify.sql.
begin;

create temp table diet_fix (recipe_id bigint, title text, old_diet text, new_diet text) on commit drop;
insert into diet_fix (recipe_id, title, old_diet, new_diet) values
  (120, 'baked parmesan fish', 'vegetarian', 'omnivore'),
  (625, 'easy baked orange roughy', 'vegetarian', 'omnivore'),
  (1295, 'orange roughy with dill sauce', 'vegetarian', 'omnivore'),
  (1628, 'scandinavian hash  biksemad', 'vegetarian', 'omnivore'),
  (1041, 'kittencal s egg or tuna and olive salad sandwiches', 'vegetarian', 'omnivore'),
  (1274, 'okonomi yaki  veggie pancakes', 'vegetarian', 'omnivore');

do $$
declare
  EXPECTED_LABEL_ROWS constant int := 1;
  expected_diet_rows  constant int := (select count(*) from diet_fix);
  changed int;
begin
  -- (a) nhãn fish cho #1041
  insert into public.recipe_allergens (recipe_id, allergen_id)
  select r.id, a.id from public.recipes r, public.allergens a
  where r.id = 1041 and r.title = 'kittencal s egg or tuna and olive salad sandwiches' and a.slug = 'fish'
  on conflict do nothing;
  get diagnostics changed = row_count;
  if changed <> EXPECTED_LABEL_ROWS then
    raise exception 'nhãn fish #1041: % dòng, cần % (id/tên lệch hoặc đã có nhãn) — huỷ', changed, EXPECTED_LABEL_ROWS;
  end if;

  -- (b) diet_type: chỉ khi id + tên + giá trị cũ đều khớp
  update public.recipes r set diet_type = f.new_diet
  from diet_fix f
  where r.id = f.recipe_id and r.title = f.title and r.diet_type = f.old_diet;
  get diagnostics changed = row_count;
  if changed <> expected_diet_rows then
    raise exception 'diet_type: % dòng, cần % (id/tên/diet cũ lệch hoặc đã áp) — huỷ', changed, expected_diet_rows;
  end if;
end $$;

commit;
