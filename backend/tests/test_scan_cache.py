"""ScanResultCache (TTL, LRU, khoá theo user + bytes ảnh) và mã phiên bản vision Gemini. Không gọi Gemini."""

import pytest

from app.services.scan_cache import SCAN_CACHE_TTL_SEC, ScanResultCache, scan_cache_key
from app.services.vision import gemini
from app.services.vision.provider import Detected

DETECTED = Detected(ingredients=["ức gà"], uncertain=[])


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_entry_expires_after_ttl() -> None:
    clock = FakeClock()
    cache = ScanResultCache(clock=clock)
    key = scan_cache_key("u1", b"anh", "v1")
    cache.put(key, DETECTED)

    clock.now += SCAN_CACHE_TTL_SEC - 1
    assert cache.get(key) == DETECTED
    clock.now += 1
    assert cache.get(key) is None and len(cache) == 0


def test_least_recently_used_entry_is_evicted_first() -> None:
    cache = ScanResultCache(max_entries=2)
    first, second, third = (scan_cache_key("u1", bytes([i]), "v1") for i in range(3))
    cache.put(first, DETECTED)
    cache.put(second, DETECTED)
    cache.get(first)  # first vừa dùng → second là mục lâu không dùng nhất
    cache.put(third, DETECTED)

    assert cache.get(second) is None
    assert cache.get(first) == DETECTED and cache.get(third) == DETECTED


def test_key_differs_by_user_image_and_version() -> None:
    base = scan_cache_key("u1", b"anh", "v1")

    assert scan_cache_key("u1", b"anh", "v1") == base
    assert scan_cache_key("u2", b"anh", "v1") != base
    assert scan_cache_key("u1", b"anH", "v1") != base
    assert scan_cache_key("u1", b"anh", "v2") != base


@pytest.mark.parametrize("name", ["GEMINI_MODEL", "SYSTEM_PROMPT", "USER_PROMPT"])
def test_gemini_version_changes_with_model_or_prompt(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    before = gemini.gemini_vision_version()
    monkeypatch.setattr(gemini, name, getattr(gemini, name) + " ")

    assert gemini.gemini_vision_version() != before
