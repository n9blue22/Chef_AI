# Eval sau khi áp `label-fixes.sql`

Ngày 2026-11-13. Chỉ đọc: SELECT bảng và RPC `search_recipes` (`stable`), bge-m3 chạy local. Không ghi DB, không đọc `.env`
(script tự nạp cấu hình qua `app.core.config`), không gọi Groq/Gemini/Cloudflare, không chạy pytest.

- Giai đoạn 1: `python -m scripts.eval.run_phase1` → `backend/scripts/eval/out/{phase1,order,summary}-20261113-011515.*`
  (thư mục bị gitignore). Lệnh `print(summary)` cuối script lỗi `UnicodeEncodeError` (console cp1252), nhưng cả 3 file đã
  được ghi trước dòng đó. Lần sau nên chạy với `-X utf8`.
- Bản trước khi sửa: `E:\bep-ai-archive\eval-truoc-sua-nhan\*-20261112-235340.*`.
- S1, S5, P1: gọi RPC thật, diet `omnivore`, một lần không lọc và mười lần lọc, mỗi lần một slug. Tập "qua lọc"
  (độ phủ ≥ 0,5) tính lại offline theo đúng công thức RPC. Script nằm trong scratchpad, không đưa vào repo.

## Kết luận

| Tiêu chí | Trước | Sau | Đạt |
|---|---|---|---|
| Món lọt dị ứng | 0 | **0** | ✅ |
| Nghi vấn theo tên gốc chưa map | 0 | 0 | ✅ |
| Món sai chế độ ăn | 0 | **0** | ✅ |
| Ca đủ 5 món | 28/40 | **28/40** | ✅ không giảm |
| Tổng món trả về | 158 | 158 | |
| 5 món đầu của S1 (mọi lọc) | | **không đổi** | ✅ |
| 5 món đầu của S5 (mọi lọc) | | **không đổi** | ✅ |
| Món mang nhãn `peanut` | 66 | **72** | ✅ |

**Giai đoạn 1 khớp tuyệt đối:** cả 40 ca trả đúng các món cũ, đúng thứ tự, đúng điểm. Phép đảo thứ tự (`order-*.jsonl`) cũng
trùng từng byte. Trong `summary` chỉ khác bảng thời gian: RPC trung vị 404 → 172 ms. Mức chênh này do mạng và tải máy,
không do nhãn.

⚠️ Hệ quả: bộ 40 ca **không chạm** món nào trong 122 món nhận nhãn mới. Eval này chỉ xác nhận sửa nhãn không làm hỏng gì.
Nó không chứng minh được các nhãn mới lọc đúng. Phần đó dựa vào mục "Kiểm DB" bên dưới.

## Kiểm DB: 184 cặp đã vào đủ

- 184/184 cặp (món, nhãn) trong `label-fixes.sql` có trong `recipe_allergens`. Không thiếu cặp nào.
- `recipe_allergens`: 5439 → **5623** dòng (+184), 3171 món (không đổi). Có 122 món khác nhau nhận nhãn mới, đúng như
  `label-fixes-expected.md`.

### Số món bị lọc thêm theo từng loại dị ứng (toàn DB)

"Sau" là số đếm trên DB thật. "Trước" = Sau − số cặp SQL thêm. SQL chỉ thêm nhãn, không xoá.

| Dị ứng | Trước | Sau | Lọc thêm | Kỳ vọng (`label-fixes-expected.md`) |
|---|---|---|---|---|
| wheat | 1335 | 1429 | **+94** | 25 + 49 + 20 = 94 ✅ |
| soy | 377 | 436 | **+59** | 58 + 1 = 59 ✅ |
| egg | 895 | 904 | **+9** | 9 ✅ |
| tree_nuts | 85 | 92 | **+7** | 7 ✅ |
| peanut | 66 | **72** | **+6** | 6 ✅ |
| fish | 607 | 612 | **+5** | 5 ✅ |
| shellfish | 260 | 262 | **+2** | 2 ✅ |
| molluscs | 180 | 181 | **+1** | 1 ✅ |
| sesame | 195 | 196 | **+1** | 1 ✅ |
| dairy | 1439 | 1439 | 0 | 0 ✅ |
| **Cộng** | | | **+184** | 184 ✅ |

## S1, S5, P1

Món qua lọc: S1 40, S5 48, P1 31, đều khớp `demo-sets.md`. Mọi tên đều được tự nhận, không có tên "chưa chắc".

### 5 món đầu không lọc: không đổi ở cả 3 bộ

| Bộ | 5 món đầu (giống hệt `demo-sets.md`, cả điểm) |
|---|---|
| S1 | Trứng Chiên Cà Chua 0,9595 · Đậu Hũ Chiên Sốt Cà Chua Ngọt 0,8759 · Đậu Hũ Chiên Sốt Cà Chua Béo Thơm 0,8697 · Trứng Cuộn Hành Lá 0,7936 · Trứng Chiên Cà Chua Ngon Cơm 0,7925 |
| S5 | Tôm Chiên Sa Tế 0,8635 · Tôm Rang Mặn Ngọt 0,8484 · Tôm Rang Mặn Ngọt Ngon Cơm 0,8238 · Canh Bầu Nấu Tôm 0,8165 · Tôm Tích Rim Nước Mắm 0,8137 |
| P1 | Gỏi Đu Đủ Tôm Tai Heo 0,7329 · Tôm Tái Chanh 0,7321 · Tôm Thẻ Rim Chua Ngọt 0,6812 · Tôm Tích Rim Nước Mắm 0,6129 · Chà Bông Tôm 0,6084 |

### Món qua lọc nhận nhãn mới

| Bộ | Món | Nhãn mới | Nằm trong 5 món đầu khi lọc nhãn đó? |
|---|---|---|---|
| S1 | #2374 Đậu Hũ Chiên Sốt Mayonnaise | egg | Không. Trước đây món này cũng ở dưới hạng 5 khi lọc `egg` |
| S5 | #3148 Tôm Xóc Tỏi | soy, wheat | Không. Top 5 khi lọc soy/wheat = top 5 không lọc |
| S5 | #2561 Nấm Đùi Gà Xào Tỏi | soy, wheat | Không, cùng lý do |
| P1 | #2374 Đậu Hũ Chiên Sốt Mayonnaise | egg | Không. Top 5 khi lọc egg = top 5 không lọc |

Nhãn chỉ dùng để loại món, điểm không phụ thuộc bộ lọc. Vì vậy 5 món đầu khi lọc chỉ đổi khi một món **đang nằm trong đó**
nhận nhãn mới. Không có ca nào như vậy, nên **mọi kết quả lọc của cả 3 bộ đều không đổi**. Kết luận này khớp mục 3 của
`label-fixes-expected.md`. Riêng #2374 ở S1 (+egg) không được liệt kê trong file đó, vì bảng ở đó chỉ xét các slug khác `egg`.

### Ẩn / qua lọc theo dị ứng (trước → sau)

| Dị ứng | S1 (40) | S5 (48) | P1 (31) |
|---|---|---|---|
| fish | 3 → 3 | 21 → 21 | 7 → 7 |
| shellfish | 2 → 2 | 25 → 25 | 9 → 9 |
| molluscs | 0 → 0 | 2 → 2 | 0 → 0 |
| egg | 26 → **27** | 2 → 2 | 1 → **2** |
| dairy | 3 → 3 | 5 → 5 | 3 → 3 |
| peanut | 0 → 0 | 0 → 0 | 1 → 1 |
| tree_nuts | 0 → 0 | 0 → 0 | 0 → 0 |
| soy | 11 → 11 | 1 → **3** | 2 → 2 |
| wheat | 10 → 10 | 1 → **3** | 1 → 1 |
| sesame | 1 → 1 | 1 → 1 | 0 → 0 |

Số "trước" của S1 fish/egg/peanut và S5 fish/egg/peanut khớp `demo-sets.md` (3, 26, 0, 21, 2, 0).

### Kịch bản demo: vẫn như cũ

| Bộ + dị ứng | Bị loại khỏi top 5 | Lên thay | Khớp `demo-sets.md` |
|---|---|---|---|
| S1 + `egg` | Trứng Chiên Cà Chua, Trứng Cuộn Hành Lá, Trứng Chiên Cà Chua Ngon Cơm | Đậu Hũ Nhồi Thịt Băm Sốt Cà, Tàu Hũ Sốt Cà, Đậu Hũ Hấp Hành Hương | ✅ |
| S1 + `fish` | Đậu Hũ Chiên Sốt Cà Chua Béo Thơm | Trứng Cuộn Nhiều Lớp | ✅ |
| S5 + `fish` | Tôm Chiên Sa Tế, Tôm Rang Mặn Ngọt, Tôm Rang Mặn Ngọt Ngon Cơm, Tôm Tích Rim Nước Mắm | Tôm Rang Giòn, Canh Bí Đỏ Nấu Tôm, garlic shrimp, Tôm Chiên Tỏi Ớt Chua Cay | ✅ |
| P1 + `peanut` | Gỏi Đu Đủ Tôm Tai Heo | Tôm Luộc | ✅ |

Ghi thêm, không do sửa nhãn: S1 + `soy` loại cả hai món Đậu Hũ Chiên Sốt Cà Chua, vì đậu hũ vốn mang `soy`. Bánh Hành lên
hạng 5. Nếu khi demo có ai khai dị ứng đậu nành với bộ S1 thì đây là kết quả đúng, không phải lỗi.

## Chờ anh duyệt

File này chưa commit. Nhánh hiện tại là `main`, nên nếu anh muốn commit thì em sẽ tạo nhánh riêng trước.
