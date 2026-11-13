# Kiểm trực tiếp nhãn mới (sau `label-fixes.sql`)

Ngày 2026-11-13 · nhánh `main` (đã merge `fix/allergen-labels`) · chỉ đọc: SELECT bảng + RPC `search_recipes` (`stable`),
bge-m3 chạy local, `-X utf8`. Không ghi DB, không đọc `.env` (cấu hình nạp qua `app.core.config`), không gọi LLM, không chạy pytest.
Script: `label_proof.py` trong scratchpad (dùng lại `build_context` của `scripts/eval/run_phase1.py`), không đưa vào repo.

**Kiểm đầu vào:** `label-fixes.sql` có 184 dòng món–nhãn (wheat 94, soy 59, egg 9, tree_nuts 7, peanut 6, fish 5,
shellfish 2, molluscs 1, sesame 1). `Dầu hào` trong DB hiện mang `molluscs, wheat, soy` ✅.

## 1. Món lọt trong `label-audit.md`: có lọc thì không còn, không lọc thì vẫn có

**Cách làm:** truy vấn = mọi nguyên liệu bắt buộc (không tuỳ chọn) của chính món đó, dựng bằng `build_query_text`
giống luồng thật. Diet `omnivore`. Gọi RPC 2 lần: `p_allergens = []` và `p_allergens = [slug]`. RPC trả tối đa 5 món.

| # | Món | Nhãn kiểm | Nhãn món hiện có | Không lọc: có? (hạng) | Có lọc: có? | Đạt |
|---|---|---|---|---|---|---|
| 2290 | Cháo Hàu | molluscs | dairy, molluscs | có (1) | không | ✅ |
| 2521 | Bánh Mì Chảo Sườn Kho Ốp La | wheat | egg, fish, molluscs, soy, wheat | có (1) | không | ✅ |
| 2588 | Bánh Mì Xíu Mại Trứng Muối | wheat | egg, molluscs, soy, wheat | có (1) | không | ✅ |
| 2374 | Đậu Hũ Chiên Sốt Mayonnaise | egg | egg, soy | có (1) | không | ✅ |
| 2468 | Khoai Tây Nghiền Với Trứng Và Thịt Muối | egg | dairy, egg | có (1) | không | ✅ |
| 1902 | tuna and spinach tortellini salad | wheat | dairy, egg, fish, wheat | có (1) | không | ✅ |
| 1902 | tuna and spinach tortellini salad | egg | (như trên) | có (1) | không | ✅ |
| 120 | baked parmesan fish | fish | dairy, egg, fish, wheat | có (1) | không | ✅ |
| 1398 | pioneer woman lasagna | wheat | dairy, egg, wheat | có (1) | không | ✅ |
| 1687 | smoked turkey avocado brie sandwiches | wheat | dairy, egg, wheat | có (1) | không | ✅ |
| 986 | iowa maid rites loose meat sandwiches | wheat | wheat | có (1) | không | ✅ |
| 1581 | salmon and pasta salad | wheat | dairy, egg, fish, wheat | có (1) | không | ✅ |
| 538 | creamy pumpkin pasta | wheat | dairy, wheat | có (1) | không | ✅ |
| 1496 | rachael ray s mamacello pasta | wheat | dairy, wheat | có (1) | không | ✅ |
| 1247 | my my my minestra (soup with pasta) | wheat | dairy, wheat | có (3) | không | ✅ |
| **1041** | **kittencal s egg or tuna and olive salad sandwiches** | **fish** | egg, wheat | có (2) | **có (2)** | ❌ **vẫn lọt** |

**15/16 đạt.** #1041 nằm trong Phụ lục của `label-audit.md` (thiếu fish: món cho chọn trứng *hoặc* cá ngừ) nhưng
**không có dòng nào trong `label-fixes.sql`** → chưa được gắn `fish`. Người dị ứng cá vẫn thấy món này.
Sửa: thêm `(1041, 'fish', 'kittencal s egg or tuna and olive salad sandwiches', 'a')` vào `label-fixes.sql` + rollback — chờ anh duyệt.

Danh sách món trả về từng lần (id, theo hạng), để đối chiếu:

| Món | Không lọc | Có lọc |
|---|---|---|
| 2290 | 2290, 2658, 2438, 3133, 2843 | 2658, 2438, 3133, 2843, 2563 |
| 2521 | 2521, 2574, 2718, 3045, 2635 | 2574, 2718, 3045, 2635, 3050 |
| 2588 | 2588, 2229, 1906, 2215, 2249 | 2229, 1906, 2215, 2644, 2574 |
| 2374 | 2374, 2323, 2885, 2250, 2379 | 2323, 2885, 2250, 2379, 2753 |
| 2468 | 2468, 1510, 211, 2279, 2817 | 1510, 211, 2279, 2817, 491 |
| 1902 | 1902, 1759, 1087, 317, 1369 | 1759, 1087, 317, 1369, 1666 (cả wheat lẫn egg) |
| 120 | 120, 2911, 1403, 799, 1006 | 2911, 1403, 799, 1006, 744 |
| 1398 | 1398, 756, 384, 3083, 2494 | 756, 384, 3083, 2494, 1114 |
| 1041 | 3083, **1041**, 9, 3109, 3134 | 3083, **1041**, 9, 3109, 3134 |
| 1687 | 1687, 2453, 1379, 1164, 1742 | 2453, 1164, 3037, 756, 1611 |
| 986 | 986, 732, 504, 544, 754 | 504, 754 |
| 1581 | 1581, 1583, 1109, 480, 1576 | 1583, 1109, 480, 1576, 1648 |
| 538 | 538, 3076, 33, 197, 1246 | 3076, 197, 1246, 1631, 1465 |
| 1496 | 1496, 1286, 1097, 1670, 71 | 1286, 1097, 1670, 71, 639 |
| 1247 | 1360, 1834, 1247, 756, 1328 | 1360, 1834, 756, 1328, 2442 |

## 2. Mẫu món nhận nhãn mới, mỗi loại 5 món (đọc bằng mắt)

Chọn theo thứ tự trong `label-fixes.sql`, xoay vòng giữa các nhóm thay đổi (`a` rà tên món, `b-dau-hao`, `b-ruoc`,
`c-tu-khoa`) để không dồn một nguồn. molluscs (1), sesame (1), shellfish (2) chỉ có chừng đó món nên in hết.
`[slug]` = nhãn của nguyên liệu danh mục; `raw` = tên gốc chưa map (`raw_ingredient_names`). **Nhãn in đậm = nhãn mới.**

### wheat (94 món)
- **#19 a doozie of a floozie burger** · omnivore · `a` · nhãn: dairy, egg, **wheat**
  Xà lách; Cà chua; Hành tây; Nấm mỡ; Thì là; Thịt bò xay; Trứng gà[egg]; Bơ[dairy]; Phô mai cheddar[dairy]; Bún; Xốt mayonnaise[egg] · raw: cajun seasoning; pepper
- **#1828 thai spicy basil beef** · omnivore · `b-dau-hao` · nhãn: fish, molluscs, soy, **wheat**
  Hành tây; Tỏi; Ớt chuông; Rau mùi; Húng quế; Thịt bò đùi; Dầu ăn; Đường; Nước mắm[fish]; Dầu hào[molluscs,soy,wheat] · raw: chile; white pepper
- **#32 all in one broccoli macaroni and cheese** · vegetarian · `c-tu-khoa` · nhãn: dairy, **wheat**
  Bông cải xanh; Sữa tươi[dairy]; Bơ[dairy]; Phô mai cheddar[dairy] · raw: water; salt and pepper
- **#242 blue moon burgers** · omnivore · `a` · nhãn: dairy, egg, **wheat**
  Xà lách; Cà chua; Hành tây; Thịt bò xay; Phô mai cheddar[dairy]; Bún; Xốt mayonnaise[egg]; Phô mai kem[dairy]; Phô mai monterey jack[dairy]
- **#1829 thai style pork in black pepper (moo pat prik thai dam)** · omnivore · `b-dau-hao` · nhãn: fish, molluscs, soy, **wheat**
  Hành tây; Tỏi; Gừng; Ớt; Ớt chuông; Thịt nạc vai heo; Dầu ăn; Đường; Nước mắm[fish]; Dầu hào[molluscs,soy,wheat]; Tiêu đen · raw: fresh pepper; water

### fish (5 món — in hết)
- **#120 baked parmesan fish** · **vegetarian** · `a` · nhãn: dairy, egg, **fish**, wheat
  Cam; Trứng gà[egg]; Sữa tươi[dairy]; Bột mì[wheat]; Muối; Phô mai parmesan[dairy]; Bột paprika · raw: pepper
- **#625 easy baked orange roughy** · **vegetarian** · `a` · nhãn: dairy, **fish**
  Cam; Bơ[dairy]; Muối; Bột paprika · raw: pepper
- **#899 haddock supreme** · omnivore · `a` · nhãn: dairy, egg, **fish**, wheat
  Tỏi; Trứng gà[egg]; Sữa tươi[dairy]; Bơ[dairy]; Bột mì[wheat]; Dầu ăn; Muối; Tương cà; Bột chiên xù[wheat]; Rượu vang trắng · raw: haddock fillets
- **#1295 orange roughy with dill sauce** · **vegetarian** · `a` · nhãn: dairy, egg, **fish**
  Thì là; Cam; Chanh vàng; Chanh; Phô mai parmesan[dairy]; Xốt mayonnaise[egg]; Mù tạt
- **#1339 pan sauted chilean sea bass** · omnivore · `a` · nhãn: dairy, **fish**
  Cà chua; Tỏi; Húng quế; Chanh vàng; Bơ[dairy]; Dầu ô liu; Lá oregano; Phô mai feta[dairy]; Rượu vang trắng · raw: sea bass fillets; salt & pepper

### egg (9 món)
- **#541 creamy tomato basil tortellini soup** · omnivore · `a` · nhãn: dairy, **egg**, **wheat**
  Cà chua; Hành tây; Tỏi; Húng quế; Sữa tươi[dairy]; Phô mai cheddar[dairy]; Dầu ô liu; Phô mai parmesan[dairy]; Nước dùng gà · raw: light cream
- **#1271 nutty cheese tortellini** · vegetarian · `a` · nhãn: dairy, **egg**, tree_nuts, **wheat**
  Mùi tây; Bơ[dairy]; Phô mai cheddar[dairy]; Phô mai parmesan[dairy]; Quả óc chó[tree_nuts] · raw: fresh coarse ground black pepper
- **#1717 southwest tortellini casserole** · omnivore · `a` · nhãn: dairy, **egg**, **wheat**
  Cà chua; Hành lá; Rau mùi; Chanh; Phô mai cheddar[dairy]; Đậu đen; Đường; Kem chua[dairy]; Thì là ai cập; Phô mai monterey jack[dairy]; Ô liu đen · raw: diced green chilies
- **#1742 spicy tortellini soup** · omnivore · `a` · nhãn: dairy, **egg**, **wheat**
  Rau chân vịt; Cà chua; Hành tím; Tỏi; Húng quế; Phô mai cheddar[dairy]; Nước dùng gà; Ớt cayenne; Lá oregano · raw: reduced-sodium chicken broth; ground black pepper
- **#1762 spinach artichoke cheesy tortellini** · omnivore · `a` · nhãn: dairy, **egg**, wheat
  Rau chân vịt; Hành tây; Tỏi; Bơ[dairy]; Phô mai cheddar[dairy]; Kem tươi[dairy]; Bột mì[wheat]; Dầu ô liu; Phô mai parmesan[dairy]; Nước dùng gà; Nhục đậu khấu · raw: water-packed artichoke hearts

### molluscs (1 món — in hết)
- **#2290 Cháo Hàu** · omnivore · `a` · nhãn: dairy, **molluscs**
  Hành lá; Hành tím; Tỏi; Ớt; Giá đỗ; Rau mùi; Sữa tươi[dairy]; Gạo tẻ; Gạo nếp; Dầu ăn; Muối; Rau răm; Nấm rơm · raw: hạt nêm; bột ngọt; tiêu

### soy (59 món)
- **#1828 thai spicy basil beef** · omnivore · `b-dau-hao` · nhãn: fish, molluscs, **soy**, wheat — nguyên liệu như ở mục wheat
- **#448 chocolate and nutella surprise muffins** · omnivore · `c-tu-khoa` · nhãn: dairy, egg, **soy**, **tree_nuts**, wheat
  Trứng gà[egg]; Sữa tươi[dairy]; Sữa chua[dairy]; Bơ[dairy]; Bột mì[wheat]; Đường; Bột nở; Muối nở; Vani; Bột cacao · raw: nutella
- **#1829 thai style pork in black pepper** · omnivore · `b-dau-hao` · nhãn: fish, molluscs, **soy**, wheat — nguyên liệu như ở mục wheat
- **#2020 Cá hồi ngũ sắc** · omnivore · `b-dau-hao` · nhãn: dairy, fish, molluscs, **soy**, **wheat**
  Khoai tây; Tỏi; Ớt chuông; Bông cải trắng; Thì là; Chanh; Cá hồi[fish]; Bơ[dairy]; Bột năng; Dầu ăn; Muối; Dầu hào[molluscs,soy,wheat] · raw: tiêu; hạt nêm aji ngon heo
- **#2084 Cua lột xào chua ngọt** · omnivore · `b-dau-hao` · nhãn: molluscs, shellfish, **soy**, wheat
  Cà chua; Hành lá; Tỏi; Gừng; Cua[shellfish]; Bột mì[wheat]; Dầu ăn; Đường; Muối; Dầu hào[molluscs,soy,wheat]; Giấm · raw: tiêu

### shellfish (2 món — in hết)
- **#2093 Ruốc chiên lá quế** · omnivore · `b-ruoc` · nhãn: egg, **shellfish**, wheat
  Xà lách; Cà chua; Dưa leo; Hành lá; Ớt; Dứa; Thịt heo xay; Trứng gà[egg]; Bột mì[wheat]; Dầu ăn; Quế; Xốt mayonnaise[egg]; Tương ớt · raw: ruốc biển; tiêu; hạt nêm aji ngon heo; bột ngọt aji no moto
- **#2110 Gà hon đậu phộng** · omnivore · `b-ruoc` · nhãn: fish, peanut, **shellfish**, wheat
  Hành lá; Tỏi; Sả; Ớt; Dứa; Gà nguyên con; Bánh mì[wheat]; Đậu phộng[peanut]; Dầu ăn; Đường; Nước mắm[fish]; Nghệ; Ngò gai; Rượu trắng; Cơm trắng · raw: mắm ruốc huế; bột ngọt aji no moto; hạt nêm aji ngon gà

### tree_nuts (7 món)
- **#167 barb s best zucchini bread** · omnivore · `c-tu-khoa` · nhãn: egg, **peanut**, **tree_nuts**, wheat
  Bí ngòi; Trứng gà[egg]; Bột mì[wheat]; Dầu ăn; Đường; Muối; Quế; Đinh hương; Bột nở; Muối nở; Vani; Nhục đậu khấu; Nho khô · raw: nuts
- **#448 chocolate and nutella surprise muffins** — như ở mục soy (raw: nutella)
- **#457 cinnamon coffee cake (kaffeekuchen)** · omnivore · `c-tu-khoa` · nhãn: dairy, egg, **peanut**, **tree_nuts**, wheat
  Trứng gà[egg]; Sữa tươi[dairy]; Bơ[dairy]; Bột mì[wheat]; Đường; Giấm; Quế; Bột nở; Muối nở · raw: nuts
- **#476 cocoa oatmeal muffins** · omnivore · `c-tu-khoa` · nhãn: dairy, egg, **peanut**, **tree_nuts**, wheat
  Trứng gà[egg]; Sữa tươi[dairy]; Bơ[dairy]; Bột mì[wheat]; Yến mạch; Đường; Muối; Bột nở; Vani; Bột cacao · raw: nuts
- **#556 crumb topped banana muffins** · omnivore · `c-tu-khoa` · nhãn: dairy, egg, **peanut**, **tree_nuts**, wheat
  Chuối; Trứng gà[egg]; Bơ[dairy]; Bột mì[wheat]; Đường; Đường nâu; Muối; Quế; Bột nở; Muối nở · raw: nuts

### sesame (1 món — in hết)
- **#1677 six layer mediterranean dip** · omnivore · `c-tu-khoa` · nhãn: dairy, **sesame**
  Cà chua; Dưa leo; Tỏi; Chanh vàng; Quả bơ; Sữa chua[dairy]; Muối; Thì là ai cập; Phô mai feta[dairy]; Ô liu đen · raw: hummus; salt & fresh ground pepper

### peanut (6 món)
- **#167, #457, #476, #556** — như ở mục tree_nuts (raw: nuts)
- **#936 high altitude zucchini bread** · omnivore · `c-tu-khoa` · nhãn: egg, **peanut**, **tree_nuts**, wheat
  Bí ngòi; Cam; Trứng gà[egg]; Bột mì[wheat]; Dầu ăn; Đường; Muối; Quế; Bột nở; Muối nở; Vani · raw: nuts

## 3. Điều thấy thêm khi đọc (ngoài phạm vi nhãn dị ứng — chưa sửa gì)

1. **3 món cá đang mang diet `vegetarian`:** #120 baked parmesan fish, #625 easy baked orange roughy,
   #1295 orange roughy with dill sauce. Nguyên nhân giống nhau: "orange roughy" (cá) bị map thành `Cam` (quả cam),
   nên khi seed không có nguyên liệu thịt/cá → món được xếp chay. Nhãn `fish` mới chặn được người dị ứng cá,
   nhưng **người ăn chay vẫn nhận được 3 món cá này**. Cần đổi `diet_type` → `omnivore` (và gỡ `Cam` nếu muốn) — chờ anh quyết.
2. **"bun" (bánh burger) bị map thành `Bún`** (bún gạo) ở các món burger (#19, #242, …) và #986 — đây là lý do các món
   này thiếu wheat. Nhãn mới đã bù, nhưng nguyên liệu vẫn sai (ảnh hưởng hiển thị và độ phủ khi tìm bằng bún).
3. **Cháo Hàu có `Sữa tươi[dairy]`** — cháo hàu thường không có sữa; khả năng cao tên gốc là "hàu sữa" bị map nhầm
   thành sữa. Hệ quả là lọc thừa (người dị ứng sữa không thấy món), không nguy hiểm. Ghi để anh biết.
4. `peanut` + `tree_nuts` cho các món chỉ ghi "nuts" là gắn bảo thủ (không rõ loại hạt) — đúng như đã chốt ở commit 1914c90.
5. `tortellini` → `egg` (#541, #1717, #1742, #1762): tortellini tươi/khô thương mại thường có trứng → hợp lý.

## Tóm tắt để anh duyệt

- Lọc trực tiếp: **15/16 ca đạt**; **#1041 vẫn lọt fish** vì bị sót khỏi `label-fixes.sql`.
- 9 loại có nhãn mới, mẫu ở mục 2: tôi đọc thấy nhãn hợp lý ở mọi món mẫu.
- Ngoài nhãn: 3 món cá xếp nhầm `vegetarian` (mục 3.1) là lỗi an toàn thực sự cho người ăn chay.

Chỉ báo cáo, chưa đổi gì trong DB hay mã. Chờ anh duyệt.
