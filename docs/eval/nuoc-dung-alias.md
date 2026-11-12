# Tách alias chung "Nước dùng" khỏi Nước dùng gà (đề xuất, CHƯA áp dụng)

Ngày 2026-11-13. Đo offline: chạy `IngredientNormalizer` trên bản dump danh mục chỉ-đọc (232 nguyên liệu) cùng các tên gốc
trong `backend/data/vifoodrec_processed.csv` và `foodcom_filtered.csv`. Không đụng DB, không gọi AI.

## Vấn đề

`Nước dùng gà` (id 192) có alias `Nước dùng`. Vì `token_set_ratio` cho 100 điểm khi một tên chứa trọn tên kia, mọi tên
**bắt đầu bằng "nước dùng"** đều được tự nhận là Nước dùng gà: `nước dùng cá`, `nước dùng heo`, `nước dùng bò`,
`nước dùng chay`, `nước dùng xương`, `nước dùng lẩu barona`… Món dùng nước dùng cá vì thế không nhận nhãn `fish`.
Người dùng gõ `nước dùng cá` cũng được tick sẵn "Nước dùng gà".

## Hai phương án

| | P1: chỉ bỏ alias `Nước dùng` | P2: P1 + tên chung chung → "chưa chắc" |
|---|---|---|
| Thay đổi | Xoá `Nước dùng` khỏi alias của id 192 (CSV `ingredients_usda.csv` + cập nhật cột `aliases` trong DB) | Như P1, cộng thêm trong `IngredientNormalizer._match_one`: tên sau khi làm sạch nằm trong `GENERIC_NAMES = {"nuoc dung", "nuoc leo", "broth", "stock"}` (so trên bản bỏ dấu) thì trả `UNCERTAIN`, giữ Nước dùng gà làm gợi ý |
| `nước dùng cá / heo / bò / chay / xương / lẩu …` | tự nhận → **chưa chắc** (86–92 điểm) ✅ | như P1 ✅ |
| `nước dùng` trơn | vẫn **tự nhận** Nước dùng gà (khớp mờ 100, vì là tập con của "nước dùng gà") ❌ | **chưa chắc**, user tự chọn ✅ |
| `broth`, `stock` trơn | vẫn tự nhận Nước dùng gà | chưa chắc |
| `nước dùng gà`, `nước hầm gà`, `chicken broth`, `chicken stock` | không đổi (khớp chính xác) | không đổi |
| `nước dùng tôm`, `… lẩu cua đồng` | đang "chưa chắc" → thành **tự nhận Tôm / Cua** (điểm cao nhất còn lại) ⚠️ | như P1 ⚠️ |
| Món trong DB đổi liên kết khi seed lại* | 0 | 17 (bỏ liên kết Nước dùng gà vì tên gốc chỉ là `nước dùng` / `broth` / `stock`; tên rơi vào `raw_ingredient_names`) |
| Top-40 nguyên liệu (124 tên + alias, `docs/demo-sets.md` mục 1) | 1 đổi: chính `Nước dùng` (exact → khớp mờ, vẫn tự nhận) | 1 đổi: `Nước dùng` → chưa chắc. 123 tên còn lại giữ nguyên id, điểm, trạng thái |

\* Chỉ tính 3123 món có đúng 1 dòng nguồn trùng tên; 48 món trùng tên với nhiều dòng nguồn được bỏ qua.

`nước dùng tôm` → Tôm ở cả hai phương án: về dị ứng thì an toàn hơn (món nhận nhãn `shellfish`), nhưng dinh dưỡng và độ phủ
lại tính như tôm thật. Nếu không muốn vậy, thêm `nuoc dung` làm tiền tố chặn tự nhận (luôn "chưa chắc"). Cách này rộng hơn P2,
em chưa đo.

**Em đề xuất P2.** P1 không xử lý được tên hay gặp nhất (`nước dùng` trơn, 34 công thức nguồn). Không phương án nào gắn được
`fish` cho món đã seed. Phải seed lại món hoặc gắn nhãn tay, giống `label-fixes.sql`. Tên gốc của phần đã map không được lưu,
nên không biết trong 164 món dùng Nước dùng gà có bao nhiêu món thực ra là nước dùng cá.

## Test đi kèm khi áp dụng (P2)

Thêm vào `backend/tests/test_ingredient_normalizer.py`, phần không cần DB (catalog dựng tay):

```python
BROTH_CATALOG = [
    CatalogIngredient(id=192, name_vi="Nước dùng gà", name_en="Chicken broth",
                      aliases=("Chicken stock", "Nước hầm gà")),
    CatalogIngredient(id=113, name_vi="Tôm", name_en="Shrimp", aliases=("Prawn",)),
]


@pytest.mark.parametrize(("name", "status"), [
    ("nước dùng gà", MatchStatus.ACCEPTED), ("nước hầm gà", MatchStatus.ACCEPTED),
    ("chicken stock", MatchStatus.ACCEPTED),
    ("nước dùng", MatchStatus.UNCERTAIN), ("nuoc dung", MatchStatus.UNCERTAIN), ("broth", MatchStatus.UNCERTAIN),
    ("nước dùng cá", MatchStatus.UNCERTAIN), ("nước dùng heo", MatchStatus.UNCERTAIN),
])
def test_generic_broth_is_not_auto_accepted_as_chicken(name: str, status: MatchStatus) -> None:
    match = IngredientNormalizer(BROTH_CATALOG).normalize([name])[0]
    assert match.status is status
    assert match.ingredient_id == 192
```

Thêm một test hồi quy: tên + alias của top-40 nguyên liệu vẫn map đúng id như trước (ngoại trừ `Nước dùng`).

## Chờ anh duyệt

- Chọn P1 hay P2 (hoặc chặn cả tiền tố `nước dùng`).
- Có seed lại món sau khi đổi không. Không seed lại thì thay đổi chỉ có tác dụng ở màn nhận diện / nhập tay của app.
