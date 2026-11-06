# Ghi chú bảo mật phụ thuộc

Kiểm 2026-11-06. Chỉ nâng cận dưới của Pillow (mục "Pillow — đã xử lý"); các gói khác chưa nâng.

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

`requirements.txt` dùng `>=` nên image lấy bản mới nhất **tại lúc dựng**. Image đang chạy (dựng trước khi Pillow 13.0.0
ra) có thể còn các lỗi Pillow dưới đây — **chưa kiểm được trong image**.

### Cảnh báo ở venv local: có trên đường chạy thật không, khai thác từ xa được không

| Gói (bản local → bản sửa) | Số | Trên đường chạy thật? | Từ xa? |
|---|---|---|---|
| **pillow 12.3.0 → 13.0.0** | 39 | **Có, một phần.** `POST /api/v1/recognize` → `upload_image.prepare_image_for_vision`: `Image.open` **không giới hạn định dạng**, rồi `exif_transpose` + `convert("RGB")` giải mã ảnh, `save` JPEG. Lọt qua được: bộ giải mã TIFF (tile/strip, OOB read, heap overflow `_decodeTile`), libopenjp2 (JPEG 2000, heap **write**), BMP RLE / MSP RLE (cấp RAM vô hạn), XBM ReDoS, GIF comment bậc hai, `Exif.load` (CPU). Có thể: ghi comment JPEG sau ICC (comment từ ảnh gốc đi theo `info`), MPO/DCX/SPIDER `seek`. **Không** trên đường chạy: lưu TIFF/PDF, vẽ chữ, ImageMorph, rank filter, `Image.merge`, Arrow, TarIO, PILfont, WMF (chỉ Windows), EPS (image không có Ghostscript), FlashPix/MIC (không cài `olefile`). | **Có**, nhưng cần đăng nhập (JWT) và bị rate limit `recognize` (5/phút, 30/ngày). Tệ nhất: làm sập worker (DoS) hoặc hỏng bộ nhớ qua JPEG 2000/TIFF. |
| certifi 2026.7.22 → 2026.10.18 | 2 (trùng) | Có — kho CA cho kết nối ra Supabase/Groq/Gemini/Cloudflare (httpx). Còn tin root `emSign ECC Root CA - G3`. | Không trực tiếp: cần vừa MITM được đường ra của server vừa có chứng chỉ từ CA đó. |
| dnspython 2.8.0 → 2.9.0 | 1 | Không. Chỉ `email-validator` dùng khi `check_deliverability=True`; `EmailStr` của pydantic tắt cờ này → không tra DNS. | Không. |
| pyasn1 0.6.4 → 0.6.5 | 4 | Không. Qua `google-auth`/`pyasn1_modules`, chỉ giải mã khoá/chứng chỉ cục bộ; Gemini dùng API key. | Không. |
| filelock 4.0.3 → 4.2.1 | 14 | Không với request. `huggingface_hub`/`torch` khoá file cục bộ; image đặt `HF_HUB_OFFLINE=1`. | Không — cần quyền ghi file trên máy. |
| setuptools 84.0.0 → 84.1.0 | 1 | Không — chỉ lúc cài wheel trên Windows. | Không. |

## Pillow — đã xử lý

Lỗ hổng: 39 advisory ở Pillow < 13.0.0 (bảng trên). Phần lọt tới được từ `POST /api/v1/recognize` nằm ở các bộ giải mã
TIFF, JPEG 2000, BMP/MSP RLE, XBM, GIF — vì `Image.open` trước đây mở **mọi** định dạng Pillow biết (~40).

Đã làm:
1. **Giới hạn định dạng** (`backend/app/services/upload_image.py`, `ALLOWED_IMAGE_FORMATS = ("JPEG", "PNG", "WEBP")`):
   `Image.open(..., formats=...)` không thử bộ giải mã nào khác → TIFF/BMP/GIF/JPEG 2000… trả **415** JSON, không tới
   vision. MPO (JPEG nhiều khung của một số điện thoại Android) vẫn qua vì Pillow mở nó bằng bộ "JPEG". Ảnh hỏng (cắt
   cụt, sai CRC, rác sau header) ra `UnidentifiedImageError`/`OSError` → 415. Giới hạn điểm ảnh **có sẵn từ trước**:
   `MAX_IMAGE_PIXELS = 50_000_000` → 413, kiểm từ header trước khi giải nén. Test: `test_ai_routes.py::
   test_recognize_decodes_only_allowed_formats` (ảnh TIFF/BMP hợp lệ do Pillow tự tạo → 415; JPEG/PNG/WebP → 200).
2. **`pillow>=13.0.0`** trong `requirements.txt`: nội dung file đổi → Docker không dùng lại layer cũ, pip buộc lấy bản đã vá.
   pip-audit lại sau khi đổi: `requirements.txt` (resolve ra pillow 13.0.0) và `requirements-ml.txt` đều 0 cảnh báo.

Xác nhận trong image sau khi dựng (chưa dựng):

```
docker run --rm <image> python -c "import PIL; print(PIL.__version__)"   # phải >= 13.0.0
```

### HEIC (ảnh iPhone)

Backend **chưa bao giờ** đọc được HEIC: Pillow (12.3 lẫn 13.0) không có plugin HEIF, image không cài `pillow-heif` →
HEIC luôn trả 415, trước và sau thay đổi này. Frontend (đọc mã, chưa thử máy thật):
- Chụp bằng camera trong app (`expo-camera`, `takePictureAsync`) → JPEG. Không ảnh hưởng.
- Chọn từ thư viện trên **iOS** (`expo-image-picker` 57, `quality: 0.6`, `preferredAssetRepresentationMode` mặc định
  `current`): `ImageUtils.readDataAndFileExtension` giữ **nguyên dữ liệu** với ảnh HEIC (cũng như TIFF, BMP, WebP, AVIF, GIF),
  chỉ ảnh "khác" mới nén lại thành JPEG. Frontend luôn gắn nhãn `photo.jpg` / `image/jpeg` bất kể nội dung.
  → **Ảnh HEIC chọn từ thư viện iPhone gửi lên dưới dạng HEIC và bị 415** — lỗi có từ trước, chưa sửa. Hướng sửa (chờ duyệt):
  phía app đặt `preferredAssetRepresentationMode: Compatible` (iOS tự chuyển sang JPEG), hoặc phía backend cài `pillow-heif`.
- Chọn từ thư viện trên **Android**: `CompressionImageExporter` nén lại thành JPEG/PNG khi `quality < 1`.
- **Web**: gửi nguyên file người dùng chọn (`ExponentImagePicker.web.ts`: `FileReader`/`createObjectURL`, không nén lại; `quality` không tác dụng).
- Định dạng **mới bị chặn** so với trước (trước đây qua được): GIF, AVIF, BMP, TIFF… chọn từ thư viện iOS hoặc web.

## Frontend — npm audit

Ghi chú lúc lên kế hoạch: 17 cảnh báo, phần lớn ở công cụ dựng (Expo CLI, ESLint, config plugins), không nằm trong image
backend (stage `web` chỉ chép `dist`). **Không** dùng `npm audit fix --force` — nó hạ Expo 57 xuống 51. **Hoãn tới sau
buổi trình bày.**

Đo lại 2026-11-06 (`npm audit --json`, chỉ đọc): **25** cảnh báo (1 critical, 7 high, 16 moderate, 1 low) — nhiều hơn
17 do có advisory mới. Bản "fix" của npm hiện là `expo@52.0.49` (vẫn là hạ major).

⚠️ Chưa chắc "không nằm trong bản chạy": `expo-router` (high) kéo `query-string` và `decode-uri-component` (high) —
hai gói này chạy trong trình duyệt khi phân tích URL, nên có thể **nằm trong bundle web**. `zod` (high) chưa rõ có vào
bundle không. Cần kiểm bundle (`dist/_expo/static/js`) trước khi kết luận.
