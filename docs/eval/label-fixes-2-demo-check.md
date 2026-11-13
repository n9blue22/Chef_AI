# `label-fixes-2.sql` không đụng các bộ demo S1, S5, P1, S12

Ngày 2026-11-13 · chỉ đọc, tính offline trên bản dump chỉ-đọc 2026-11-13 (không gọi RPC, không ghi DB, không đọc `.env`).
Script `demo_check.py` để ở scratchpad, không đưa vào repo.

**Món kiểm:** #1041 (thêm `fish`), #120, #625, #1295, #1628 (diet_type `vegetarian` → `omnivore`).

## Cách tính

"Đủ điều kiện" = qua lọc độ phủ của `search_recipes` (`20260930120000_search_recipes_verified_bonus.sql`):
độ phủ = tỉ lệ nguyên liệu **bắt buộc** của món (bỏ `is_optional` và gia vị cơ bản Dầu ăn, Đường, Muối, Nước mắm,
Tiêu đen) có trong bộ; cần ≥ 0,5. Tính với diet `omnivore`, không lọc dị ứng, nên đây là **tập lớn nhất**: thêm diet
chay hay dị ứng chỉ làm tập nhỏ đi. Top 5 luôn nằm trong tập đủ điều kiện.

Kiểm cách tính: số món đủ điều kiện ra **đúng bằng** cột "Qua lọc" của `docs/demo-sets.md` ở cả 4 bộ.

## Kết quả

| Bộ | Nguyên liệu (id) | Đủ điều kiện: omnivore / chay (vegetarian+vegan) | #1041 | #120 | #625 | #1295 | #1628 | Món kiểm có mặt? |
|---|---|---|---|---|---|---|---|---|
| S1 | trứng 101, cà chua 7, hành lá 14, đậu hũ 140 | 40 / 19 | 0,38 | 0,17 | 0 | 0 | 0,20 | không |
| S5 | tôm 113, tỏi 16, hành lá 14 | 48 / 4 | 0,12 | 0 | 0 | 0 | 0 | không |
| P1 | đu đủ 63, cà rốt 9, tôm 113, rau răm 172, chanh 60 | 31 / 20 | 0 | 0 | 0 | 0,14 | 0 | không |
| S12 | đậu hũ 140, cà chua 7, nấm hương 35, hành lá 14, nước tương 156 | 30 / 8 | 0,25 | 0 | 0 | 0 | 0 | không |
| S12 (3 thứ anh nêu) | đậu hũ 140, cà chua 7, nấm hương 35 | 8 / 1 | 0,12 | 0 | 0 | 0 | 0 | không |

Các ô số là độ phủ của món kiểm với bộ đó; mọi giá trị < 0,5. Vậy cả 5 món **không nằm trong danh sách đủ điều kiện,
và do đó không nằm trong top 5**, của S1, S5, P1, S12, với mọi diet và mọi dị ứng. `label-fixes-2.sql` không làm
đổi kết quả 4 bộ này. Top 5 ghi trong `demo-sets.md` (S1: 3083, 2372, 2545, 2426, 2792; S5: 2509, 3133, 2563, 2274, 2861)
cũng không chứa món nào trong 5 món trên.
