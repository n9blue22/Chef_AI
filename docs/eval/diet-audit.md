# Rà món chay có từ khoá thịt / cá / hải sản / trứng / sữa

Ngày 2026-11-13 · nhánh `fix/allergen-labels-2` · chỉ đọc. Nguồn: bản dump chỉ-đọc 2026-11-13 (3171 món: omnivore 1852,
vegetarian 851, vegan 468) và tên nguồn trong `backend/data/vifoodrec_processed.csv`, `foodcom_filtered.csv`
(cả 1319 món chay đều tra được nguồn theo tên món). Không ghi DB, không đọc `.env`, không gọi model, không chạy test.
Script `diet_audit.py` để ở scratchpad, không đưa vào repo.

## Cách dò

- Phạm vi: mọi món `vegetarian` hoặc `vegan`.
- Dò trên 3 chỗ: **tên món**, **tên gốc chưa map** (`raw_ingredient_names`), và thêm **tên nguyên liệu nguồn** (CSV).
  Lý do thêm cột nguồn: lúc seed, món chỉ được xếp chay khi mọi tên chưa map đều là gia vị trung tính
  (`classify_diet`), nên `raw_ingredient_names` của món chay gần như không bao giờ chứa thịt. Lỗi thật nằm ở tên
  **đã map nhầm** (vd `orange roughy fillets` → `Cam`), chỉ thấy được khi đọc tên nguồn.
- Từ khoá thịt/cá/hải sản (cả 2 loại món): thịt, bò, heo, lợn, gà, vịt, ngan, dê, cừu, cá, tôm, tép, mực, cua, ghẹ,
  nghêu, sò, hàu, ốc, hến, mắm, ruốc, nước mắm, xương, sườn, giò, chả, lạp xưởng, pate, huyết, lòng, bạch tuộc, sứa,
  hải sản, dầu hào, chà bông, xúc xích, jambon, ba chỉ · meat, beef, pork, chicken, turkey, duck, lamb, veal, venison,
  bacon, ham, sausage, pepperoni, salami, prosciutto, pancetta, chorizo, hot dog, meatball, steak, lard, suet, gelatin(e),
  fish, fish sauce, oyster sauce, worcestershire, anchovy, salmon, tuna, cod, roughy, haddock, halibut, tilapia, trout,
  sardine, mackerel, snapper, sea bass, catfish, swordfish, mahi, pollock, flounder, bonito, dashi, shrimp, prawn, crab,
  lobster, crawfish, crayfish, scallop, clam, oyster, mussel, squid, calamari, octopus, seafood, caviar, roe.
- Từ khoá trứng/sữa (trứng, sữa, phô mai, bơ, kem, egg, yolk, mayo(nnaise), milk, cheese, butter, cream, yogurt, ghee,
  whey, parmesan, mozzarella, ricotta, feta): **chỉ dò ở món `vegan`**, vì `vegetarian` được phép có trứng/sữa.
- Khớp nguyên từ (cho phép `-s`), bỏ trước các cụm trông giống: nấm đùi gà, trứng gà/vịt/cút, lòng đỏ/trắng, tỏi tép,
  eggplant, sữa dừa/đậu nành/hạt…, coconut/soy/almond milk, bơ đậu phộng, quả/trái bơ, peanut butter, butternut,
  cream of tartar, ice cream.

**Kết quả: 46 món khớp.** 4 món chắc chắn có cá/thịt, 3 món chờ anh duyệt, 39 món khớp nhầm.

## 1. Chắc chắn có cá/thịt → đã đưa vào `label-fixes-2.sql` (diet_type → `omnivore`)

| id | Tên | diet_type | Từ khoá khớp | Nguyên liệu đã map | Căn cứ |
|---|---|---|---|---|---|
| 120 | baked parmesan fish | vegetarian | tên: fish · nguồn: `orange roughy fillets` → roughy | Cam; Trứng gà; Sữa tươi; Bột mì; Muối; Phô mai parmesan; Bột paprika | `orange roughy` (cá) map nhầm thành `Cam` |
| 625 | easy baked orange roughy | vegetarian | tên: roughy · nguồn: `orange roughy fillets` | Cam; Bơ; Muối; Bột paprika | như trên |
| 1295 | orange roughy with dill sauce | vegetarian | tên: roughy · nguồn: `orange roughy fillets` | Thì là; Cam; Chanh vàng; Chanh; Phô mai parmesan; Xốt mayonnaise; Mù tạt | như trên |
| **1628** | **scandinavian hash  biksemad** | vegetarian | nguồn: `meat` | Khoai tây; Hành tây; **Cơm dừa**; Trứng gà; Bơ; Muối | `meat` map nhầm thành `Cơm dừa` (coconut meat). Các bước nấu: *"add meat and cook for 2-3 minutes"*, mô tả: *"re-cycling left over roasts"* |

#120, #625, #1295 là việc 1; **#1628 là món mới tìm thấy** khi rà, đã thêm vào cùng file SQL và rollback.

## 2. Chờ anh duyệt (KHÔNG có trong SQL) — cập nhật: #1041, #1274 đã chuyển vào SQL, xem mục 5

| id | Tên | diet_type | Từ khoá khớp | Nguyên liệu đã map | Vì sao chưa chắc |
|---|---|---|---|---|---|
| 1041 | kittencal s egg or tuna and olive salad sandwiches | vegetarian | tên: tuna | Xà lách; Cà chua; Hành lá; Trứng gà; Bánh mì; Muối; Xốt mayonnaise; Ớt cayenne; Ô liu đen | Nguồn **không có cá ngừ** (chỉ `hard-boiled eggs`…); tên cho chọn trứng *hoặc* cá ngừ. Làm theo công thức thì là món chay. `label-fixes-2.sql` đã thêm nhãn `fish` (chặn người dị ứng cá) nhưng **giữ** `vegetarian`. Đổi sang `omnivore` nếu anh muốn bảo thủ. |
| 1274 | okonomi yaki  veggie pancakes | vegetarian | nguồn: `meat` | Bắp cải; Cà rốt; Hành tây; Cần tây; **Cơm dừa**; Trứng gà; Sữa tươi; Bột mì; Đường nâu; Muối | Nguồn có `meat` (cũng map nhầm thành `Cơm dừa`), nhưng tên ghi "veggie" và các bước nấu không nhắc thịt. Dù chay hay không thì `Cơm dừa` vẫn sai. |
| 2034 | Bánh sen chiên giòn | vegetarian | nguồn: `bột giòn hải sản` → hải sản | Tỏi; Ớt; Củ sen; Rau húng; Chanh; Bột mì; Mè; Dầu ăn; Tương cà; Xốt mayonnaise; Tương ớt; Hạt sen | Là bột chiên giòn bán sẵn loại "dùng cho hải sản"; thường không có hải sản nhưng em chưa kiểm được thành phần. |

## 3. Khớp từ khoá nhưng không có thịt/cá/trứng/sữa (dương tính giả, không sửa)

**Nước chấm / ướp / bột áo "dùng cho" món mặn**: tên nhắc thịt/cá, nguồn và nguyên liệu đã map không có.

| id | Tên | diet_type | Từ khoá (tên) |
|---|---|---|---|
| 37 | amazing pork chop or chicken marinade | vegan | chicken, pork |
| 183 | batter for sweet and sour shrimp | vegetarian | shrimp |
| 190 | beef stew seasoning mix | vegan | beef |
| 380 | cheddar bay biscuits  red lobster | vegetarian | lobster (tên nhà hàng) |
| 531 | creamy lemon butter sauce for fish and seafood | vegetarian | fish, seafood |
| 1242 | mustard sauce for corned beef | vegetarian | beef |
| 1248 | my secret shrimp sauce recipe | vegetarian | shrimp |
| 1396 | pineapple glaze for baked ham | vegan | ham |
| 1815 | tempura batter for fish and vegetables | vegetarian | fish |
| 1854 | the only marinade you will need for grilled salmon | vegan | salmon |
| 1877 | tom s oven steak fries | vegan | steak (khoai cắt múi) |
| 1993 | zankou chicken s lebanese garlic sauce  copycat | vegan | chicken (tên nhà hàng) |
| 2475 | Muối Chanh Ớt Chấm Gà Luộc | vegan | gà |

**Tên bánh Việt** (không có thịt): Bánh bò — #2247, 2302, 2543, 2557, 2904, 2907, 2913, 2914, 2915, 2917, 2993 (bò);
Bánh da lợn / da heo — #2284, 2560, 2786, 2788, 2791 (heo/lợn); #2217 Bánh Mì Xoắn **Ốc** Nhân Kem Trứng (ốc = hình xoắn).

**Món vegan khớp trứng/sữa nhưng không có**: #630, #1199 bread and butter pickles (dưa chua, butter là tên kiểu muối);
#1825 thai dipping sauce for spring wrap or egg rolls (nước chấm); #2223 Chè Bơ Viên, #2491 Salad Bơ Giảm Cân
(đã map `Quả bơ`, đúng).

**Tên món trùng nhiều dòng nguồn** (khớp nhầm sang một công thức khác cùng tên; nguyên liệu đã map khớp bản chay):
#2982 Bánh Tằm Bì, #2991 Bánh Bao Chiên, #3075 Bánh Bắp Chiên, #3162 Bánh Khoai Lang.

## 4. Thấy thêm (chưa sửa)

- `meat` → `Cơm dừa` là lỗi map tên, không phải lỗi nhãn. Ở món chay chỉ gặp #1628 và #1274; món `omnivore` có thể cũng bị
  (không ảnh hưởng chế độ ăn, nhưng sai nguyên liệu và độ phủ). Em chưa rà phần này.
- Rà theo từ khoá không bắt được món map nhầm mà cả tên món lẫn tên nguồn đều không có từ khoá (vd tên cá lạ ngoài danh sách).

## 5. Đọc kỹ 3 món chờ duyệt (2026-11-13)

Nguồn: CSV, đọc đủ nguyên liệu và mọi bước nấu.

### #1041 kittencal s egg or tuna and olive salad sandwiches · vegetarian · foodcom 97601
- Nguyên liệu nguồn: hard-boiled eggs, green onions, seasoning salt, stuffed green olive, mayonnaise, fresh ground black pepper, cayenne pepper, bread, lettuce, tomatoes.
- Bước: 1. slice the cooked eggs using an egg slicer or coarsely chop using a fork **or flake the tuna** in a bowl using a fork ·
  2. add in all remaining ingredients · 3. lightly mix with a large spatula or spoon until combined ·
  4. cover and refrigerate for 2 or more hours to blend the flavors · 5. divide the mixture to make sandwiches.
- Kết luận: các bước nấu có cá ngừ là một lựa chọn → anh chốt đổi sang `omnivore` và giữ nhãn `fish`.

### #1274 okonomi yaki  veggie pancakes · vegetarian · foodcom 38400
- Nguyên liệu nguồn: green cabbage, carrot, onion, celery, whole wheat flour, egg, brown sugar, salt, evaporated milk, water, **meat**.
- Bước: 1. mix together the veggies · 2. mix together the remaining ingredients to form a smooth, pourable batter ·
  3. mix the veggies in the batter … adjust with either water or flour · 4. on a heated sprayed with oil skillet drop spoonfuls of batter ·
  5. your heat should be medium · 6. brown well on one side flip and brown on the other · 7. serve hot or cold.
- Kết luận: các bước không nhắc tới thịt, nhưng nguyên liệu có `meat` (bước 2 "remaining ingredients") → anh chốt đổi sang `omnivore`.

### #2034 Bánh sen chiên giòn · vegetarian · vifoodrec-136 (CHƯA đưa vào SQL)
- Nguyên liệu nguồn: củ sen non, hạt sen, mè đen, húng lũi, nước cốt chanh, tỏi, ớt, tỏi phi, tương ớt, tương cà, dầu ăn,
  **bột giòn hải sản**, xốt mayonnaise aji mayo vị nguyên bản.
- Bước: 1. Đun nóng dầu ăn, múc 1 miếng củ sen và xếp vài hạt sen lên trên, cho bánh vào chảo dầu trở đều hai mặt đến khi chín
  vàng, vớt ra để ráo dầu. · 2. Pha xốt chấm: 3 muỗng xốt Mayonnaise Aji-Mayo, 1 muỗng nước chanh, 1 muỗng tương ớt, 1/2 muỗng tương cà.
- "Bột giòn hải sản" là **Aji-Quick Bột Chiên Giòn Hải Sản** (Ajinomoto): trong ViFoodRec có 60 công thức dùng loại bột này, và các
  bước nấu gọi đúng tên đó. Bột được dùng để tẩm tôm, cá, sườn, cánh gà, đậu hũ, chả nấm. Vậy "hải sản" là **món nên dùng bột này**,
  không phải thành phần của bột.
- Thành phần: trang Ajinomoto Việt Nam chỉ nêu chung cho dòng Aji-Quick là tinh bột, bột mì, bột bắp, vụn bánh mì, hành, tỏi…,
  **không có bảng thành phần riêng cho loại Hải Sản**. Không thấy nguồn nào nói bột có hải sản thật, nhưng cũng **chưa xác nhận**
  được (cần xem nhãn bao bì). Món đã có nhãn `wheat` qua `Bột mì`. Đề xuất giữ `vegetarian`, chờ anh quyết.
