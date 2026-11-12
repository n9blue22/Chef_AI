# Kết quả kỳ vọng của `label-fixes.sql`

Ngày 2026-11-13. Đếm trên bản dump chỉ-đọc cùng ngày (3171 món, 5439 dòng `recipe_allergens`). Chỉ đếm cặp món–nhãn
**chưa có** trong DB, nên số dòng thêm = số dòng rollback xoá. Một cặp thuộc nhiều thay đổi thì tính cho thay đổi đầu tiên
theo thứ tự a → b → c. Ví dụ: 2 món bánh mì có dầu hào nhận `wheat` ở (a), không tính lại ở (b).

## Tổng

| Thay đổi | Dòng thêm | Món bị ảnh hưởng | Trong đó món đã kiểm duyệt | Theo nhãn |
|---|---|---|---|---|
| (a) nhãn trực tiếp theo rà tên món / nguồn | 40 | 34 | 6 | wheat 25, egg 9, fish 5, molluscs 1 |
| (b) `Dầu hào` +wheat +soy, lan xuống món | 107 + 2 nhãn nguyên liệu | 60 / 106 món dùng dầu hào | 58 | soy 58, wheat 49 (51 nếu không trừ 2 món ở (a)) |
| (b) `mắm ruốc` / `ruốc biển` +shellfish | 2 | 2 | 2 | shellfish 2 |
| (c) từ khoá mới | 35 | 28 | 1 | wheat 20, tree_nuts 7, peanut 6, soy 1, sesame 1 |
| **Cộng** | **184** (+2) | **122 món khác nhau** | | |

Không có cặp nào thuộc `dairy`: nutella chỉ thêm `tree_nuts` và `soy`, vì món #448 đã có nhãn `dairy`. 6 cặp `peanut` (thêm 2026-11-13 sau khi anh duyệt) đều mới: cả 6 món chưa mang `peanut` lúc dump. Số món mang `peanut` tăng từ 66 lên 72. 6 món này đã nằm trong 28 món của (c), nên tổng số món bị ảnh hưởng vẫn là 122.

## (a) Nhãn trực tiếp: 34 món

Gồm 7 ca ở phụ lục `label-audit.md` cộng các món cùng loại. Khi kiểm từng món, phần lớn ca lọt hoá ra **có trong nguồn
nhưng bị map sai hoặc rơi** (cột "Căn cứ"). Chỉ 6 ca dựa vào tên món, vì nguồn không liệt kê nguyên liệu đó.

| Món | Thêm | Căn cứ |
|---|---|---|
| #2290 Cháo Hàu | molluscs | nguồn có `hào sữa` (hàu) nhưng bị map thành **Sữa tươi** |
| #120 baked parmesan fish | fish | nguồn `orange roughy fillets` bị map thành **Cam** |
| #625 easy baked orange roughy, #1295 orange roughy with dill sauce | fish | `orange roughy fillets` |
| #899 haddock supreme | fish | `haddock fillets` |
| #1339 pan sauted chilean sea bass | fish | `sea bass fillets` |
| #1902, #541, #1271, #1717, #1742, #1890 (tortellini) | wheat, egg | `cheese tortellini` |
| #1762 spinach artichoke cheesy tortellini | egg (đã có wheat) | `cheese tortellini` |
| #19, #242, #379, #495, #732, #986, #1254 (burger, sloppy joes, sandwich) | wheat | `hamburger bun(s)` |
| #1428 portabella and gouda burger | wheat | `rolls` |
| #380 cheddar bay biscuits | wheat | `bisquick` / `buttermilk biscuit mix` |
| #414 chicken fajita pizza | wheat | `pizza dough` |
| #1675 siu mai dumplings | wheat | `wonton wrappers` |
| #2158 Súp hoành thánh | wheat | `lá hoành thánh` |
| #1282, #1284 (gnocchi) | wheat | `gnocchi` |
| #1755 spinach mushroom cheesy quiche | wheat | `pie crust` |
| #2521 Bánh Mì Chảo Sườn Kho Ốp La, #2588 Bánh Mì Xíu Mại Trứng Muối | wheat | tên món: nguồn không liệt kê bánh mì |
| #2374 Đậu Hũ Chiên Sốt Mayonnaise | egg | tên món: nguồn không liệt kê mayonnaise |
| #2468 Khoai Tây Nghiền Với Trứng Và Thịt Muối | egg | tên món: nguồn không có trứng |
| #1398 pioneer woman lasagna | wheat | tên món: nguồn không liệt kê lá lasagna |
| #1687 smoked turkey avocado brie sandwiches | wheat | tên món: nguồn không liệt kê bánh mì |

### Ứng viên độ tin cậy thấp: KHÔNG áp dụng, chờ anh duyệt

| Món | Có thể thiếu | Vì sao chưa áp |
|---|---|---|
| #1003, #1472, #1906, #1983 (hamburger / burger) | wheat | nguồn không có bánh; patty có thể ăn không bánh |
| #1245 sloppy joes pizza joes | wheat | nguồn không có bánh |
| #183 batter for sweet and sour shrimp, #1815 tempura batter for fish | shellfish / fish | công thức chỉ là bột áo, không có tôm/cá |
| #1854 marinade for grilled salmon, #531 lemon butter sauce for fish | fish | chỉ là nước ướp / xốt |
| #1248 my secret shrimp sauce | shellfish | xốt chấm, nguồn không có tôm |
| #1412 pork, chicken, or shrimp fried rice | shellfish | tôm là một lựa chọn, nguồn không có tôm |
| #2520 Bún Quậy Phú Quốc | molluscs | 1 trong 2 dòng nguồn trùng tên có `mực ống`; DB khớp dòng không có mực |
| 16 món "pasta / spaghetti / pizza sauce" (#71, #540, #542, #652, #665, #784, #892, #990, #1056, #1164, #1259, #1286, #1364, #1761, #1793, #142) | wheat | chỉ là xốt, không có mì/bánh |

Đã loại vì dương tính giả (không liệt kê từng món): tên nhà hàng (Red Lobster, Bonefish Grill, Oyster Bar, Cracker Barrel),
"ốc" trong *xoắn ốc / ngũ cốc / lốc xoáy*, "hào" trong *su hào*, mực/sò **chay**, nấm sò, bơ = quả bơ, sữa đậu nành,
vú sữa heo, bánh cá (hình con cá), tortilla Tây Ban Nha (trứng + khoai), há cảo bột gạo, bánh mì "bread and butter pickles".

### Lỗ hổng từ khoá thấy thêm (chưa sửa, ngoài danh sách anh giao)

`bun`, `roll`, `bisquick`, `biscuit`, `pizza dough`, `wonton`, `hoành thánh`, `tortellini`, `gnocchi`, `pie crust` (wheat);
`hào` (molluscs, cần loại `su hào`, `dầu hào chay`); tên cá Âu–Mỹ `orange roughy`, `haddock`, `sea bass`, `cod`… (fish);
nutella chưa nằm trong `ANIMAL_DERIVED_KEYWORDS` (có sữa → không chay). Các món hiện có đã được (a) vá tay. Seed lại thì vẫn lọt,
cho tới khi thêm các từ khoá này.

## (b) Dầu hào: 60 món

106 món dùng Dầu hào: 51 món thiếu `wheat`, 58 món thiếu `soy`. Tổng 60 món, 58 món là ViFoodRec đã kiểm duyệt (món xào, rim, kho).
Đây là thay đổi ảnh hưởng nhiều nhất tới món Việt: người khai dị ứng **đậu nành** hoặc **lúa mì** sẽ không còn thấy các món
dùng dầu hào. Mắm ruốc / ruốc biển: #2093 Ruốc chiên lá quế, #2110 Gà hon đậu phộng.

## (c) Từ khoá mới: 28 món

Lấy theo tên nguồn của từng món: `chưa map` = tên nằm trong `raw_ingredient_names`, `đã map` = tên đã khớp một nguyên liệu
không mang nhãn đó, ví dụ `macaroni and cheese mix`. Chi tiết từng dòng xem `change = 'c-tu-khoa'` trong `label-fixes.sql`.

- wheat (20): `macaroni` (7, gồm `elbow macaroni`, `macaroni and cheese mix`), `spaghetti` (3), `penne` (1), `crouton(s)` (4), `cracker(s)` (4), `bột bánh bao` (1).
- tree_nuts (7): `nuts` (6), `nutella` (1). soy (1): `nutella`. sesame (1): `hummus`.
- peanut (6): `nuts` trơn, cùng 6 món nhận `tree_nuts` ở trên (#167, #457, #476, #556, #936, #1470). Seed lại cũng ra nhãn này:
  `scripts/ingredient_senses.py` gắn `peanut` cho `nuts` / `mixed nuts` / `chopped nuts` không ghi rõ loại hạt
  (`pine nuts`, `macadamia nuts`… vẫn chỉ ra `tree_nuts`). Trong 3171 món đang có, luật này khớp đúng 6 món trên.

Không gắn dừa vào `tree_nuts`, không gắn yến mạch vào `wheat` (theo yêu cầu).

## S1 và S5 (`docs/demo-sets.md`): 5 món đầu có đổi không?

Không món nào trong 18 món đang hiện ở các bảng S1 / S5 (top 5 không lọc, top 5 khi lọc fish / egg / peanut, kể cả món "lên thay")
nhận thêm nhãn. Nhãn chỉ dùng để **loại** món, nên:

| Bộ | Không lọc | fish | egg | peanut | wheat, molluscs, tree_nuts | soy | sesame | shellfish |
|---|---|---|---|---|---|---|---|---|
| **S1** trứng, cà chua, hành lá, đậu hũ | không đổi | không đổi | không đổi | không đổi | không đổi¹ | không đổi² | không đổi¹ | không đổi¹ |
| **S5** tôm, tỏi, hành lá | không đổi | không đổi | không đổi | không đổi | không đổi¹ | không đổi¹ | không đổi² | không đổi² |

¹ Không món nào trong top 5 không lọc mang nhãn này, trước lẫn sau khi sửa. Top 5 khi lọc vì thế trùng top 5 không lọc và không đổi.
² Bản trước ghi "chưa xác định". Nay đã chốt offline, không cần embed hay RPC (xem câu 3 ở cuối file).

Kết luận cho demo: kịch bản đã ghi (S1 + `egg`, S5 + `fish`) không đổi.

---

# Trả lời 3 câu hỏi duyệt (2026-11-13)

Cách làm: dùng lại bản dump chỉ-đọc ở trên (3171 món), tên nguồn trong `backend/data/vifoodrec_processed.csv` và
`foodcom_filtered.csv` (tra theo tên món: cả 3171 món đều có trong nguồn, gồm 48 món trùng tên nhiều dòng nguồn), cùng
`raw_ingredient_names`. Không ghi DB, không đọc `.env`, không gọi model, không chạy test.

## 1. Món dùng nước dùng cá / tôm / hải sản đã được gắn nhãn chưa?

**Tiền đề cần sửa:** 17 món nêu ở `nuoc-dung-alias.md` **không phải** món dùng fish stock / seafood stock. Đó là 17 món có tên
gốc chỉ là `nước dùng`, `broth` hay `stock` trơn (nguồn không nói nước dùng gì). Chúng sẽ bỏ liên kết Nước dùng gà nếu áp P2.

**Nước dùng hải sản trong nguồn:** có 10 dòng nguồn. Chỉ 5 dòng có món tương ứng trong DB, và cả 5 đều là `clam juice` /
`minced clams with juice`. Tên này map vào **Nghêu (id 117)**, không phải Nước dùng gà. Cả 5 món đã có `molluscs` từ lúc seed,
`label-fixes.sql` không cần thêm gì.

| id | Món | Tên nguồn | Nhãn đang có | `label-fixes.sql` thêm |
|---|---|---|---|---|
| 827 | great new england clam chowder | clam juice | dairy, molluscs, wheat | — |
| 1256 | new england clam chowder | clam juice | dairy, molluscs, wheat | — |
| 1336 | oyster bar pan roast | clam juice | dairy, fish, molluscs, shellfish | — |
| 1504 | red lobster clam chowder | minced clams with juice | dairy, molluscs, wheat | — |
| 1954 | wegman s delicious spunky clammy chowda longmeadow | clam juice | dairy, molluscs | — |

5 dòng nguồn còn lại **không có trong DB** (không được seed): cod with spiced red lentils (`fish stock`), corn crab and chipotle
chowder (`clam broth`), tamago yaki sushi omelette (`dashi stock`), Thịt Kho Nước Tương Kiểu Nhật (`bột nêm dashi`), Bánh Đa Cua
(`nước dùng hoàn chỉnh barona lẩu cua đồng`).

→ Không món nào trong DB đang thiếu nhãn cá hay giáp xác chỉ vì alias "Nước dùng". Cả 164 món dùng Nước dùng gà đều đã tra
lại theo tên nguồn: không món nào có tên gốc là nước dùng cá, tôm hay hải sản.

**17 món tên gốc chung chung** (cho đủ). `label-fixes.sql` không thêm nhãn nào cho các món này. Nhãn hải sản ở món Việt đến từ
nguyên liệu khác trong nguồn:

| id | Món | Tên gốc | Nhãn đang có | Nguyên liệu hải sản khác trong nguồn |
|---|---|---|---|---|
| 1305 | our favorite black bean soup | broth | dairy | — |
| 1362 | passatelli dei nonni bread and parmesan cheese soup | broth | dairy, egg, wheat | — |
| 1364 | pasta sauce 1 | broth | — | — |
| 431 | chicken thighs with lime and curry | stock | dairy, wheat | — |
| 737 | fresh cream of mushroom soup | stock | dairy, wheat | — |
| 971 | hungarian mushroom soup from the moosewood cookbook | stock | dairy, soy, wheat | — |
| 1465 | pumpkin risotto | stock | dairy | — |
| 2065 | Tôm viên cơm cháy | nước dùng | sesame, shellfish, soy, wheat | tôm viên |
| 2074 | Canh rau củ ba rọi xông khói | nước dùng | — | — |
| 2077 | Cháo yến mạch thịt bò | nước dùng | dairy | — |
| 2080 | Cua lột xốt cam | nước dùng | shellfish, soy, wheat | cua lột |
| 2148 | Bún ốc | nước dùng | molluscs, shellfish, soy | thịt ốc miếng, mắm tôm |
| 2175 | Cá kèo chiên mè | nước dùng | fish, sesame, wheat | cá kèo, bột giòn hải sản |
| 2584 | Canh Khổ Qua Nhồi Thịt Ngày Tết | nước dùng | fish | — (fish từ nước mắm) |
| 2846 | Súp Bắp Cua | nước dùng | egg, sesame, shellfish, soy, wheat | thịt cua |
| 3085 | Bò Kho Ngon Kiểu Mới | nước dùng | wheat | — |
| 3160 | Bò Sốt Rượu Vang | nước dùng | wheat | — |

Món có thể đáng ngờ: **Bún ốc (#2148)**. Nước dùng bún ốc truyền thống nấu từ xương, ốc và cua đồng. Món đã có `shellfish`
và `molluscs` nên không thiếu nhãn.

## 2. 28 món nhận nhãn từ từ khoá mới (29 dòng)

Khớp theo `_keyword_pattern`: nguyên từ, cho phép đuôi `-s` (`\b(?:…)s?\b`). Vì vậy `nut` **không** khớp chestnut, doughnut,
butternut, coconut, nutmeg hay peanut. Rà mọi tên nguồn của 3171 món, các từ chứa "nut" gồm: walnut(s) 35, nutmeg 73,
coconut 7, peanut(s) 11, chestnut(s) 3, nuts 6, nutella 1, minute 2. Chỉ `nuts` (6) và `nutella` (1) khớp `tree_nuts`.
DB không có doughnut hay butternut squash. `chestnut` trong DB là **củ năng** (water chestnut, id 233) và nấm chestnut, không
phải hạt dẻ, nên không gắn nhãn là đúng. `spaghetti squash` (1 tên) đã được bỏ qua khi dò `wheat`.

| id | Món | Nhãn | Từ khoá | Tên nguồn khớp | Nghi vấn |
|---|---|---|---|---|---|
| 32 | all in one broccoli macaroni and cheese | wheat | macaroni | macaroni and cheese mix (đã map) | |
| 101 | bacon lettuce tomato layered salad | wheat | crouton | seasoned croutons | |
| 167 | barb s best zucchini bread | tree_nuts | nut | nuts | ⚠️ "nuts" không rõ loại |
| 204 | best macaroni salad | wheat | macaroni | macaroni and cheese mix (đã map) | |
| 328 | caesar salad | wheat | crouton | garlic-flavored croutons (đã map) | |
| 377 | charmie s meatloaf with pineapple topping | wheat | cracker | ritz cracker | |
| 448 | chocolate and nutella surprise muffins | tree_nuts | nutella | nutella | |
| 448 | chocolate and nutella surprise muffins | soy | nutella | nutella | (lecithin đậu nành) |
| 457 | cinnamon coffee cake kaffeekuchen | tree_nuts | nut | nuts | ⚠️ "nuts" không rõ loại |
| 476 | cocoa oatmeal muffins | tree_nuts | nut | nuts | ⚠️ "nuts" không rõ loại |
| 524 | creamy caesar salad | wheat | crouton | crouton | |
| 538 | creamy pumpkin pasta | wheat | penne | penne | |
| 556 | crumb topped banana muffins | tree_nuts | nut | nuts | ⚠️ "nuts" không rõ loại |
| 611 | dreamy spaghetti casserole | wheat | spaghetti | spaghetti | |
| 927 | herb coated cod | wheat | cracker | butter flavored cracker (đã map) | |
| 933 | herbed tomato soup | wheat | crouton | parmesan croutons (đã map) | |
| 936 | high altitude zucchini bread | tree_nuts | nut | nuts | ⚠️ "nuts" không rõ loại |
| 1020 | kelly s cheese potato casserole | wheat | cracker | chicken in a biscuit crackers (đã map) | |
| 1027 | kids love tuna mac | wheat | macaroni | macaroni and cheese mix (đã map) | |
| 1157 | manhattan clam chowder quick | wheat | cracker | oyster crackers (đã map) | |
| 1247 | my my my minestra italian vegetable soup with pasta | wheat | macaroni | macaroni | |
| 1277 | old fashioned baked mac n cheese | wheat | macaroni | elbow macaroni | |
| 1470 | quick amish friendship bread or muffins no starter required | tree_nuts | nut | nuts | ⚠️ "nuts" không rõ loại |
| 1496 | rachael ray s mamacello pasta | wheat | spaghetti | spaghetti | |
| 1581 | salmon and pasta salad | wheat | macaroni | macaroni | |
| 1677 | six layer mediterranean dip | sesame | hummus | hummus | |
| 1804 | sweetie pie s mac and cheese | wheat | macaroni | cooked elbow macaroni | |
| 1857 | the realtor s shrimp scampi w spaghetti | wheat | spaghetti | thin spaghetti | |
| 2703 | Bánh Bao Lá Dứa Nhân Mặn | wheat | bột bánh bao | bột bánh bao | |

**Gắn nhầm: 0 món.** Không món nào thuộc kiểu doughnut, butternut squash hay chestnut. `oyster crackers` (#1157) ra `wheat`
là đúng: đó là bánh quy giòn, không có hàu. Món này mang sẵn `molluscs` vì có nghêu.

**6 món ⚠️ (`nuts` trơn, bánh mì / muffin Mỹ):** gắn `tree_nuts` là đúng hướng an toàn, vì "nuts" trong bánh nướng thường là
walnut / pecan. Nhưng nếu người làm dùng đậu phộng thì món vẫn **thiếu `peanut`**. **Đã duyệt: thêm `peanut`**
(xem mục (c)). Cả 6 món không nằm trong tập qua lọc của S1 (40), S5 (48) hay P1 (31) ở `demo-sets.md`, nên không đổi demo.

Ghi chú: `mì` không phải từ khoá mới, đã có từ trước (`df0e389` chỉ thêm macaroni, spaghetti, penne, crouton, cracker,
bột bánh bao, nut, nutella, hummus, mắm ruốc, ruốc biển).

## 3. Có cần chạy lại để chốt 3 ca "chưa xác định" không?

**Không cần.** RPC `search_recipes` chỉ dùng nhãn để **loại** món (`not exists … recipe_allergens`). Điểm của từng món không
phụ thuộc vào bộ lọc. Vì vậy:

> Danh sách khi lọc = danh sách không lọc, bỏ đi các món mang nhãn. Nếu không món nào trong tập "qua lọc" (độ phủ ≥ 0,5)
> nhận nhãn mới, kết quả khi lọc sau SQL trùng hệt trước SQL, ở mọi vị trí.

Em dựng lại tập qua lọc offline đúng như RPC: nguyên liệu không tuỳ chọn, bỏ gia vị cơ bản (`pantry_basic_ids`), độ phủ ≥ 0,5.
Kết quả ra **40 món (S1) và 48 món (S5), khớp đúng con số trong `docs/demo-sets.md`**. Sau đó đối chiếu với các dòng trong
`label-fixes.sql`:

| Ca | Món qua lọc nhận nhãn này từ SQL | Kết luận |
|---|---|---|
| S1 + `soy` | 0 / 40 | không đổi |
| S5 + `sesame` | 0 / 48 | không đổi |
| S5 + `shellfish` | 0 / 48 | không đổi |
| (thêm) S1 + wheat / molluscs / tree_nuts / sesame / shellfish | 0 / 40 | không đổi |
| (thêm) S5 + `soy`, `wheat` | 2 / 48: #3148 Tôm Xóc Tỏi, #2561 Nấm Đùi Gà Xào Tỏi | không đổi¹ |

¹ Hai món này nằm ngoài top 5 không lọc của S5. Top 5 không lọc không có món nào mang `soy` / `wheat`, nên top 5 khi lọc vẫn
trùng top 5 không lọc.

Script đối chiếu (chỉ đọc file dump và CSV) nằm ở scratchpad của phiên này, không đưa vào repo.

**Nếu anh vẫn muốn kiểm trên DB thật sau khi áp SQL**, chạy lệnh sau. Lệnh chỉ đọc: SELECT bảng `ingredients`, còn RPC
`search_recipes` khai báo `stable`. Có hai lưu ý. Lệnh đọc `backend/.env` qua `create_admin_client`, nên anh tự chạy. BGE-M3
chạy local, không gọi API ngoài, nhưng lần đầu sẽ tải khoảng 2,2 GB model.

```bash
cd backend
venv/Scripts/python.exe -X utf8 -c "
from scripts.supabase_admin import create_admin_client
from app.services.ingredient_normalizer import catalog_ingredient_from_row
from app.services.pantry_basics import pantry_basic_ids
from app.services.pipeline import build_query_text
from app.services.embedding.bge_m3 import BgeM3Provider
c = create_admin_client()
cat = [catalog_ingredient_from_row(r) for r in c.table('ingredients').select('id,name_vi,name_en,aliases,category,is_vegan').execute().data]
model = BgeM3Provider()
for name, ids, slug in [('S1', [101, 7, 14, 140], 'soy'), ('S5', [113, 16, 14], 'sesame'), ('S5', [113, 16, 14], 'shellfish')]:
    emb = model.encode([build_query_text(ids, cat)])[0]
    rows = c.rpc('search_recipes', {'query_embedding': emb, 'p_diet': 'omnivore', 'p_allergens': [slug],
                 'p_ingredient_ids': ids, 'p_pantry_basic_ids': pantry_basic_ids(cat)}).execute().data
    print(name, slug, [r['title'] for r in rows])
"
```

id nguyên liệu: S1 = Trứng gà 101, Cà chua 7, Hành lá 14, Đậu phụ 140 (gõ "đậu hũ"); S5 = Tôm 113, Tỏi 16, Hành lá 14. Các id này lấy từ
`IngredientNormalizer` trên bản dump, tất cả đều `accepted`. So kết quả với bảng mục 3 của `demo-sets.md`.

## Chờ anh duyệt

- Câu 1: không cần thêm dòng nào vào `label-fixes.sql`.
- Câu 2: đã duyệt, thêm `peanut` cho 6 món `nuts` trơn (#167, #457, #476, #556, #936, #1470): +6 cặp, tổng 184.
- Câu 3: đã chốt "không đổi" offline. Chạy lệnh trên là tuỳ anh.
