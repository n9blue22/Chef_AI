-- Kiểm trước và sau khi áp docs/eval/label-fixes-2.sql. CHỈ SELECT, không ghi gì.
-- Chạy cả file trước khi áp, rồi chạy lại sau khi áp; so cột "ky_vong_truoc" / "ky_vong_sau".
-- Giá trị "trước" lấy từ bản dump chỉ-đọc 2026-11-13.

-- 1. Từng món: id + tên khớp, diet_type, có nhãn fish chưa.
--    Trước: 120/625/1295/1628 = vegetarian; sau: = omnivore. 1041 giữ vegetarian.
--    #1041 có_fish: trước = false, sau = true. #120/625/1295 đã có fish từ đợt 1 (cả trước lẫn sau = true).
select
  v.recipe_id,
  r.title = v.title                                   as ten_khop,
  r.diet_type,
  v.diet_truoc                                        as ky_vong_truoc,
  v.diet_sau                                          as ky_vong_sau,
  exists (
    select 1 from public.recipe_allergens ra join public.allergens a on a.id = ra.allergen_id
    where ra.recipe_id = v.recipe_id and a.slug = 'fish'
  )                                                   as co_fish,
  v.fish_truoc                                        as fish_ky_vong_truoc,
  v.fish_sau                                          as fish_ky_vong_sau
from (values
  (120,  'baked parmesan fish',                               'vegetarian', 'omnivore',   true,  true),
  (625,  'easy baked orange roughy',                          'vegetarian', 'omnivore',   true,  true),
  (1295, 'orange roughy with dill sauce',                     'vegetarian', 'omnivore',   true,  true),
  (1628, 'scandinavian hash  biksemad',                       'vegetarian', 'omnivore',   false, false),
  (1041, 'kittencal s egg or tuna and olive salad sandwiches', 'vegetarian', 'vegetarian', false, true)
) v (recipe_id, title, diet_truoc, diet_sau, fish_truoc, fish_sau)
left join public.recipes r on r.id = v.recipe_id
order by v.recipe_id;

-- 2. Tổng: số món theo diet_type và tổng số dòng recipe_allergens.
--    Trước: omnivore 1852, vegetarian 851, vegan 468; recipe_allergens 5623 (= 5439 lúc dump + 184 của đợt 1).
--    Sau:   omnivore 1856, vegetarian 847, vegan 468; recipe_allergens 5624 (tăng đúng 1).
select diet_type, count(*) as so_mon from public.recipes group by diet_type order by diet_type;
select count(*) as recipe_allergens_rows from public.recipe_allergens;

-- 3. Mọi nhãn hiện có của 5 món (đọc bằng mắt: sau khi áp, chỉ #1041 có thêm fish).
select ra.recipe_id, string_agg(a.slug, ', ' order by a.slug) as nhan
from public.recipe_allergens ra join public.allergens a on a.id = ra.allergen_id
where ra.recipe_id in (120, 625, 1041, 1295, 1628)
group by ra.recipe_id
order by ra.recipe_id;

-- 4. Món chay/thuần chay mà mang nhãn fish (tính trên dump + đợt 1).
--    Trước: đúng 3 dòng #120, #625, #1295. Sau: đúng 1 dòng #1041 (cố ý giữ vegetarian, xem diet-audit.md mục 2).
select r.id, r.title, r.diet_type
from public.recipes r
where r.diet_type in ('vegetarian', 'vegan')
  and exists (
    select 1 from public.recipe_allergens ra join public.allergens a on a.id = ra.allergen_id
    where ra.recipe_id = r.id and a.slug = 'fish'
  )
order by r.id;
