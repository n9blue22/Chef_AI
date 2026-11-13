-- Hoàn tác docs/eval/label-fixes-2.sql: gỡ nhãn fish của #1041 và trả diet_type về đúng giá trị lúc dump (2026-11-13).
-- Lúc dump #1041 chưa có fish, nên xoá cặp này không đụng nhãn cũ (trừ khi nhãn được thêm bằng đường khác sau ngày dump).
-- Chỉ trả diet_type khi giá trị hiện tại đúng là giá trị label-fixes-2.sql đã đặt.
-- Số dòng kỳ vọng: DELETE recipe_allergens = 1, UPDATE recipes = 3. Lệch là huỷ cả giao dịch.
begin;

create temp table diet_fix (recipe_id bigint, title text, old_diet text, new_diet text) on commit drop;
insert into diet_fix (recipe_id, title, old_diet, new_diet) values
  (120, 'baked parmesan fish', 'vegetarian', 'omnivore'),
  (625, 'easy baked orange roughy', 'vegetarian', 'omnivore'),
  (1295, 'orange roughy with dill sauce', 'vegetarian', 'omnivore');

do $$
declare
  EXPECTED_LABEL_ROWS constant int := 1;
  expected_diet_rows  constant int := (select count(*) from diet_fix);
  changed int;
begin
  delete from public.recipe_allergens ra
  using public.recipes r, public.allergens a
  where ra.recipe_id = r.id and ra.allergen_id = a.id
    and r.id = 1041 and r.title = 'kittencal s egg or tuna and olive salad sandwiches' and a.slug = 'fish';
  get diagnostics changed = row_count;
  if changed <> EXPECTED_LABEL_ROWS then
    raise exception 'gỡ nhãn fish #1041: % dòng, cần % — huỷ', changed, EXPECTED_LABEL_ROWS;
  end if;

  update public.recipes r set diet_type = f.old_diet
  from diet_fix f
  where r.id = f.recipe_id and r.title = f.title and r.diet_type = f.new_diet;
  get diagnostics changed = row_count;
  if changed <> expected_diet_rows then
    raise exception 'trả diet_type: % dòng, cần % — huỷ', changed, expected_diet_rows;
  end if;
end $$;

commit;
