# Kiểm tra cache cho `POST /recognize`

Ngày 2026-11-12. Chỉ đọc mã, không sửa. Không gọi Gemini, không đọc `.env`. Số đo ở mục 4 chạy trên máy dev, danh mục
dựng từ CSV seed.

## 1. Mỗi lượt quét tốn những gì

Luồng chạy: `deps.limit_user("recognize", consume_daily=True)` (`app/api/deps.py:56-67`), sau đó tới
`routes/ai.py:103-110`, rồi `pipeline.recognize_ingredients` (`app/services/pipeline.py:68-91`).

| # | Lượt gọi | Số lần mỗi request | Ghi chú |
|---|---|---|---|
| 1 | Kiểm chữ ký JWT (`JwtVerifier.verify`) | 0 lượt mạng (thường gặp) | Khoá JWKS cache 3600 s (`auth_tokens.py:17`). Chỉ tải lại JWKS (HTTP tới Supabase **Auth**, không phải DB) lúc mới khởi động, khi hết hạn hoặc gặp `kid` lạ. |
| 2 | Hạn mức theo phút (`RateLimiter.check`) | 0 | Đếm trong RAM. |
| 3 | **Supabase: RPC `consume_daily_quota`** | **1** | Gọi bằng client secret. Trong một giao dịch: `insert … on conflict do nothing` 2 bucket (`user:<id>:recognize`, `global:recognize`), `select … for update`, kiểm trần, `update used+1`. Là 1 lượt HTTP tới PostgREST, ~255 ms từ máy dev tới Sydney. |
| 4 | Supabase: đọc danh mục `ingredients` | 0, cứ 300 s thì 1 | `IngredientCatalogCache` (`ingredient_normalizer.py:189-210`) dùng chung cả app, dựng trong `main.lifespan`. Lượt đầu sau khởi động đọc DB (~650 ms). |
| 5 | **Gemini `generate_content`** | **1** (tối đa 3 lượt HTTP) | `gemini_client.py`: `RETRY_ATTEMPTS = 3`, SDK tự thử lại khi gặp 408/429/5xx. Lỗi tạm thời có thể ngốn tới 3 lượt Gemini nhưng app chỉ thấy 1. |
| 6 | Nhúng vector (bge-m3) | **0** | `/recognize` không nhúng. Chỉ `/recipes/suggest` nhúng. |
| 7 | Ghi log vào DB | **0** | Không có bảng log hay middleware nào ghi DB. Chỉ có `logger.exception/warning` ra stdout khi lỗi, cộng header `X-Process-Time`. |

Tổng mỗi lượt quét (catalog đã có trong cache): **1 lượt Gemini (có thể tới 3 khi thử lại) và 1 lượt Supabase (RPC
trừ hạn mức)**.

**Danh mục và bộ chuẩn hoá:**
- Danh mục: nạp **một lần rồi giữ trong RAM**, đọc lại DB sau 300 s.
- Bộ chuẩn hoá: **dựng lại mỗi request**. `IngredientNormalizer(catalog)` ở `pipeline.py:79` mỗi lần đều dựng lại
  `IngredientMatcher` và 2 bảng alias. Tốn ~1,9 ms (xem mục 4).

**Phát hiện thêm (ngoài câu hỏi):** lượt ngày bị trừ ở **dependency**, tức là **trước** khi đọc và kiểm ảnh. Vì vậy
ảnh quá cỡ (413), sai định dạng (415), ảnh không có đồ ăn (422) và Gemini lỗi (503) **đều mất 1 lượt ngày**.
`docs/demo-caps.md` mới ghi trường hợp "gọi lỗi vẫn mất lượt", chưa ghi trường hợp 413/415.

## 2. Thứ tự hiện tại và có nên trừ lượt ngày khi cache trúng

Thứ tự hiện tại:

1. Kiểm JWT.
2. Kiểm hạn mức theo phút (RAM).
3. **Trừ hạn mức ngày (RPC).**
4. Đọc file, `prepare_image_for_vision` (kiểm định dạng, giải mã, thu nhỏ).
5. Lấy catalog (thường từ cache).
6. Gọi Gemini.
7. Chuẩn hoá.
8. Trả kết quả.

**Có nên trừ lượt ngày khi cache trúng không? Theo em là không.** Hạn mức ngày đặt ra để giữ quota free tier của
Gemini (`rate_limit.py`, docstring đầu file). Cache trúng thì không gọi Gemini, nên trừ lượt là phạt user mà không giữ
được gì. Hạn mức theo phút vẫn giữ nguyên ở dependency để chống spam.

Muốn không trừ khi trúng thì phải dời bước trừ ra khỏi dependency. Thứ tự mới:

1. JWT.
2. Hạn mức theo phút (vẫn ở dependency: `limit_user("recognize")`, bỏ `consume_daily=True`).
3. Đọc và kiểm ảnh.
4. Băm ảnh, tra cache.
   - **Trúng:** trả luôn, `X-Cache: HIT`, không trừ lượt.
   - **Trượt:** trừ lượt ngày (RPC, như cũ), gọi Gemini, chuẩn hoá, lưu cache nếu thành công, trả kết quả với
     `X-Cache: MISS`.

Rủi ro khi đổi thứ tự:

| Rủi ro | Mức độ | Xử lý |
|---|---|---|
| User đã hết lượt ngày vẫn khiến server giải mã ảnh (Pillow, tới ~150 MB RAM với ảnh 50 MP) rồi mới nhận 429. | Thấp | Đã có trần 5 lượt/phút/user và chặn bom giải nén. Nếu vẫn lo thì thêm `ensure_daily_available` trước bước giải mã, đổi lại tốn thêm 1 lượt DB mỗi request. Em **không** đề xuất. |
| Ảnh hỏng (413/415) không còn mất lượt ngày. | Đây là thay đổi hành vi, có lợi cho user | Sửa lại `docs/demo-caps.md` dòng 32. |
| User hết lượt nhưng quét lại đúng ảnh cũ vẫn nhận kết quả (trúng cache). | Chấp nhận được | Không tốn Gemini. Ghi rõ hành vi này trong spec. |
| 2 request cùng ảnh gửi đồng thời đều trượt, cùng trừ lượt và cùng gọi Gemini. | Thấp (giống hiện nay) | Không làm gom request trùng (single-flight). Ghi `ponytail:` trong mã. |
| Trừ lượt nằm trong service, không còn ở dependency. Nếu sau này có endpoint khác gọi `recognize_ingredients` mà quên trừ lượt thì quota bị lọt. | Thấp | Để việc trừ lượt nằm cùng hàm với tra cache (trong service, giống `suggest_recipes` nhận `quota_check`). Route chỉ truyền callback vào. |
| 503/422 vẫn mất lượt (đã trừ trước khi gọi Gemini). | Giữ như hiện nay | Muốn đổi sang "chỉ trừ khi thành công" như `suggest` là một quyết định riêng, không thuộc việc cache. |

## 3. Thiết kế tầng 1: cache kết quả quét

**Khoá:** `(user_id, PIPELINE_VERSION, sha256(bytes gốc của file))`. Chỉ băm **sau khi** `prepare_image_for_vision`
chạy xong không lỗi, nên ảnh hỏng không bao giờ thành khoá. Băm bytes gốc, không băm JPEG đã thu nhỏ: hai cách cho
kết quả như nhau vì Pillow mã hoá tất định trên cùng phiên bản, nhưng băm bytes gốc không phụ thuộc phiên bản Pillow.

**Giá trị:** em đề xuất cache `Detected`, tức là đầu ra của Gemini (2 danh sách tên), **không** cache
`RecognizedIngredients`. Khi trúng thì chạy lại bước chuẩn hoá trên catalog hiện tại, tốn ~5 ms.
- Lợi: seed thêm nguyên liệu hay sửa bộ chuẩn hoá thì cache tự đúng theo. Không có rủi ro trả `ingredient_id` hoặc tên
  đã cũ suốt 24 giờ.
- Như vậy "phiên bản" trong khoá chỉ cần đại diện cho **phía vision**:
  `PIPELINE_VERSION = sha256(GEMINI_MODEL + SYSTEM_PROMPT + USER_PROMPT)[:12]`. Giá trị này tính tự động, nên đổi
  prompt hay model là cache tự mất, không ai phải nhớ tăng số. Có thể cộng thêm một hằng `SCAN_CACHE_VERSION = 1` để
  xoá cache bằng tay khi cần.
- Nếu anh vẫn muốn đúng như yêu cầu (cache kết quả cuối, khoá có phiên bản bộ chuẩn hoá) thì cần thêm hằng
  `NORMALIZER_VERSION` và nhớ tăng nó mỗi khi sửa `ingredient_normalizer.py` / `ingredient_matching.py`. Vẫn còn lệch
  catalog tối đa 24 giờ sau mỗi lần seed. Em không khuyên cách này.

**Lưu trữ:** chỉ trong RAM. Dùng `collections.OrderedDict` làm LRU (truy cập thì `move_to_end`, quá 200 mục thì
`popitem(last=False)`), mỗi mục kèm thời điểm lưu, quá 24 h thì coi như trượt và xoá. Không cần thư viện mới:
`cachetools` chưa cài, còn `functools.lru_cache` không có TTL và không dùng được với hàm async. 200 mục, mỗi mục cỡ
<1 KB, nên RAM không đáng kể. **Không lưu ảnh**, chỉ giữ hash. Server ngủ hoặc khởi động lại là mất cache, chấp nhận.

**Không cache:** `VisionUnavailableError` (503), `NoUsableIngredientsError` (422, gồm cả ảnh không có đồ ăn lẫn ảnh
không khớp catalog), 413/415. Quy tắc gọn nhất: chỉ ghi vào cache khi `recognize_ingredients` trả về được kết quả.

**X-Cache:** route nhận thêm tham số `response: Response` và đặt `response.headers["X-Cache"] = "HIT" | "MISS"`. Muốn
JS phía web đọc được header này thì thêm `"X-Cache"` vào `expose_headers` trong `main.py`. Chỉ xem trong DevTools thì
không cần thêm.

### Thay đổi mã (ước lượng)

| File | Thay đổi | Dòng |
|---|---|---|
| `app/services/scan_cache.py` (mới) | `ScanResultCache` (OrderedDict + TTL + giới hạn 200, đồng hồ truyền vào được để test), `scan_cache_key(user_id, image_bytes)`, `PIPELINE_VERSION` | ~45 |
| `app/services/pipeline.py` | Tách `recognize_ingredients` thành `detect` (gọi Gemini) và `match_detected` (chuẩn hoá, gồm 2 lần raise `NoUsable…`). Thêm `recognize_with_cache(raw, prepared, user_id, cache, consume_quota, vision, catalog_cache) -> tuple[RecognizedIngredients, bool]`. File tăng từ 204 lên ~230 dòng, chưa chạm mốc 300. | ~30 |
| `app/api/routes/ai.py` | `recognize_user = limit_user("recognize")` (bỏ `consume_daily`). Route truyền `functools.partial(limiter.consume_daily, "recognize", user.id)` vào, giống `suggest`, rồi đặt `X-Cache`. Không có logic trong route. | ~8 |
| `AiServices` (`ai.py`) + `main.lifespan` | Thêm field `scan_cache: ScanResultCache` | ~3 |
| `main.py` | (Tuỳ chọn) thêm `X-Cache` vào `expose_headers` | 1 |
| `docs/demo-caps.md`, `feature-spec.md` | Ghi hành vi mới về thời điểm trừ lượt và việc cache | — |

**Công sức:** khoảng 2–3 giờ, cả test. Rủi ro thấp: không đụng DB, không cần migration, không đổi API (chỉ thêm
header).

### Test cần có

Đặt trong `tests/test_ai_routes.py`, dùng `FakeVision` có đếm số lần gọi:

1. **Cùng user, cùng ảnh, gửi 2 lần:** Gemini được gọi 1 lần, `X-Cache` lần lượt là `MISS` rồi `HIT`, body giống
   nhau, `FakeLimiter.daily == ["recognize"]` (trừ lượt 1 lần).
2. **Hai user, cùng một ảnh:** Gemini được gọi 2 lần, cả hai lần đều `MISS`. Cách làm: override `require_user` theo
   từng lượt gọi, hoặc gọi thẳng service với 2 `user_id`.
3. **Đổi phiên bản làm mất cache:** monkeypatch `scan_cache.PIPELINE_VERSION` giữa 2 lần gửi, lần sau là `MISS` và
   Gemini được gọi lại.
4. **Ảnh hỏng không vào cache:** gửi JPEG cắt cụt → 415, cache vẫn rỗng, `FakeLimiter.daily == []`.
5. **Lỗi không vào cache:** Gemini ném `VisionUnavailableError` → 503. Lần gửi sau cùng ảnh (Gemini giờ trả kết quả)
   là `MISS` → 200. Làm tương tự với `Detected` rỗng → 422.
6. **Hạn mức theo phút vẫn tính khi trúng:** **không** override `recognize_user`. Override `require_user` và dùng
   `RateLimiter` thật với admin giả (`rpc` trả `True`). Gửi 6 lần cùng ảnh: 5 lần đầu 200 (1 MISS, 4 HIT), lần thứ 6
   429. Gemini được gọi 1 lần, RPC được gọi 1 lần.
7. Unit test cho `ScanResultCache` với đồng hồ giả: hết TTL 24 h thì trượt, mục thứ 201 đẩy mục ít dùng nhất ra.

### Tác động tới test hiện có

- `client_with` (`test_ai_routes.py:98`): `AiServices` là dataclass frozen, phải truyền thêm
  `scan_cache=ScanResultCache()`. Mỗi lần gọi `client_with` tạo cache mới, nên các test không dính cache của nhau.
- `FakeLimiter` đã có `consume_daily`, không cần sửa. Hiện các test override `recognize_user` nên trước giờ không ai
  đi qua đường trừ lượt ngày. Sau khi đổi, việc trừ lượt chạy trong service và đi qua `FakeLimiter`, nên test được.
- `test_recognize_decodes_only_allowed_formats`, `…rejects_non_image…`, `…distinguishes_vision_error…`: đều dùng
  client mới, không đổi.
- `test_pipeline.py:360` gọi thẳng `recognize_ingredients(...)`. Nếu giữ nguyên chữ ký hàm này (cho nó gọi
  `detect` + `match_detected`) thì không phải sửa.
- `test_openapi.py:69`: mã lỗi giữ nguyên (401/413/415/422/429/503), không đổi.

### Hiệu quả thực tế: chưa biết, nên đo trước khi làm

Ảnh chụp camera lần nào cũng ra bytes mới, nên **không bao giờ** trúng cache. Chỉ trúng khi user chọn lại đúng file
trong thư viện ảnh, hoặc gửi lại (bấm thử lại, quay về rồi quét lại). Riêng ảnh thư viện,
`useImageScan.ts:6` đặt `quality: 0.6` nên Expo nén lại. Em **chưa kiểm** được Expo nén lại có ra đúng bytes cũ
không. Nếu không ra đúng bytes cũ thì tỉ lệ trúng gần 0. Đề xuất rẻ hơn để làm trước: log `sha256` (8 ký tự đầu) của
mỗi lượt quét trong 1–2 tuần, đếm số lần trùng, rồi mới quyết định làm tầng 1.

## 4. Tầng 2 (danh mục trong RAM, cache kết quả khớp tên)

- **Danh mục trong RAM: đã có** (`IngredientCatalogCache`, 300 s).
- **Cache kết quả khớp tên: chưa có.** Bộ chuẩn hoá cũng được dựng lại mỗi request.

Số đo thật (`bench_normalize.py` trong scratchpad, 200 vòng, danh mục 246 dòng dựng từ
`data/ingredients_usda.csv` + `ingredients_vn_manual.csv`, 10 tên kiểu Gemini hay trả, gồm cả tên phải khớp mờ):

| Bước | Trung vị | Max |
|---|---|---|
| Dựng `IngredientNormalizer` | 1,9 ms | 15,7 ms |
| `normalize` 10 tên | 3,3 ms | 6,0 ms |
| **Dựng + chuẩn hoá (đúng việc mỗi request đang làm)** | **5,5 ms** | 16,9 ms |

So với cả request (trung vị 2453 ms theo `feature-spec.md:466`, Gemini chiếm 1,1–4,2 s), phần này chiếm **~0,2 %**.
**Không đáng làm.** Giữ bộ chuẩn hoá dựng sẵn thì bớt được ~2 ms, cache khớp tên bớt thêm ~3 ms, nhưng phải xử lý
việc làm mất cache khi catalog đổi. Chưa có lý do làm, khi nào danh mục lên hàng nghìn dòng thì đo lại.

Còn một cải tiến nhỏ đáng làm hơn, tách biệt với cache: lượt đầu sau khởi động đọc catalog mất ~650 ms. Có thể gọi
`await catalog.get()` trong `lifespan` để nạp trước (`feature-spec.md:476` đã ghi ý này). Thêm 1 dòng.

## 5. Ngoài phạm vi

Theo yêu cầu, tài liệu này không đề xuất cache kết quả tìm công thức (`/recipes/suggest`).

## 6. Đã làm (nhánh `feat/v4-cache`) và số đo MISS/HIT

Làm theo mục 3 với 3 điều chỉnh đã duyệt: cache **đầu ra Gemini** (`Detected`), **chạy lại chuẩn hoá** khi trúng,
khoá có **mã phiên bản tự tính**: `VisionProvider.output_version()`, bản Gemini là
`sha256(GEMINI_MODEL + SYSTEM_PROMPT + USER_PROMPT + schema Detected)[:12]` (`vision/gemini.py`), đọc lúc gọi nên
đổi model/prompt là trượt ngay. Không thêm `SCAN_CACHE_VERSION` bằng tay (chưa cần: restart là xoá cache).

Đo ngày 2026-11-12, script `bench_scan_cache.py` (scratchpad, không commit). Đi qua route thật bằng `TestClient`,
vision giả `asyncio.sleep(2,0 s)` (cỡ trung vị Gemini), RPC trừ lượt giả `asyncio.sleep(0,255 s)`, danh mục 246 dòng
dựng từ CSV seed, ảnh `chicken_parmesan_mise_en_place.jpg` lưu lại qua Pillow (960×954, 254 KB). MISS: 10 ảnh khác
nhau 1 byte; HIT: 10 lần cùng 1 ảnh. Số là `X-Process-Time` (trong server, chưa tính mạng).

| | Trung vị | Min | Max |
|---|---|---|---|
| MISS | 2284 ms | 2275 ms | 2303 ms |
| HIT | 13 ms | 12 ms | 191 ms |

MISS ≈ 2000 (vision) + 255 (RPC) + ~25 ms (kiểm/thu nhỏ ảnh, chuẩn hoá). HIT vẫn giải mã ảnh (phải kiểm 413/415 trước
khi tra cache) và chuẩn hoá lại, nên không về 0. Max 191 ms của HIT là 1 lượt lẻ, chưa tìm nguyên nhân (có thể GC).
Tỉ lệ trúng thực tế vẫn **chưa biết** (xem mục "Hiệu quả thực tế" ở trên): ảnh camera luôn trượt.
