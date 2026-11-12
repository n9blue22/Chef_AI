"""/recognize + cache đầu ra vision: thứ tự kiểm ảnh → tra cache → trừ lượt → gọi vision, header X-Cache.
Provider và limiter giả, không gọi Gemini / Supabase."""

import pytest

from app.api.deps import get_rate_limiter, require_user
from app.api.routes import ai
from app.main import app
from app.services.auth_tokens import CurrentUser
from app.services.rate_limit import POLICIES, RateLimiter
from app.services.vision.provider import Detected, VisionUnavailableError
from test_ai_routes import (  # noqa: F401 — no_db là fixture autouse: không đọc danh mục từ DB
    CHICKEN_ID, TEST_USER, FakeLimiter, FakeVision, client_with, image_bytes, no_db, post_image,
)

CHICKEN = Detected(ingredients=["ức gà"], uncertain=[])
OTHER_USER = CurrentUser(id="00000000-0000-0000-0000-00000000000b", access_token="test-token-b")


def current_scan_cache_size() -> int:
    return len(app.dependency_overrides[ai.get_ai_services]().scan_cache)


def test_same_user_same_image_hits_cache_without_daily_quota() -> None:
    vision, limiter = FakeVision(CHICKEN), FakeLimiter()
    client = client_with(vision=vision, limiter=limiter)
    first, second = post_image(client, image_bytes()), post_image(client, image_bytes())

    assert [first.headers["X-Cache"], second.headers["X-Cache"]] == ["MISS", "HIT"]
    assert first.json() == second.json() and first.json()["accepted_ids"] == [CHICKEN_ID]
    assert vision.calls == 1 and limiter.daily == ["recognize"]


def test_two_users_same_image_do_not_share_cache() -> None:
    vision, limiter = FakeVision(CHICKEN), FakeLimiter()
    client = client_with(vision=vision, limiter=limiter)
    current = [TEST_USER]
    app.dependency_overrides[ai.recognize_user] = lambda: current[0]

    first = post_image(client, image_bytes())
    current[0] = OTHER_USER
    second = post_image(client, image_bytes())

    assert [first.headers["X-Cache"], second.headers["X-Cache"]] == ["MISS", "MISS"]
    assert vision.calls == 2 and limiter.daily == ["recognize", "recognize"]


class OrderedLimiter(FakeLimiter):
    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events

    async def consume_daily(self, policy_name: str, user_id: str) -> None:
        self.events.append("quota")


class OrderedVision(FakeVision):
    def __init__(self, output: Detected | Exception, events: list[str]) -> None:
        super().__init__(output)
        self.events = events

    async def detect_ingredients(self, image: bytes, mime_type: str) -> Detected:
        self.events.append("vision")
        return await super().detect_ingredients(image, mime_type)


def test_miss_consumes_daily_quota_before_calling_vision_and_vision_error_still_costs() -> None:
    events: list[str] = []
    client = client_with(vision=OrderedVision(VisionUnavailableError("timeout"), events), limiter=OrderedLimiter(events))

    assert post_image(client, image_bytes()).status_code == 503
    assert events == ["quota", "vision"]


@pytest.mark.parametrize("failure", [VisionUnavailableError("timeout"), Detected(ingredients=[], uncertain=[]),
                                     Detected(ingredients=["sô cô la"], uncertain=[])],
                         ids=["vision-loi", "rong", "khong-khop-danh-muc"])
def test_failed_scan_is_not_cached(failure: Detected | Exception) -> None:
    vision, limiter = FakeVision(failure), FakeLimiter()
    client = client_with(vision=vision, limiter=limiter)
    failed = post_image(client, image_bytes())
    vision.output = CHICKEN
    retried = post_image(client, image_bytes())

    assert failed.status_code in (422, 503) and "X-Cache" not in failed.headers
    assert retried.status_code == 200 and retried.headers["X-Cache"] == "MISS"
    assert vision.calls == 2 and limiter.daily == ["recognize", "recognize"]


def test_invalid_image_is_not_cached_and_costs_no_daily_quota() -> None:
    vision, limiter = FakeVision(CHICKEN), FakeLimiter()
    client = client_with(vision=vision, limiter=limiter)
    broken = image_bytes(fmt="JPEG")[:100]

    assert [post_image(client, broken).status_code for _ in range(2)] == [415, 415]
    assert vision.calls == 0 and limiter.daily == [] and current_scan_cache_size() == 0


def test_vision_version_change_invalidates_cache() -> None:
    vision = FakeVision(CHICKEN)
    client = client_with(vision=vision)
    post_image(client, image_bytes())
    vision.version = "fake-v2"  # như đổi model hoặc prompt Gemini (xem test_scan_cache)

    assert post_image(client, image_bytes()).headers["X-Cache"] == "MISS" and vision.calls == 2


def test_image_differing_by_one_byte_misses() -> None:
    vision = FakeVision(CHICKEN)
    client = client_with(vision=vision)
    original = image_bytes(fmt="JPEG")
    assert original[6:11] == b"JFIF\0"
    tweaked = bytearray(original)
    tweaked[15] ^= 1  # byte thấp của mật độ điểm ảnh trong header JFIF: ảnh giải mã vẫn y hệt
    assert sum(a != b for a, b in zip(original, tweaked)) == 1

    responses = [post_image(client, data) for data in (original, bytes(tweaked))]
    assert [r.headers["X-Cache"] for r in responses] == ["MISS", "MISS"] and vision.calls == 2


class _Executable:
    def __init__(self, data: bool) -> None:
        self.data = data

    async def execute(self) -> "_Executable":
        return self


class AlwaysAllowAdmin:
    """Giả RPC consume_daily_quota luôn còn lượt; đếm số lần gọi."""

    def __init__(self) -> None:
        self.rpc_calls = 0

    def rpc(self, name: str, params: dict) -> _Executable:
        self.rpc_calls += 1
        return _Executable(True)


def test_per_minute_limit_still_counts_on_cache_hit() -> None:
    vision, admin = FakeVision(CHICKEN), AlwaysAllowAdmin()
    client = client_with(vision=vision)
    del app.dependency_overrides[ai.recognize_user]  # đi qua limit_user thật (hạn mức theo phút)
    app.dependency_overrides[require_user] = lambda: TEST_USER
    limiter = RateLimiter(admin)
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    per_minute = POLICIES["recognize"].windows[0].limit

    statuses = [post_image(client, image_bytes()).status_code for _ in range(per_minute + 1)]
    assert statuses == [200] * per_minute + [429]
    assert vision.calls == 1 and admin.rpc_calls == 1
