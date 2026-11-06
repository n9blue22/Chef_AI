# Ghi chú bảo mật phụ thuộc

Kiểm 2026-11-06, chỉ đọc — **chưa nâng gói nào**.

## Backend — pip-audit

Lệnh (chạy bằng `uvx`, môi trường tạm, không đụng venv; `PYTHONUTF8=1` vì Windows cp1252 làm pip-audit lỗi mã hoá):

```
uvx pip-audit -r requirements-ml.txt --no-deps     # file ghim phiên bản
uvx pip-audit -r requirements.txt                   # resolve mới như lúc Docker dựng (gộp cả requirements-ml.txt)
uvx pip-audit -r <pip freeze của backend/venv> --no-deps   # phiên bản đang cài thật ở máy dev
```

| Nguồn | Kết quả |
|---|---|
| `requirements-ml.txt` (torch 2.14.0, transformers 5.17.0, sentence-transformers 6.1.0) | 0 cảnh báo |
| `requirements.txt` resolve mới (114 gói, Pillow 13.0.0, certifi 2026.10.23) | 0 cảnh báo |
| venv local (`pip freeze`) | **61 cảnh báo / 6 gói** — bảng dưới |

`requirements.txt` dùng `>=` nên image lấy bản mới nhất **tại lúc dựng**. Image dựng hôm nay sẽ sạch; image đang chạy
(dựng trước khi Pillow 13.0.0 ra) có thể còn các lỗi Pillow dưới đây — **chưa kiểm được trong image**.

### Cảnh báo ở venv local: có trên đường chạy thật không, khai thác từ xa được không

| Gói (bản local → bản sửa) | Số | Trên đường chạy thật? | Từ xa? |
|---|---|---|---|
| **pillow 12.3.0 → 13.0.0** | 39 | **Có, một phần.** `POST /api/v1/recognize` → `upload_image.prepare_image_for_vision`: `Image.open` **không giới hạn định dạng**, rồi `exif_transpose` + `convert("RGB")` giải mã ảnh, `save` JPEG. Lọt qua được: bộ giải mã TIFF (tile/strip, OOB read, heap overflow `_decodeTile`), libopenjp2 (JPEG 2000, heap **write**), BMP RLE / MSP RLE (cấp RAM vô hạn), XBM ReDoS, GIF comment bậc hai, `Exif.load` (CPU). Có thể: ghi comment JPEG sau ICC (comment từ ảnh gốc đi theo `info`), MPO/DCX/SPIDER `seek`. **Không** trên đường chạy: lưu TIFF/PDF, vẽ chữ, ImageMorph, rank filter, `Image.merge`, Arrow, TarIO, PILfont, WMF (chỉ Windows), EPS (image không có Ghostscript), FlashPix/MIC (không cài `olefile`). | **Có**, nhưng cần đăng nhập (JWT) và bị rate limit `recognize` (5/phút, 30/ngày). Tệ nhất: làm sập worker (DoS) hoặc hỏng bộ nhớ qua JPEG 2000/TIFF. |
| certifi 2026.7.22 → 2026.10.18 | 2 (trùng) | Có — kho CA cho kết nối ra Supabase/Groq/Gemini/Cloudflare (httpx). Còn tin root `emSign ECC Root CA - G3`. | Không trực tiếp: cần vừa MITM được đường ra của server vừa có chứng chỉ từ CA đó. |
| dnspython 2.8.0 → 2.9.0 | 1 | Không. Chỉ `email-validator` dùng khi `check_deliverability=True`; `EmailStr` của pydantic tắt cờ này → không tra DNS. | Không. |
| pyasn1 0.6.4 → 0.6.5 | 4 | Không. Qua `google-auth`/`pyasn1_modules`, chỉ giải mã khoá/chứng chỉ cục bộ; Gemini dùng API key. | Không. |
| filelock 4.0.3 → 4.2.1 | 14 | Không với request. `huggingface_hub`/`torch` khoá file cục bộ; image đặt `HF_HUB_OFFLINE=1`. | Không — cần quyền ghi file trên máy. |
| setuptools 84.0.0 → 84.1.0 | 1 | Không — chỉ lúc cài wheel trên Windows. | Không. |

Đề xuất (chưa làm, chờ duyệt):
1. Dựng lại image để lấy Pillow ≥ 13.0.0 và kiểm `pip show pillow` trong image; cân nhắc ghim `pillow>=13.0.0`.
2. Giới hạn định dạng: `Image.open(..., formats=["JPEG", "PNG", "WEBP"])` — chặn cả lớp lỗi TIFF/JPEG 2000/BMP/MSP/XBM
   kể cả khi Pillow sau này có lỗi mới. Cần kiểm định dạng ảnh mà frontend thật sự gửi (HEIC từ iPhone?) trước khi chốt.

## Frontend — npm audit

Ghi chú lúc lên kế hoạch: 17 cảnh báo, phần lớn ở công cụ dựng (Expo CLI, ESLint, config plugins), không nằm trong image
backend (stage `web` chỉ chép `dist`). **Không** dùng `npm audit fix --force` — nó hạ Expo 57 xuống 51. **Hoãn tới sau
buổi trình bày.**

Đo lại 2026-11-06 (`npm audit --json`, chỉ đọc): **25** cảnh báo (1 critical, 7 high, 16 moderate, 1 low) — nhiều hơn
17 do có advisory mới. Bản "fix" của npm hiện là `expo@52.0.49` (vẫn là hạ major).

⚠️ Chưa chắc "không nằm trong bản chạy": `expo-router` (high) kéo `query-string` và `decode-uri-component` (high) —
hai gói này chạy trong trình duyệt khi phân tích URL, nên có thể **nằm trong bundle web**. `zod` (high) chưa rõ có vào
bundle không. Cần kiểm bundle (`dist/_expo/static/js`) trước khi kết luận.
