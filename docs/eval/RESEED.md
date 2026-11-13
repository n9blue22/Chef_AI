# Nạp lại dữ liệu

**Không nạp lại DB (seed / xoá rồi seed) khi chưa được anh yêu cầu rõ trong chính lượt đó.**
DB hiện tại đã được vá tay; seed lại sẽ mất các bản vá mà mã seed không tái tạo (mục 2).

## 1. Nếu buộc phải nạp lại

Theo thứ tự, mỗi bước xong mới sang bước sau:

1. Chạy seed (`seed_ingredients` → `seed_allergens` → `seed_recipes`, cwd = `backend`).
2. `docs/eval/label-fixes.sql`, rồi `docs/eval/label-fixes-2.sql` (kiểm trước/sau bằng `label-fixes-2-verify.sql`).
3. Bộ eval giai đoạn 1 (cwd = `backend`): `venv\Scripts\python.exe -m scripts.eval.run_phase1`; so với `docs/eval/phase1.md`.
4. Phép kiểm trực tiếp: chạy `docs/eval/label-fixes-2-verify.sql` (chỉ SELECT), so cột `ky_vong_sau`.

Cả hai file vá chặn áp nhầm bằng id + tên món (và diet cũ): lệch là huỷ cả giao dịch, không ghi gì. Hai chỗ chắc chắn lệch:

- **id món**: seed vào DB trống thì id do DB cấp, có thể khác bản dump 2026-11-13 → phải sinh lại hai file theo id mới.
- **`label-fixes-2.sql` phần (b)**: từ a5cfcc3, seed đã cho 5 món #120, #625, #1295, #1274, #1628 ra `omnivore`, nên
  UPDATE chỉ đổi 1 dòng (#1041) thay vì 6 → file báo lỗi và huỷ, **kéo theo cả nhãn fish của #1041**. Cần bản chỉ gồm #1041.

Ghi chú: `seed_recipes` bỏ qua món trùng tên đã có, nên chạy lại trên DB cũ **không** sửa món cũ theo mã seed mới.

## 2. Bản vá mã seed KHÔNG tái tạo

| Bản vá | Ở đâu | Vì sao seed không tái tạo |
|---|---|---|
| Nhãn trực tiếp cho 34 món (40 cặp: wheat 25, egg 9, fish 5, molluscs 1) | `label-fixes.sql`, dòng `change = 'a'`; danh sách và căn cứ ở `label-fixes-expected.md` mục (a) | từ khoá dò dị ứng chưa có `bun`, `roll`, `tortellini`, `gnocchi`, `roughy`, `haddock`, `sea bass`, `hào`…; 6 ca dựa vào tên món, nguồn không liệt kê nguyên liệu |
| Nhãn `fish` của #1041 | `label-fixes-2.sql` (a) | nguyên liệu nguồn không có cá ngừ; chỉ tên món ("egg or tuna") và bước nấu ("flake the tuna") nhắc tới |
| `diet_type` #1041 `vegetarian` → `omnivore` | `label-fixes-2.sql` (b) | a5cfcc3 chỉ sửa 5 món còn lại, không gồm #1041 |

Seed **đã** tái tạo (không cần vá tay nếu seed vào DB trống): Dầu hào +wheat +soy (`b-dau-hao`, b0b786d), mắm ruốc /
ruốc biển +shellfish (`b-ruoc`), từ khoá mới (`c-tu-khoa`, df0e389; `peanut` cho "nuts" trơn, 1914c90), diet của #120, #625, #1295, #1274, #1628 (a5cfcc3).
Chạy lại `label-fixes.sql` vẫn an toàn với các dòng này (`on conflict do nothing`).
