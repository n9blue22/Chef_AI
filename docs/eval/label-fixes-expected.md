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
| (c) từ khoá mới | 29 | 28 | 1 | wheat 20, tree_nuts 7, soy 1, sesame 1 |
| **Cộng** | **178** (+2) | **122 món khác nhau** | | |

Không có cặp nào thuộc `dairy` hay `peanut`: nutella chỉ thêm `tree_nuts` và `soy`, vì món #448 đã có nhãn `dairy`.

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

Không gắn dừa vào `tree_nuts`, không gắn yến mạch vào `wheat` (theo yêu cầu).

## S1 và S5 (`docs/demo-sets.md`): 5 món đầu có đổi không?

Không món nào trong 18 món đang hiện ở các bảng S1 / S5 (top 5 không lọc, top 5 khi lọc fish / egg / peanut, kể cả món "lên thay")
nhận thêm nhãn. Nhãn chỉ dùng để **loại** món, nên:

| Bộ | Không lọc | fish | egg | peanut | wheat, molluscs, tree_nuts | soy | sesame | shellfish |
|---|---|---|---|---|---|---|---|---|
| **S1** trứng, cà chua, hành lá, đậu hũ | không đổi | không đổi | không đổi | không đổi | không đổi¹ | chưa xác định² | không đổi¹ | không đổi¹ |
| **S5** tôm, tỏi, hành lá | không đổi | không đổi | không đổi | không đổi | không đổi¹ | không đổi¹ | chưa xác định² | chưa xác định² |

¹ Không món nào trong top 5 không lọc mang nhãn này, trước lẫn sau khi sửa. Top 5 khi lọc vì thế trùng top 5 không lọc và không đổi.
² Top 5 không lọc có món mang nhãn này: S1 có 2 món đậu hũ mang `soy`; S5 có Tôm Chiên Sa Tế mang `sesame` và cả 5 món mang
`shellfish`. Món lên thay nằm ngoài top 5 đã biết, nên phải chạy embed + RPC mới biết có món nào trong đó dùng dầu hào hay không.
Em không chạy vì đây là bước gọi model.

Kết luận cho demo: kịch bản đã ghi (S1 + `egg`, S5 + `fish`) không đổi.
