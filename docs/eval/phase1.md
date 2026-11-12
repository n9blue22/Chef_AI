# Đánh giá giai đoạn 1: tìm công thức (không LLM)

Ngày chạy: 2026-11-12, trên DB thật (3171 công thức, 232 nguyên liệu). Chỉ đọc DB. Không gọi Groq/Gemini/Cloudflare,
không gọi `/recipes/suggest`. Cấu hình được nạp qua `app.core.config`.

Mỗi ca chạy đúng các bước mà `suggest_recipes` làm trước khi gọi LLM:
`IngredientNormalizer` → `build_query_text` → `BgeM3Provider.embed` → `search_recipes` (RPC, top 5).
Sau đó món trả về được **đọc lại thẳng từ bảng** (`recipes`, `recipe_allergens`, `recipe_ingredients` → `ingredients`
→ `ingredient_allergens`) để kiểm chéo bộ lọc SQL.

- Bộ ca: `backend/scripts/eval/cases.json` (40 ca)
- Script: `backend/scripts/eval/run_phase1.py`; phép kiểm thuần nằm ở `phase1_checks.py`, bảng tóm tắt ở `phase1_report.py`
- Chạy (cwd = `backend`): `venv\Scripts\python.exe -m scripts.eval.run_phase1`
- Đầu ra (gitignore): `backend/scripts/eval/out/phase1-<giờ>.jsonl` (mỗi ca 1 dòng), `order-<giờ>.jsonl`, `summary-<giờ>.md`

Quy ước giống luồng quét ảnh: chỉ nguyên liệu khớp **tự nhận** (`accepted`) được gửi đi tìm. Tên `uncertain`
(user phải tự tick) và `rejected` thì bị bỏ.

## Kết quả chính

| Tiêu chí | Kết quả |
|---|---|
| Món lọt dị ứng (theo nhãn món **hoặc** theo nguyên liệu) | **0** / 158 món |
| Món sai chế độ ăn (theo nhãn món **hoặc** cờ chay của từng nguyên liệu) | **0** / 158 món |
| Nghi vấn theo tên gốc chưa map (dò từ khoá) | 0 |
| Ca trả đủ 5 món | 28/40; 12 ca trả ít hơn, trong đó 4 ca trả 0 món |
| Đảo thứ tự nguyên liệu: top 5 cùng tập món / cùng thứ hạng | 11/20 (55%) / 2/20 (10%) |
| Nhúng / tìm, trung vị (máy local) | 432 ms / 404 ms |

## 1. Dị ứng

"Ca có nguyên liệu gây dị ứng" nghĩa là danh sách nguyên liệu của user có ít nhất một thứ mang nhãn dị ứng đó.
Số liệu này đếm từ `ingredient_allergens` sau khi khớp tên, không đếm theo tag trong file ca.

| Dị ứng | Ca | Ca có nguyên liệu gây dị ứng | Món trả về | Món lọt | Nghi vấn tên gốc |
|---|---|---|---|---|---|
| fish | 4 | 4 | 20 | 0 | 0 |
| shellfish | 4 | 3 | 16 | 0 | 0 |
| molluscs | 4 | 4 | 20 | 0 | 0 |
| egg | 4 | 4 | 15 | 0 | 0 |
| dairy | 4 | 4 | 15 | 0 | 0 |
| peanut | 2 | 2 | 7 | 0 | 0 |
| tree_nuts | 2 | 2 | 10 | 0 | 0 |
| soy | 4 | 4 | 16 | 0 | 0 |
| wheat | 3 | 3 | 14 | 0 | 0 |
| sesame | 2 | 2 | 10 | 0 | 0 |

Ca nhiều dị ứng (c28, c40) được đếm ở mọi dòng liên quan. Vì vậy cột "Món trả về" cộng lại lớn hơn tổng số món.

**Số món lọt: 0.** Không món nào có nhãn dị ứng của user ở `recipe_allergens`, cũng không món nào có nguyên liệu
mang nhãn đó.

Các ca khó đều không lọt:

| Ca | Nguyên liệu bẫy | Dị ứng | Khớp thành |
|---|---|---|---|
| c01, c02 | nước mắm | fish | Nước mắm (fish) |
| c03 | chả lụa | fish | Chả lụa (fish) |
| c05 | mắm tôm | shellfish | Mắm tôm (shellfish) |
| c08, c28 | dầu hào | molluscs | Dầu hào (molluscs) |
| c11 | mì trứng | egg | Mì trứng (egg, wheat) |
| c12 | xốt mayonnaise | egg | Xốt mayonnaise (egg) |
| c14 | bơ | dairy | Bơ = Butter (dairy), không phải Quả bơ |
| c20, c38 | nước tương / soy sauce | soy | Nước tương (soy, wheat) |
| c25 | nước tương | wheat | Nước tương (soy, wheat) |
| c27 | dầu mè | sesame | Dầu mè (sesame) |

## 2. Chế độ ăn

| Chế độ ăn | Ca | Món trả về | Món sai chế độ |
|---|---|---|---|
| omnivore | 25 | 102 | 0 |
| vegetarian | 6 | 25 | 0 |
| vegan | 9 | 31 | 0 |

Ca c32 (người thuần chay có nước mắm trong bếp) cũng sạch: nước mắm vẫn được gửi đi, nhưng không món nào trả về chứa nó.

## 3. Số món và độ phủ

- Ca được tìm (có ít nhất 1 nguyên liệu tự nhận): 39/40. Ca c37 có 3 tên đều `uncertain` nên không được tìm.
- Trung bình 4,05 món mỗi ca được tìm.
- Độ phủ phía món (công thức như SQL: phần nguyên liệu bắt buộc **của món** mà user có): trung bình 0,57.
- Phần nguyên liệu **của user** mà món dùng (không tính gia vị cơ bản): trung bình 0,45.

### Ca trả ít hơn 5 món

| Ca | Món | Chế độ / dị ứng | Nguyên liệu đã khớp | Không chắc / chưa khớp | Lý do chính |
|---|---|---|---|---|---|
| c06 | 1 | omnivore + shellfish | Cua, Mồng tơi, Mướp, Tôm khô | — | 2/4 nguyên liệu là thứ user dị ứng |
| c16 | 2 | vegan + peanut | Đậu phộng, Rau muống, Tỏi | — | đậu phộng bị cấm, còn 2 rau |
| c21 | 3 | vegan + soy | Đậu phụ, Cà chua, Hành lá | — | món chính (đậu phụ) bị cấm |
| c22 | 3 | vegan + soy | Đậu nành, Gạo tẻ | — | ít nguyên liệu, đậu nành bị cấm |
| c25 | 4 | vegan + wheat | Nước tương, Đậu phụ, Nấm hương, Gừng | — | nước tương bị cấm, kho món thuần chay nhỏ |
| c32 | 2 | vegan | Đậu phụ, Nấm rơm, Nước mắm, Hành lá | — | kho món thuần chay nhỏ |
| c33 | 2 | vegan | Rau muống, Tỏi | — | ít nguyên liệu |
| c34 | 1 | omnivore | Thịt bò đùi | — | 1 nguyên liệu |
| c35 | 0 | omnivore | Cá thu | — | 1 nguyên liệu, mọi món cá thu cần ≥ 3 thứ |
| c36 | 0 | omnivore | Thịt heo xay | rau dền, cá lóc, lá lốt | 3/4 tên không có trong danh mục |
| c37 | 0 | omnivore | — | rau xanh, nấm, cá | không tên nào tự nhận nên không tìm |
| c40 | 0 | vegetarian + egg + dairy | Trứng gà, Phô mai cheddar, Cà chua, Bánh mì | — | 2/4 nguyên liệu bị cấm |

## 4. Thời gian phía backend

| Giai đoạn | n | Trung vị (ms) | p95 (ms) | Max (ms) |
|---|---|---|---|---|
| Nhúng (bge-m3, CPU, đã nạp sẵn model) | 39 | 432 | 694 | 1094 |
| `search_recipes` (RPC, tính cả mạng) | 39 | 404 | 996 | 1195 |

Đo trên máy dev Windows, gọi Supabase qua mạng nhà. Số này **không phải** số của server Azure.
Thời gian RPC có cả round-trip mạng.

## 5. Đảo thứ tự nguyên liệu

Lấy 20 ca đầu có ≥ 4 nguyên liệu tự nhận, đảo ngược danh sách id rồi tìm lại.

- Top 5 cùng tập món (theo id): **11/20 (55%)**. Trung bình 0,90 id trùng (4,5/5 món).
- Top 5 cùng thứ hạng ở mọi vị trí: **2/20 (10%)**. Trung bình 0,50 vị trí trùng.
- c06 chỉ có 1 món nên giống hệt là điều hiển nhiên. Bỏ c06 thì chỉ còn 1/19 ca giữ nguyên thứ hạng.

5 ca lệch nhiều nhất:

| Ca | Số nguyên liệu | id trùng | vị trí trùng | Top gốc | Top đảo |
|---|---|---|---|---|---|
| c24 | 4 | 0.60 | 0.00 | [2450, 71, 1547, 142, 1286] | [1811, 1547, 71, 2450, 1259] |
| c07 | 4 | 0.80 | 0.20 | [783, 897, 655, 1667, 1973] | [783, 655, 1667, 1435, 897] |
| c12 | 4 | 0.80 | 0.20 | [2694, 1562, 2662, 2279, 2988] | [2694, 2662, 1562, 2580, 2279] |
| c13 | 4 | 0.80 | 0.20 | [2331, 1221, 1791, 2707, 947] | [2331, 2707, 1221, 1791, 2766] |
| c19 | 4 | 0.80 | 0.40 | [2522, 3120, 2654, 3128, 2629] | [2522, 3120, 3128, 2654, 3159] |

Nguyên nhân: `build_query_text` ghép tên theo đúng thứ tự user gửi, nên đảo thứ tự cho ra câu khác và vector khác.
Độ phủ không đổi. Phần điểm từ độ giống văn bản (0,6·sim) thì đổi, và nhiều món nằm sát nhau quanh ngưỡng nên
đổi chỗ cho nhau. Món #1 thường giữ nguyên, các hạng 2–5 xáo trộn. Món ở hạng 5 có thể bị thay bằng món khác.

## 6. Phân tích lỗi

1. **An toàn: chưa thấy lỗi.** Lọc dị ứng và chế độ ăn trong SQL khớp với kiểm tra độc lập ở cả hai tầng
   (nhãn món và nhãn nguyên liệu), kể cả với các gia vị mang nhãn ẩn.
2. **Nguyên liệu user dị ứng vẫn được dùng để tìm.** Khi user có món mình dị ứng (cá thu ở c01, tôm ở c04,
   đậu phụ ở c21), tên đó vẫn nằm trong câu embed và trong `p_ingredient_ids`. Vector bị kéo về các món sẽ bị lọc,
   và món chính coi như mất. Đây là nguyên nhân chính của 6/12 ca thiếu món (c06, c16, c21, c22, c25, c40).
   Ví dụ c04 (tôm, bí đao, hành lá): top 5 là món bí, khổ qua, đậu hũ, mỗi món chỉ dùng 1/3 thứ user có. Có thể bỏ nguyên liệu
   mang dị ứng của user khỏi truy vấn trước khi embed. Em **chưa làm**.
3. **Độ phủ chỉ tính phía món** (đã nêu ở `docs/investigate-fish.md`). Trung bình món chỉ dùng 45% nguyên liệu
   của user. Ví dụ dễ thấy: c03 (thịt ba chỉ, chả lụa, bánh mì, dưa leo) ra 4 món nước ép/detox dưa leo;
   c25 (đậu phụ, nấm hương, nước tương, gừng) ra mứt gừng và chuối sấy.
4. **Ít nguyên liệu → 0–1 món** (c34, c35). Với 1 nguyên liệu, ngưỡng phủ 0,5 chỉ cho qua món có ≤ 2 nguyên liệu
   bắt buộc (không tính gia vị cơ bản).
5. **Tên chưa khớp:** `cá lóc`, `lá lốt` bị loại; `rau dền`, `cải ngọt`, `rau xanh`, `nấm`, `cá` chỉ ở mức
   `uncertain` nên không được gửi đi. Tên tiếng Anh (c38) khớp hết.
6. **Thứ tự nguyên liệu làm đổi thứ hạng** ở 90% ca (mục 5). Có thể sắp `ingredient_ids` theo id trước khi dựng
   câu embed để cùng một tập nguyên liệu luôn cho cùng một kết quả. Em **chưa làm**.

## 7. Giới hạn của bộ ca

- **40 ca không đại diện.** Em tự chọn tay, nghiêng về ca dị ứng (30/40 ca có ít nhất 1 dị ứng). Mỗi loại dị ứng
  chỉ có 2–4 ca, nên 0 lọt ở đây không chứng minh được tỉ lệ lọt bằng 0 trên toàn bộ người dùng.
- Tên nguyên liệu do em gõ, **không phải đầu ra Gemini thật**. Ca tên tiếng Anh chỉ có 1.
- Phép kiểm dùng **cùng nguồn nhãn** với SQL (`ingredient_allergens`, cờ `is_vegetarian`/`is_vegan`). Nếu một
  nguyên liệu trong danh mục bị gán nhãn sai thì cả SQL lẫn phép kiểm đều không thấy. Cột "nghi vấn tên gốc" dùng
  đúng hàm dò từ khoá mà script seed đã dùng để gắn nhãn, nên cột này gần như luôn bằng 0 theo cách xây dựng.
- Không có đáp án chuẩn về độ liên quan, nên chỉ đo được độ phủ chứ không đo được món có "đúng ý" hay không.
- Chỉ xét top 5 (giới hạn của RPC). Không đánh giá bước LLM chỉnh món và lớp validation sau LLM.
- Luồng tủ lạnh (user tick cả tên `uncertain`) không được mô phỏng.
- Chạy 1 lần. Thời gian đo trên máy local nên dao động theo mạng.
