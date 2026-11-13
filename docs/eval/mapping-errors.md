# Lỗi map tên nguyên liệu: "meat" → Cơm dừa và các lỗi cùng kiểu

Ngày 2026-11-13 · nhánh `fix/allergen-labels-2` · chỉ đọc, **không sửa**. Không ghi DB, không đọc `.env`, không gọi model,
không chạy test. Script `replay_map.py` để ở scratchpad, không đưa vào repo.

## Cách đo

DB không lưu tên nguồn của nguyên liệu đã map (`raw_ingredient_names` chỉ giữ tên **không** map được). Vì vậy em chạy lại
đúng hàm seed `scripts/recipe_preparation.map_ingredients` trên danh mục của bản dump chỉ-đọc 2026-11-13 (232 nguyên liệu;
cờ động vật lấy từ `data/ingredients_vn_manual.csv` và `ingredients_usda.csv`), với tên nguồn trong
`vifoodrec_processed.csv` / `foodcom_filtered.csv`.

**Kiểm độ tin cậy:** ở **3109/3171 món**, tập nguyên liệu chạy lại **trùng khít** `recipe_ingredients` trong dump. Món có
tên trùng nhiều dòng nguồn thì lấy đúng dòng cho kết quả trùng. 62 món còn lại không tái hiện được, nhiều khả năng do
danh mục đã thêm alias sau lúc seed. 62 món này bị loại khỏi phần đếm theo cặp tên → nguyên liệu, nhưng **có** được tính
trong phần quét "meat" ở mục 1 (quét thẳng trên dump + CSV).

## 1. "meat" → Cơm dừa

| id | Tên | diet_type (dump) | Tên nguồn | Map thành | Kiểu khớp |
|---|---|---|---|---|---|
| 1274 | okonomi yaki  veggie pancakes | vegetarian | `meat` | Cơm dừa | mờ, điểm 100 |
| 1628 | scandinavian hash  biksemad | vegetarian | `meat` | Cơm dừa | mờ, điểm 100 |

- **Phạm vi: đúng 2 món, cả 2 đều `vegetarian`** (omnivore 0, vegan 0). Quét toàn bộ 3171 món (cả 62 món không tái hiện được):
  chỉ 2 món này có tên nguồn `meat` trơn mà lại mang `Cơm dừa`. Cả 2 đã được chuyển sang `omnivore` trong `label-fixes-2.sql`.
- 5 món đang có `Cơm dừa`: 2 món trên (sai), cùng #2832 Thịt Ba Rọi Kho Cùi Dừa, #2247 Bánh Bò Cốt Dừa Lá Dứa,
  #2355 Nấm Rơm Cơm Dừa Kho Tiêu. 3 món sau map từ tên nguồn `cơm dừa`, đúng.
- **Nguyên nhân:** `Cơm dừa` có `name_en = "Coconut meat"`, nên `token_set_ratio("meat", "coconut meat") = 100` và chỉ có một
  ứng viên, vì vậy được tự nhận. Lưới chặn `is_contradictory_fuzzy_match` không bắt được vì `MEAT_KEYWORDS`
  (`scripts/ingredient_senses.py`) **không có từ `meat`**: tên thịt không bị coi là trái nghĩa với nguyên liệu chay.
  Lỗi `orange roughy` → `Cam` đi cùng đường: `token_set_ratio` khớp chữ `orange` với `Orange`, và `roughy` không có trong
  từ khoá thịt/cá.

### Có món nào nằm trong bộ demo không

Độ phủ offline, cách tính như `label-fixes-2-demo-check.md`. Ngưỡng lọc là 0,5.

| Bộ | #1274 | #1628 | Đủ điều kiện? | Top 5? |
|---|---|---|---|---|
| S1 | 0,11 | 0,20 | không | không |
| S5 | 0 | 0 | không | không |
| P1 | 0,11 | 0 | không | không |
| S12 (5 thứ) / S12 (3 thứ) | 0 / 0 | 0 / 0 | không | không |

## 2. Top-60 tên nguồn hay gặp nhất

Đếm trên các cặp tên nguồn → nguyên liệu đã map của 3109 món tái hiện được (1869 tên khác nhau). **Không thấy tên nào bị map
sai** trong 60 tên đầu. Mỗi tên luôn ra cùng một nguyên liệu, và nguyên liệu đó đúng nghĩa.

| # | Tên nguồn (số lần) → nguyên liệu | | |
|---|---|---|---|
| 1–4 | salt (1029) → Muối | butter (652) → Bơ | dầu ăn (534) → Dầu ăn | muối (519) → Muối |
| 5–8 | đường trắng (494) → Đường (mờ) | olive oil (426) → Dầu ô liu | sugar (369) → Đường | tỏi (367) → Tỏi |
| 9–12 | onion (345) → Hành tây | eggs (316) → Trứng gà | flour (308) → Bột mì | nước mắm (308) → Nước mắm |
| 13–16 | milk (294) → Sữa tươi | garlic (271) → Tỏi | hành lá (264) → Hành lá | garlic cloves (238) → Tỏi (mờ) |
| 17–20 | hành tím (237) → Hành tím | baking powder (226) → Bột nở | parmesan cheese (218) → Phô mai parmesan | ớt (208) → Ớt |
| 21–24 | đường (193) → Đường | all-purpose flour (176) → Bột mì (mờ) | egg (171) → Trứng gà | trứng gà (168) → Trứng gà |
| 25–28 | vegetable oil (161) → Dầu ăn | bột mì (156) → Bột mì | lemon juice (155) → Chanh vàng (mờ) | paprika (154) → Bột paprika |
| 29–32 | cà rốt (153) → Cà rốt | garlic powder (147) → Tỏi (mờ) | hành tây (146) → Hành tây | brown sugar (145) → Đường nâu |
| 33–36 | sour cream (143) → Kem chua | baking soda (142) → Muối nở | black pepper (139) → Tiêu đen | gừng (139) → Gừng |
| 37–40 | bột năng (133) → Bột năng | potatoes (124) → Khoai tây | nước tương (120) → Nước tương | cheddar cheese (115) → Phô mai cheddar (mờ) |
| 41–44 | fresh parsley (114) → Mùi tây | oil (112) → Dầu ăn | mayonnaise (110) → Xốt mayonnaise | tomatoes (110) → Cà chua |
| 45–48 | soy sauce (107) → Nước tương | bacon (98) → Thịt xông khói | ngò rí (98) → Rau mùi | sả (97) → Sả |
| 49–52 | chicken broth (95) → Nước dùng gà | tôm (94) → Tôm | dầu hào (94) → Dầu hào | parsley (93) → Mùi tây |
| 53–56 | cinnamon (93) → Quế | cà chua (93) → Cà chua | extra virgin olive oil (92) → Dầu ô liu | worcestershire sauce (87) → Xốt worcestershire |
| 57–60 | cayenne pepper (84) → Ớt cayenne | nước cốt chanh (83) → Chanh (mờ) | onions (82) → Hành tây | honey (81) → Mật ong |

## 3. Quét thêm: tên nguồn có từ thịt/cá/hải sản mà bị map sang nguyên liệu không phải động vật

Dùng bộ từ khoá thịt/cá/hải sản của `diet-audit.md`, quét **mọi** cặp tên → nguyên liệu (không chỉ top-60):

| Tên nguồn | → nguyên liệu | Số món (theo diet) | Đánh giá |
|---|---|---|---|
| `bột giòn hải sản` | Bột mì (mờ) | 17 (omnivore 16, vegetarian 1: #2034) | Không phải lỗi: là bột chiên Aji-Quick "dùng cho hải sản" (xem `diet-audit.md` mục 5) |
| `orange roughy fillets` | Cam (mờ) | 3 (vegetarian 3: #120, #625, #1295) | **Lỗi**, đã xử lý nhãn `fish` (đợt 1) và diet (`label-fixes-2.sql`) |
| `meat` | Cơm dừa (mờ) | 2 (vegetarian 2: #1274, #1628) | **Lỗi**, mục 1 |

Không có cặp nào khác. Giới hạn: cách quét này chỉ bắt được tên nguồn **có** từ khoá thịt/cá. Map nhầm giữa hai nguyên liệu
chay (vd `bun` → `Bún` ở các món burger, ghi trong `label-fixes-proof.md` mục 3.2) thì không bắt được.

## Hướng sửa (chưa làm, chờ anh chọn)

1. Thêm `meat` và tên cá còn thiếu (`roughy`, `haddock`, `sea bass`, …) vào `MEAT_KEYWORDS` để `is_contradictory_fuzzy_match`
   chặn khớp mờ sang nguyên liệu chay. Việc này chỉ có tác dụng khi seed lại.
2. Sửa dữ liệu đã seed: gỡ `Cơm dừa` khỏi #1274, #1628 và gỡ `Cam` khỏi #120, #625, #1295 (`recipe_ingredients`). Việc này
   làm đổi độ phủ và hiển thị, không đổi nhãn dị ứng hay diet (đã sửa riêng).
