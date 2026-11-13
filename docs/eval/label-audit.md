# Kiểm duyệt nhãn dị ứng (đọc bằng mắt)

Ngày 2026-11-13 · nhánh `feat/eval-phase1` · chỉ đọc (SELECT qua admin client), không sửa mã/DB, không gọi AI.

**Cơ chế lọc hiện tại:** `search_recipes` loại món có dòng trong `recipe_allergens` trùng slug người dùng khai.
`recipe_allergens` được tính lúc seed (`scripts/recipe_preparation.py`) = hợp nhãn của nguyên liệu đã map
(`ingredient_allergens`) ∪ dò từ khoá (`guess_allergen_ids`) trên tên gốc **không map được hoặc chỉ khớp mờ**.
Hệ quả: tên khớp chính xác qua alias chỉ nhận nhãn của nguyên liệu danh mục; tên gốc của phần đã map không được lưu
(`raw_ingredient_names` chỉ giữ phần chưa map), nên không đọc lại được "nước dùng" gốc là nước dùng gì.

**Số liệu:** 10 loại dị ứng · 232 nguyên liệu · 63 dòng `ingredient_allergens` · 3171 món · 5439 dòng `recipe_allergens`.
Kiểm nhất quán: 0 món có nguyên liệu mang nhãn X mà món lại thiếu nhãn X; 0 món có tên chưa map khớp từ khoá X mà thiếu nhãn X
→ lỗ hổng nằm ở **danh mục thiếu nhãn**, **từ khoá thiếu**, và **nguyên liệu bị rơi khi map** (xem mục 2 và Phụ lục).

## 1. Nguyên liệu đang mang nhãn (theo từng loại)

### shellfish — Giáp xác (tôm, cua) (4 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 114 | Cua | Crab | Crabmeat, Lump crabmeat | — |
| 168 | Mắm tôm | Shrimp paste | — | — |
| 113 | Tôm | Shrimp | Prawn | — |
| 184 | Tôm khô | Dried shrimp | — | — |

### molluscs — Nhuyễn thể (mực, nghêu, sò, hàu) (7 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 116 | Bạch tuộc | Octopus | — | — |
| 158 | Dầu hào | Oyster sauce | — | — |
| 119 | Hàu | Oyster | — | — |
| 115 | Mực | Squid | — | — |
| 117 | Nghêu | Clam | — | — |
| 120 | Sò điệp | Scallop | — | — |
| 118 | Vẹm | Mussel | — | — |

### fish — Cá (13 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 183 | Chả lụa | Vietnamese pork sausage | — | — |
| 109 | Cá chép | Carp | — | — |
| 112 | Cá cơm | Anchovy | — | — |
| 104 | Cá hồi | Salmon | — | — |
| 111 | Cá hồng | Snapper | — | — |
| 185 | Cá khô | Dried fish | — | — |
| 105 | Cá ngừ | Tuna | — | — |
| 108 | Cá rô phi | Tilapia | — | — |
| 106 | Cá thu | Mackerel | — | — |
| 107 | Cá tra | Catfish | Cá basa, Cá ba sa, Cá hú, Cá bông lau, Cá dứa, Cá trê | — |
| 110 | Cá tuyết | Cod | — | — |
| 157 | Nước mắm | Fish sauce | — | — |
| 193 | Xốt worcestershire | Worcestershire sauce | — | — |

### egg — Trứng (5 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 136 | Mì trứng | Egg noodles | — | wheat |
| 103 | Trứng cút | Quail egg | — | — |
| 101 | Trứng gà | Chicken egg | Trứng, Egg | — |
| 102 | Trứng vịt | Duck egg | — | — |
| 190 | Xốt mayonnaise | Mayonnaise | Mayonnaise | — |

### dairy — Sữa (17 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 123 | Bơ | Butter | — | — |
| 200 | Bơ thực vật | Margarine | — | — |
| 188 | Kem chua | Sour cream | — | — |
| 221 | Kem sữa half and half | Half and half | — | — |
| 126 | Kem tươi | Heavy cream | Kem whipping, Whipping cream, Heavy whipping cream | — |
| 124 | Phô mai cheddar | Cheddar | Phô mai, Cheese | — |
| 208 | Phô mai feta | Feta cheese | — | — |
| 196 | Phô mai kem | Cream cheese | — | — |
| 203 | Phô mai monterey jack | Monterey jack cheese | — | — |
| 125 | Phô mai mozzarella | Mozzarella | — | — |
| 186 | Phô mai parmesan | Parmesan | Parmesan cheese | — |
| 210 | Phô mai thụy sĩ | Swiss cheese | — | — |
| 211 | Súp kem nấm | Cream of mushroom soup | — | wheat |
| 205 | Sữa bơ | Buttermilk | — | — |
| 122 | Sữa chua | Yogurt | — | — |
| 121 | Sữa tươi | Whole milk | Sữa, Milk | — |
| 127 | Sữa đặc | Condensed milk | — | — |

### peanut — Đậu phộng (1 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 145 | Đậu phộng | Peanut | — | — |

### tree_nuts — Hạt cây (điều, óc chó, hồ đào) (3 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 146 | Hạt điều | Cashew | — | — |
| 213 | Hồ đào | Pecan | — | — |
| 212 | Quả óc chó | Walnut | — | — |

### soy — Đậu nành (3 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 156 | Nước tương | Soy sauce | Xì dầu | wheat |
| 141 | Đậu nành | Soybean | — | — |
| 140 | Đậu phụ | Tofu | Đậu hũ | — |

### wheat — Lúa mì (gluten) (8 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 138 | Bánh mì | White bread | — | — |
| 220 | Bánh tortilla | Flour tortilla | — | — |
| 207 | Bột chiên xù | Breadcrumbs | Bột xù, Dry breadcrumbs, Panko | — |
| 132 | Bột mì | Wheat flour | Flour, All-purpose flour, Bột mì đa dụng, Bột chiên giòn, Bột giòn | — |
| 136 | Mì trứng | Egg noodles | — | egg |
| 137 | Mì ý | Pasta | — | — |
| 156 | Nước tương | Soy sauce | Xì dầu | soy |
| 211 | Súp kem nấm | Cream of mushroom soup | — | dairy |

### sesame — Mè (2 nguyên liệu)

| id | Tên | Tên EN | Alias | Nhãn khác |
|---|---|---|---|---|
| 150 | Dầu mè | Sesame oil | — | — |
| 147 | Mè | Sesame | — | — |

## 2. Nguyên liệu có thể chứa chất gây dị ứng nhưng KHÔNG có nhãn đó

Mức: **Cao** = thành phần phổ biến của loại sản phẩm này; **TB** = tuỳ hãng/công thức, khá thường gặp;
**Thấp** = hiếm, ghi để anh quyết. "Số món" = số món trong DB dùng nguyên liệu đó (`recipe_ingredients`).
Thành phần sản phẩm thương mại là nhận định chung, cần đọc nhãn hãng cụ thể trước khi chốt.

### 2a. Nguyên liệu trong danh mục (232 dòng)

#### wheat — Lúa mì (gluten)
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước dùng gà (192), alias `Nước dùng`, `Chicken stock`, `Nước hầm gà` | 164 | Cao | Nước dùng/viên súp đóng hộp thường có bột mì, maltodextrin lúa mì, protein thuỷ phân. Alias chung `Nước dùng` gom mọi loại nước dùng về đây |
| Bột cà ri (165) | 29 | TB | Một số bột/viên cà ri trộn bột mì làm chất độn/làm sệt |
| Bột nở (187) | 268 | Thấp–TB | Một số hãng dùng tinh bột lúa mì làm chất độn (đa số dùng tinh bột bắp) |
| Yến mạch (139) | 7 | TB (tuỳ định nghĩa) | Slug ghi "Lúa mì (gluten)"; yến mạch thường nhiễm chéo gluten và có avenin. Nếu wheat = gluten thì nên gắn |
| Xốt worcestershire (193) | 93 | Thấp | Một số hãng dùng giấm mạch nha (lúa mạch, có gluten) |
| Giăm bông (214), Thịt xông khói (194) | 40, 143 | Thấp | Thịt chế biến đôi khi có tinh bột/chất độn từ lúa mì |
| Ớt bột (164) — EN "Chili powder" (hỗn hợp kiểu Mỹ) | 147 | Thấp | Hỗn hợp gia vị có thể có chất chống vón/chất độn |
| Dầu hào (158) — đã có nhãn molluscs | 106 | Cao | Dầu hào phổ biến (vd. Lee Kum Kee Panda) có bột mì/tinh bột lúa mì → **thiếu nhãn wheat** |

#### soy — Đậu nành
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước dùng gà (192) | 164 | TB | Viên/bột súp thường có protein đậu nành thuỷ phân |
| Dầu hào (158) — đã có nhãn molluscs | 106 | TB | Nhiều hãng thêm nước tương |
| Giăm bông (214), Thịt xông khói (194) | 40, 143 | Thấp–TB | Đạm đậu nành/lecithin trong thịt chế biến |
| Bánh mì (138) — đã có nhãn wheat | 83 | TB | Bánh mì công nghiệp thường có bột đậu nành/lecithin trong chất cải thiện bột |
| Bột chiên xù (207) — đã có nhãn wheat | 119 | Thấp–TB | Một số loại có dầu/bột đậu nành |
| Chả lụa (183) — đã có nhãn fish | 10 | Thấp | Chả lụa thương mại đôi khi có đạm đậu nành |
| Dầu ăn (148), alias `Dầu thực vật` | 930 | Thấp | Thường là dầu đậu nành tinh luyện — nhiều quy định miễn ghi nhãn với dầu tinh luyện |
| Giá đỗ (33) | 29 | Thấp | Thường là giá đậu xanh, nhưng có "giá đậu nành" |

#### dairy — Sữa
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước dùng gà (192) | 164 | Thấp–TB | Một số viên súp/nước dùng có bột sữa, whey |
| Bánh mì (138) — đã có nhãn wheat | 83 | TB | Bánh mì sandwich/gối thường có sữa bột, bơ |
| Bột chiên xù (207) — đã có nhãn wheat | 119 | Thấp–TB | Một số loại panko/vụn bánh có sữa |
| Giăm bông (214) | 40 | Thấp | Lactose/đạm sữa trong một số loại giăm bông |
| Bột cà ri (165) | 29 | Thấp | Viên cà ri kiểu Nhật/Thái có thể có bột sữa |
| Rượu vang trắng (209) | 79 | Thấp | Có thể lọc trong bằng casein; thường không ghi nhãn ở VN |
| *(ngược lại)* Bơ thực vật (200) đang mang nhãn dairy | 50 | — | Không phải lọt: nhiều margarine không có sữa → nhãn hiện tại có thể **lọc thừa**. Ghi để anh quyết |

#### egg — Trứng
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Mì ý (137) — đã có nhãn wheat | 61 | Thấp–TB | Mì ý khô thường không trứng, nhưng mì tươi / lasagna tươi / tortellini có trứng |
| Bánh mì (138) — đã có nhãn wheat | 83 | Thấp | Một số loại bánh mì ngọt/brioche có trứng, quét trứng mặt bánh |
| Bột chiên xù (207) | 119 | Thấp | Ít gặp |
| Bột mì (132) — alias `Bột chiên giòn`, `Bột giòn` | 804 | Thấp–TB | Alias gom bột chiên giòn (sản phẩm hỗn hợp) vào bột mì; một số bột chiên giòn/tempura có bột trứng |
| Rượu vang trắng (209) | 79 | Thấp | Có thể lọc trong bằng lòng trắng trứng |
| Nước dùng gà (192) | 164 | Thấp | Hiếm |

#### fish — Cá
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước dùng gà (192), alias `Nước dùng` | 164 | TB | Alias chung `Nước dùng` khớp chính xác → món dùng "nước dùng cá/nước dùng hải sản/dashi" bị map về nước dùng gà mà không có nhãn. Tên gốc không còn lưu nên không xác nhận được bao nhiêu ca |
| Xốt salsa (206) | 22 | Thấp | Không — ghi để loại trừ |
| Tương ớt (222) | 145 | Thấp | Một số tương ớt kiểu Thái/Hàn có nước mắm |

#### shellfish — Giáp xác
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước dùng gà (192), alias `Nước dùng` | 164 | TB | Như trên: nước dùng tôm/hải sản sẽ map về đây |
| Tương ớt (222) | 145 | Thấp | Một số tương ớt (sa tế tôm, XO) có tôm khô |
| *(không phải danh mục — xem 2b)* `mắm ruốc huế`, `ruốc biển` | 2 món | Cao | Ruốc = moi/tép biển; chỉ nhận nhãn fish qua từ khoá "mắm" |

#### molluscs — Nhuyễn thể
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước dùng gà (192), alias `Nước dùng` | 164 | Thấp | Nước dùng nghêu/sò cũng map về đây |
| Tương ớt (222) | 145 | Thấp | Xốt XO có sò điệp khô |

#### peanut — Đậu phộng
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Dầu ăn (148), alias `Dầu thực vật` | 930 | Thấp | Dầu thực vật ở VN có thể là dầu phộng (dầu tinh luyện thường được miễn). Lưu ý alias `Dầu điều` ở đây là dầu hạt điều màu (annatto), không phải hạt điều — đúng, nhưng dễ đọc nhầm |
| Tương ớt (222), Bột cà ri (165) | 145, 29 | Thấp | Sa tế/cà ri kiểu Thái/Mã có thể có đậu phộng |

#### tree_nuts — Hạt cây
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Nước cốt dừa (67), Nước dừa (68), Cơm dừa (66) | 74, 41, 5 | Tuỳ định nghĩa | Dừa từng nằm trong danh sách tree nut của FDA (Mỹ đã bỏ từ 2025; EU/Codex không tính). Cần anh chốt có coi dừa là tree_nuts không |
| Bột cà ri (165) | 29 | Thấp | Một số cà ri có hạt điều/hạnh nhân xay |

#### sesame — Mè
| Nguyên liệu (id) | Số món | Mức | Lý do |
|---|---|---|---|
| Bánh mì (138) — đã có nhãn wheat | 83 | Thấp–TB | Bánh hamburger/bánh mì rắc mè; nhiễm chéo ở lò bánh |
| Tương ớt (222) | 145 | Thấp | Một số tương ớt Hàn/Trung có dầu mè |
| Bột cà ri (165) | 29 | Thấp | Hiếm |

**Ngoài 10 loại đang theo dõi:** Mù tạt (197, 178 món) và Cần tây (40) là chất gây dị ứng theo EU nhưng không có slug;
Mayonnaise thường có mù tạt. Ghi để anh biết, không đề xuất thêm.

### 2b. Tên gốc chưa map (`raw_ingredient_names`) — không có nhãn tương ứng

Đếm số lần xuất hiện trong các món **không** mang nhãn đó.

| Tên gốc | Lần | Loại có thể thiếu | Mức | Lý do |
|---|---|---|---|---|
| `hạt nêm` (+ `aji ngon heo/gà/nấm`, `maggi`, `knorr`, `vedan`, `hạt nêm chay knorr nấm hương`) | ~480 | wheat, soy, dairy | TB | Hạt nêm là gia vị hỗn hợp; tuỳ hãng có tinh bột/protein thuỷ phân lúa mì–đậu nành, bột sữa. Không có từ khoá nào khớp nên **không món nào nhận nhãn**. Cần đọc nhãn Aji-ngon / Knorr / Maggi |
| `bột canh` | 14–17 | wheat, soy | Thấp–TB | Tuỳ hãng |
| `bột ngọt` / `aji no moto` | ~200 | — | Không | Mononatri glutamat tinh khiết |
| `macaroni`, `elbow macaroni`, `spaghetti`, `penne`, `linguine` | 7 | wheat (egg nếu mì tươi) | **Cao** | `guess_allergen_ids` có "pasta", "noodle" nhưng không có tên các loại mì cụ thể → **lọt wheat thật** (vd. #1581, #538, #1496, #1247) |
| `seasoned croutons`, `crouton`, `ritz cracker`, `rolls` | 4 | wheat (+dairy) | **Cao** | Bánh mì/bánh quy; từ khoá có "bread" nhưng không có các tên này |
| `bột bánh bao` | 1 | wheat | **Cao** | Bột bánh bao là bột mì |
| `bột bánh xèo cốt dừa taky` | 1 | wheat?, tree_nuts? (dừa) | Thấp | Chủ yếu bột gạo; cần nhãn hãng |
| `mắm ruốc huế`, `ruốc biển` | 2 | shellfish | **Cao** | Ruốc = tép/moi biển; chỉ dính fish qua "mắm" |
| `nuts` | 6 | tree_nuts (+peanut) | **Cao** | Hạt không rõ loại; từ khoá không có "nut" chung |
| `nutella` | 1 | tree_nuts, dairy | **Cao** | Hạt phỉ + sữa |
| `hummus` | 1 | sesame | **Cao** | Có tahini |
| `xốt thịt ngũ vị`, `xốt sườn xào chua ngọt`, `xốt canh chua` (Barona) | 4 | soy, wheat, fish? | TB | Xốt nêm sẵn thường có nước tương, nước mắm; cần nhãn hãng |
| `taco / cajun / creole / italian / spike seasoning`, `old bay seasoning` | ~10 | wheat, soy, dairy | Thấp | Hỗn hợp gia vị Mỹ, đa số không có, vài hãng có bột mì/whey |
| `nước mắm chay` | 3 | soy (và đang **thừa** fish) | Thấp | Nước mắm chay thường từ đậu nành/nấm; từ khoá "mắm" gắn fish sai |
| `dừa nạo`, `dừa`, `dầu dừa`, `nước cốt dừa lon`, `unsweetened flaked coconut` | 7 | tree_nuts | Tuỳ định nghĩa | Như dừa ở 2a |

## 3. Mẫu 5 món KHÔNG bị lọc cho từng loại

Chọn ngẫu nhiên (seed `20261113`) trong các món không có nhãn đó ở `recipe_allergens` (= không bị `search_recipes` lọc). Mỗi món: nguyên liệu đã map (kèm nhãn của chính nguyên liệu, `(tuỳ chọn)` nếu is_optional) và tên gốc không map được (`raw_ingredient_names`, lưu nguyên văn nguồn).

### shellfish — Giáp xác (tôm, cua) (không bị lọc: 2911/3171 món)

**#750 fried mushrooms** · vegetarian · Food.com · nhãn món: dairy, egg, wheat

- Bơ [dairy]
- Bột chiên xù [wheat]
- Hành tây
- Húng quế
- Nấm mỡ
- Trứng gà [egg]
- *(chưa map)* salt and pepper

**#78 avocado stuffed eggs** · vegetarian · Food.com · nhãn món: egg

- Bột paprika
- Chanh vàng
- Hành tây
- Muối
- Quả bơ
- Trứng gà [egg]
- Ô liu đen

**#550 crispy oven fried cod** · omnivore · Food.com · nhãn món: egg, fish, wheat

- Bột chiên xù [wheat]
- Bột ngô vàng
- Cá tuyết [fish]
- Dầu ăn
- Muối
- Trứng gà [egg]
- Ớt cayenne

**#1525 roast potatoes with olives** · vegan · Food.com · nhãn món: —

- Bột paprika
- Dầu ô liu
- Khoai tây
- Muối
- Mùi tây
- Tỏi
- Ô liu đen
- *(chưa map)* pepper

**#2816 Nước Mắm Tỏi Ớt Chua Ngọt** · omnivore · ViFoodRec (verified) · nhãn món: fish

- Chanh
- Nước mắm [fish]
- Tỏi
- Đường
- Ớt
- *(chưa map)* nước ấm

### molluscs — Nhuyễn thể (mực, nghêu, sò, hàu) (không bị lọc: 2991/3171 món)

**#40 amish pickled eggs and beets** · vegetarian · Food.com · nhãn món: egg

- Củ dền
- Giấm
- Muối
- Trứng gà [egg]
- Đường nâu

**#1902 tuna and spinach tortellini salad** · omnivore · Food.com · nhãn món: dairy, fish

- Chanh vàng
- Cá ngừ [fish]
- Dầu ô liu
- Phô mai cheddar [dairy]
- Rau chân vịt
- Ớt chuông
- *(chưa map)* salt and pepper

**#271 breakfast potatoes** · vegetarian · Food.com · nhãn món: dairy

- Bơ [dairy]
- Bột paprika
- Hành tây
- Khoai tây
- Muối
- *(chưa map)* water

**#2171 Bánh đúc tôm thịt** · omnivore · ViFoodRec (verified) · nhãn món: fish, shellfish

- Bột gạo
- Chanh
- Củ đậu
- Dầu ăn
- Hành lá
- Hành tím
- Nước cốt dừa
- Nước dừa
- Nước mắm [fish]
- Rau mùi
- Thịt nạc vai heo
- Tôm khô [shellfish]
- Tỏi
- Đường
- Ớt
- *(chưa map)* hạt nêm aji ngon heo

**#549 crispy ginger beef** · omnivore · Food.com · nhãn món: egg, sesame, soy, wheat

- Bột bắp
- Cà rốt
- Dầu mè [sesame]
- Dầu ăn
- Giấm
- Gừng
- Hành lá
- Nước tương [soy, wheat]
- Nạm bò
- Trứng gà [egg]
- Tỏi
- Đường
- Ớt cayenne
- *(chưa map)* water

### fish — Cá (không bị lọc: 2564/3171 món)

**#439 chili s chicken crispers** · omnivore · Food.com · nhãn món: dairy, egg, wheat

- Bột mì [wheat]
- Dầu ăn
- Gà nguyên con
- Muối
- Nước dùng gà
- Sữa tươi [dairy]
- Tiêu đen
- Trứng gà [egg]

**#231 blasted broccoli** · vegan · Food.com · nhãn món: —

- Bông cải xanh
- Dầu ô liu
- Giấm
- *(chưa map)* sea salt

**#1804 sweetie pie s mac and cheese** · omnivore · Food.com · nhãn món: dairy, egg

- Bơ [dairy]
- Kem chua [dairy]
- Muối
- Phô mai cheddar [dairy]
- Phô mai monterey jack [dairy]
- Sữa tươi [dairy]
- Trứng gà [egg]
- Đường
- *(chưa map)* cooked elbow macaroni
- *(chưa map)* pepper

**#247 blueberry banana pancakes** · omnivore · Food.com · nhãn món: dairy, egg, wheat

- Bột mì [wheat]
- Bột nở
- Chuối
- Dầu ăn
- Giấm
- Muối
- Muối nở
- Nhục đậu khấu
- Sữa tươi [dairy]
- Trứng gà [egg]
- Đường
- *(chưa map)* blueberries

**#2740 Màn Thầu Chay Đơn Giản** · vegan · ViFoodRec (verified) · nhãn món: wheat

- Bột mì [wheat]
- Bột nở
- Men nở
- *(chưa map)* nước

### egg — Trứng (không bị lọc: 2276/3171 món)

**#694 farfalle con pollo e spinaci** · omnivore · Food.com · nhãn món: dairy, wheat

- Bột mì [wheat]
- Dầu ô liu
- Hành tím
- Muối
- Mì ý [wheat]
- Nước dùng gà
- Nấm mỡ
- Phô mai cheddar [dairy]
- Rau chân vịt
- Rượu vang trắng
- Tỏi
- Ớt
- Ức gà

**#1824 tgi friday s baked potato skins** · omnivore · Food.com · nhãn món: dairy

- Bơ [dairy]
- Hành lá
- Khoai tây
- Muối
- Phô mai cheddar [dairy]
- Thịt xông khói

**#193 beet greens with bacon and onion** · omnivore · Food.com · nhãn món: —

- Củ dền
- Dầu ô liu
- Hành tây
- Muối
- Rượu vang trắng
- Thịt xông khói
- Tỏi
- *(chưa map)* fresh ground black pepper

**#1785 summertime chicken tacos** · omnivore · Food.com · nhãn món: dairy, wheat

- Bánh tortilla [wheat]
- Chanh
- Cà chua
- Dầu ô liu
- Lá oregano
- Muối
- Mùi tây
- Phô mai cheddar [dairy]
- Thì là ai cập
- Tỏi
- Xà lách
- Ức gà
- *(chưa map)* pepper

**#2864 Bánh Bột Lọc Nhân Đậu Xanh** · omnivore · ViFoodRec (verified) · nhãn món: soy, wheat

- Bột gạo
- Bột năng
- Dầu ăn
- Hành lá
- Muối
- Nước tương [soy, wheat]
- Đường
- Đậu xanh
- Ớt
- *(chưa map)* hạt nêm

### dairy — Sữa (không bị lọc: 1732/3171 món)

**#75 avocado blt club** · omnivore · Food.com · nhãn món: egg, wheat

- Bánh mì [wheat]
- Cà chua
- Quả bơ
- Thịt xông khói
- Xà lách
- Xốt mayonnaise [egg]
- *(chưa map)* salt and pepper

**#2675 Trứng Gà Nướng Thái Lan** · omnivore · ViFoodRec (verified) · nhãn món: egg, fish

- Muối
- Mật ong
- Nước mắm [fish]
- Trứng gà [egg]
- Đường
- *(chưa map)* tiêu

**#2738 Chả Cá Chiên Thơm Dai** · omnivore · ViFoodRec (verified) · nhãn món: fish

- Bột năng
- Bột nở
- Cá rô phi [fish]
- Dầu ăn
- Hành lá
- Muối
- Nghệ
- Nước mắm [fish]
- Thịt heo xay
- Đường

**#2905 Bánh Bí Đỏ Lạng Sơn** · omnivore · ViFoodRec (verified) · nhãn món: —

- Bí đỏ
- Bột gạo
- Dầu ăn
- Hành lá
- Muối
- Thịt ba chỉ
- *(chưa map)* bột ngọt
- *(chưa map)* tiêu

**#2755 Cải Thìa Xào Dầu Hào Thơm Ngon** · omnivore · ViFoodRec (verified) · nhãn món: molluscs

- Cải thìa
- Dầu hào [molluscs]
- Dầu ăn
- Muối
- Tỏi

### peanut — Đậu phộng (không bị lọc: 3105/3171 món)

**#1250 n  y  c  irish soda bread** · vegetarian · Food.com · nhãn món: dairy, egg, wheat

- Bơ [dairy]
- Bột mì [wheat]
- Bột nở
- Muối
- Muối nở
- Nho khô
- Sữa bơ [dairy]
- Trứng gà [egg]
- Đường nâu

**#2079 Cá hồi chiên xốt xoài** · omnivore · ViFoodRec (verified) · nhãn món: egg, fish, wheat

- Bột mì [wheat]
- Chanh
- Cà chua
- Cá hồi [fish]
- Dưa leo
- Dầu ăn
- Muối
- Nước mắm [fish]
- Xoài
- Xốt mayonnaise [egg]
- Đường
- Ớt
- *(chưa map)* salad
- *(chưa map)* tiêu

**#2925 Bánh Bèo Đà Nẵng** · omnivore · ViFoodRec (verified) · nhãn món: fish, shellfish

- Bột gạo
- Bột năng
- Chanh
- Dầu ăn
- Hành lá
- Hành tím
- Nước mắm [fish]
- Thịt heo xay
- Tôm [shellfish]
- Tỏi
- Đường
- *(chưa map)* tiêu
- *(chưa map)* hạt nêm

**#1787 sun dried tomato  basil and black pepper scones** · omnivore · Food.com · nhãn món: dairy, egg, wheat

- Bơ [dairy]
- Bột mì [wheat]
- Bột nở
- Dầu ô liu
- Húng quế
- Muối
- Mùi tây
- Sữa tươi [dairy]
- Tiêu đen
- Trứng gà [egg]
- Đường
- *(chưa map)* sun-dried tomato packed in oil

**#1078 lamb chops rosemary** · omnivore · Food.com · nhãn món: —

- Cà chua
- Hành tây
- Hương thảo
- Muối
- Thịt cừu
- Ớt chuông

### tree_nuts — Hạt cây (điều, óc chó, hồ đào) (không bị lọc: 3086/3171 món)

**#207 best ever bbq chicken** · omnivore · Food.com · nhãn món: dairy, fish

- Bơ [dairy]
- Cần tây
- Muối
- Mù tạt
- Tương cà
- Tương ớt
- Tỏi
- Xốt worcestershire [fish]
- Đường nâu
- Ớt
- Ức gà

**#2076 Sườn non rim củ nén** · omnivore · ViFoodRec (verified) · nhãn món: fish, sesame

- Cà chua
- Cơm trắng
- Dưa leo
- Dầu ăn
- Mè [sesame]
- Nước dừa
- Nước mắm [fish]
- Rau răm
- Sườn heo
- Tiêu đen
- Đường
- Ớt
- *(chưa map)* củ nén lột sạch vỏ
- *(chưa map)* hạt nêm aji ngon heo
- *(chưa map)* bột ngọt aji no moto

**#1672 simply sour cream chicken enchiladas** · omnivore · Food.com · nhãn món: dairy, wheat

- Bánh tortilla [wheat]
- Bơ [dairy]
- Bột mì [wheat]
- Dầu ăn
- Hành tây
- Kem chua [dairy]
- Nước dùng gà
- Phô mai monterey jack [dairy]
- Ức gà
- *(chưa map)* green chilies

**#1415 pork chop   o brien potato bake** · omnivore · Food.com · nhãn món: dairy

- Cần tây
- Hành tây
- Kem chua [dairy]
- Khoai tây
- Muối
- Phô mai cheddar [dairy]
- Sữa tươi [dairy]
- Thịt nạc vai heo
- *(chưa map)* pepper

**#2887 Bánh Bông Lan Siêu Mềm** · vegetarian · ViFoodRec (verified) · nhãn món: dairy, egg, wheat

- Bắp
- Bột mì [wheat]
- Chanh
- Muối
- Sữa tươi [dairy]
- Trứng gà [egg]
- Đường

### soy — Đậu nành (không bị lọc: 2794/3171 món)

**#1255 nanna s gnocchi** · vegetarian · Food.com · nhãn món: egg, wheat

- Bột mì [wheat]
- Khoai tây
- Nhục đậu khấu
- Trứng gà [egg]
- *(chưa map)* salt and pepper

**#585 danish bubble** · omnivore · Food.com · nhãn món: dairy, egg, fish

- Dầu ăn
- Hành tây
- Hẹ
- Khoai tây
- Phô mai cheddar [dairy]
- Thịt bò đùi
- Thịt xông khói
- Trứng gà [egg]
- Xốt worcestershire [fish]
- *(chưa map)* salt and pepper

**#726 freakin  good guacamole** · vegan · Food.com · nhãn món: —

- Chanh
- Cà chua
- Quả bơ
- Rau mùi
- Xốt salsa
- *(chưa map)* salt and pepper

**#317 buttered spinach** · vegetarian · Food.com · nhãn món: dairy

- Bơ [dairy]
- Chanh vàng
- Muối
- Rau chân vịt
- *(chưa map)* pepper

**#1569 roasted tomatoes onions and zucchini** · vegan · Food.com · nhãn món: —

- Bí ngòi
- Cà chua
- Cỏ xạ hương
- Dầu ô liu
- Hành tây
- Tỏi
- *(chưa map)* salt and pepper

### wheat — Lúa mì (gluten) (không bị lọc: 1836/3171 món)

**#1788 super easy honey curry chicken** · omnivore · Food.com · nhãn món: dairy

- Bơ [dairy]
- Bột cà ri
- Muối
- Mù tạt
- Mật ong
- Đùi gà

**#2695 Chả Đậu Xanh Chay** · omnivore · ViFoodRec (verified) · nhãn món: —

- Bột gạo
- Dầu ăn
- Muối
- Đường
- Đậu xanh
- *(chưa map)* hạt nêm chay
- *(chưa map)* tiêu

**#2837 Cơm Gà Xối Mỡ** · omnivore · ViFoodRec (verified) · nhãn món: egg

- Cà chua
- Cơm trắng
- Dưa leo
- Dầu ăn
- Hành lá
- Muối
- Nghệ
- Rau mùi
- Trứng gà [egg]
- Tỏi
- Xà lách
- Đùi gà
- Đường
- *(chưa map)* hạt nêm
- *(chưa map)* nước

**#1507 red potatoes with butter and chives** · vegetarian · Food.com · nhãn món: dairy

- Bơ [dairy]
- Hẹ
- Khoai tây
- *(chưa map)* salt and pepper

**#1073 kree s delicious apple pork chops** · omnivore · Food.com · nhãn món: —

- Dầu ăn
- Muối
- Quế
- Thịt nạc vai heo
- Táo
- Đường nâu
- *(chưa map)* ground black pepper
- *(chưa map)* hot water

### sesame — Mè (không bị lọc: 2976/3171 món)

**#1684 slovak cucumbers in sour cream** · vegetarian · Food.com · nhãn món: dairy

- Bột paprika
- Dưa leo
- Giấm
- Hành tây
- Kem chua [dairy]
- Muối
- Tỏi

**#1335 overnight french toast casserole** · vegetarian · Food.com · nhãn món: dairy, egg, wheat

- Bánh mì [wheat]
- Bơ [dairy]
- Quế
- Sữa tươi [dairy]
- Trứng gà [egg]
- Đường nâu

**#2264 Ruốc Tôm Khô** · omnivore · ViFoodRec (verified) · nhãn món: dairy, fish, shellfish

- Bơ thực vật [dairy]
- Nước mắm [fish]
- Tôm khô [shellfish]
- Đường
- *(chưa map)* hạt nêm

**#215 best ever grilled chicken kebabs** · omnivore · Food.com · nhãn món: —

- Chanh vàng
- Cà chua
- Dầu ô liu
- Hành tây
- Húng quế
- Hương thảo
- Lá oregano
- Muối
- Tỏi
- Ức gà
- *(chưa map)* red peppers

**#2231 Bánh Mì Nướng Tôm Phô Mai** · omnivore · ViFoodRec (verified) · nhãn món: dairy, shellfish, wheat

- Bánh mì [wheat]
- Bông cải xanh
- Bơ thực vật [dairy]
- Chanh
- Cà chua
- Mùi tây
- Nấm mỡ
- Sữa tươi [dairy]
- Tôm [shellfish]
- Tỏi
- Ớt bột
- *(chưa map)* phô mai con bò cười

## Phụ lục — món lọt do nguyên liệu bị rơi khi map

Rà tên món bằng chính `guess_allergen_ids` trên các món thiếu nhãn tương ứng, rồi đọc tay từng món. Các ca dưới đây
có tên món chỉ rõ chất gây dị ứng nhưng nguyên liệu đó **không có** trong `recipe_ingredients` lẫn `raw_ingredient_names`
(hoặc bị map sai) → món không bị lọc.

| Món | Thiếu nhãn | Nguyên liệu hiện có (rút gọn) | Vấn đề |
|---|---|---|---|
| #2290 Cháo Hàu | molluscs | gạo, sữa tươi, nấm rơm, giá… | Hàu — nguyên liệu chính — không có |
| #120 baked parmesan fish | fish | **Cam**, trứng, sữa, bột mì, parmesan | Có "Cam" (orange) — khả năng cao "orange roughy" (cá) bị map nhầm thành quả cam |
| #1041 egg or tuna and olive salad sandwiches | fish | trứng, bánh mì, mayonnaise… | Không có cá ngừ (món cho chọn trứng hoặc cá ngừ) |
| #2468 Khoai Tây Nghiền Với Trứng Và Thịt Muối | egg | khoai tây, sữa, bơ, thịt xông khói | Không có trứng |
| #2374 Đậu Hũ Chiên Sốt Mayonnaise | egg | đậu phụ, chanh, dầu, đường | Không có mayonnaise |
| #2521 Bánh Mì Chảo Sườn Kho Ốp La | wheat | sườn, trứng, nước mắm, dầu hào… | Không có bánh mì |
| #2588 Bánh Mì Xíu Mại Trứng Muối | wheat | thịt heo xay, trứng, dầu hào… | Không có bánh mì |
| #1902 tuna and spinach tortellini salad | wheat, egg | cá ngừ, rau chân vịt, phô mai… | Không có tortellini |
| #1581 salmon and pasta salad · #538 creamy pumpkin pasta · #1496 mamacello pasta · #1247 minestra with pasta | wheat | — | Mì nằm trong `raw_ingredient_names` (`macaroni`/`penne`/`spaghetti`) nhưng từ khoá không bắt |

Rà theo tên món cho ra 7–20 ứng viên mỗi loại, phần còn lại là dương tính giả (mực chay, nấm sò, bánh mì xoắn ốc,
vú sữa heo, salad bơ = quả bơ, pasta sauce chỉ là xốt…). Rà bằng tên món chỉ bắt được ca tên món nói rõ — số ca rơi nguyên liệu thật
có thể nhiều hơn.

## Tóm tắt để anh duyệt

1. **Danh mục:** ứng viên gắn thêm nhãn mạnh nhất là `Dầu hào` +wheat (+soy), `Nước dùng gà` (wheat/soy, và alias chung `Nước dùng`
   đang gom cả nước dùng cá/tôm), `Bánh mì` +soy/dairy. Hai việc anh cần chốt: dừa có tính là tree_nuts không, yến mạch có tính là wheat (gluten) không.
2. **Từ khoá `guess_allergen_ids`:** thiếu tên mì cụ thể (macaroni, spaghetti, penne, linguine, tortellini…), crouton/cracker/roll,
   bột bánh bao, ruốc (shellfish), `nuts`/nutella, hummus/tahini (có "tahini" nhưng không có "hummus"); `hạt nêm` (~480 lần) chưa có quyết định.
3. **Dữ liệu món:** ít nhất 9 món mất nguyên liệu mang dị ứng khi seed (Phụ lục), có 1 ca map nhầm cá → quả cam.

Báo cáo chỉ đọc, chưa đổi gì. Chờ anh duyệt.
