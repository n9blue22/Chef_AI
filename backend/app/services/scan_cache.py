"""Cache đầu ra vision của /recognize trong RAM (docs/caching-audit.md mục 3).

Lưu Detected (tên nguyên liệu Gemini trả), không lưu kết quả đã chuẩn hoá: lúc trúng vẫn chuẩn hoá lại theo danh mục
hiện tại nên seed thêm nguyên liệu hay sửa bộ chuẩn hoá là có hiệu lực ngay. Không lưu ảnh, chỉ giữ sha256.
"""

import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable
from typing import NamedTuple

from app.services.vision.provider import Detected

SCAN_CACHE_MAX_ENTRIES = 200
SCAN_CACHE_TTL_SEC = 24 * 3600


class ScanCacheKey(NamedTuple):
    """Mỗi user một khoá riêng: cùng ảnh nhưng khác người thì không dùng chung."""

    user_id: str
    image_sha256: str
    vision_version: str


def scan_cache_key(user_id: str, upload: bytes, vision_version: str) -> ScanCacheKey:
    """Khoá từ bytes gốc của file (chỉ gọi sau khi ảnh đã qua kiểm định dạng và kích thước)."""
    return ScanCacheKey(user_id, hashlib.sha256(upload).hexdigest(), vision_version)


class ScanResultCache:
    """LRU + TTL, 1 instance dùng chung cả app. Server khởi động lại là mất, chấp nhận.
    ponytail: 2 request cùng ảnh gửi đồng thời đều trượt, cùng trừ lượt và gọi Gemini; gom request nếu thấy xảy ra."""

    def __init__(
        self, max_entries: int = SCAN_CACHE_MAX_ENTRIES, ttl_sec: float = SCAN_CACHE_TTL_SEC,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_entries = max_entries
        self._ttl_sec = ttl_sec
        self._clock = clock
        self._entries: OrderedDict[ScanCacheKey, tuple[float, Detected]] = OrderedDict()

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: ScanCacheKey) -> Detected | None:
        """Detected đã lưu, hoặc None nếu chưa có / đã quá TTL (mục quá hạn bị xoá luôn)."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, detected = entry
        if self._clock() - stored_at >= self._ttl_sec:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return detected

    def put(self, key: ScanCacheKey, detected: Detected) -> None:
        """Lưu kết quả; quá max_entries thì bỏ mục lâu không dùng nhất."""
        self._entries[key] = (self._clock(), detected)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)
