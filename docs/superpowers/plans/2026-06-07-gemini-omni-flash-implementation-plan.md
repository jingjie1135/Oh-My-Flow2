# Gemini Omni Flash Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Flow2API 中新增 Gemini Omni Flash 第一阶段支持：通过 OpenAI/Gemini 兼容入口提交 prompt + 参考图片，调用 Flow 的 reference-images 视频接口生成 4/6/8/10 秒横屏或竖屏视频。

**Architecture:** 第一阶段把 Gemini Omni Flash 作为现有 R2V 视频模型族接入，不实现完整对话式视频编辑、音频输入或视频输入。模型能力仍由 `src/services/generation_handler.py` 的 `MODEL_CONFIG` 驱动，简化模型名与 `duration/aspectRatio` 解析集中在 `src/core/model_resolver.py`，上游请求复用或薄封装 `FlowClient.generate_video_reference_images()` 的 V2 payload。

**Tech Stack:** Python 3.11, FastAPI, Pydantic, unittest, Flow `batchAsyncGenerateVideoReferenceImages` endpoint, OpenAI-compatible chat completions, Gemini `generateContent` / `streamGenerateContent` compatibility.

---

## Scope

### Included in this plan

- Public model alias: `gemini-omni-flash`.
- Internal model variants:
  - `gemini-omni-flash-4s-landscape`
  - `gemini-omni-flash-4s-portrait`
  - `gemini-omni-flash-6s-landscape`
  - `gemini-omni-flash-6s-portrait`
  - `gemini-omni-flash-8s-landscape`
  - `gemini-omni-flash-8s-portrait`
  - `gemini-omni-flash-10s-landscape`
  - `gemini-omni-flash-10s-portrait`
- Upstream model keys:
  - `4` seconds -> `abra_r2v_4s`
  - `6` seconds -> `abra_r2v_6s`
  - `8` seconds -> `abra_r2v_8s`
  - `10` seconds -> `abra_r2v_10s`
- Aspect support: `16:9` / `landscape`, `9:16` / `portrait`.
- Input support: text prompt plus 1-3 reference images, matching the current project README statement that Flow R2V supports at most 3 reference images.
- Gemini route support through `generationConfig.duration` and `generationConfig.aspectRatio`.
- OpenAI-compatible route support through extra fields such as `duration`, `aspect_ratio`, and `generationConfig`.

### Excluded from first stage

- Audio input.
- Video input.
- Conversational video editing.
- Start-frame and start/end-frame Omni workflows.
- Character-reference objects and named reference tokens such as `@Character1`.
- 7-reference-image support from third-party Omni gateway docs, because this project currently documents and enforces 3 images for Flow R2V.
- 4K/1080p upsample variants for Omni Flash.

## Evidence Summary

- Google / DeepMind public pages confirm Gemini Omni Flash is available in Gemini app, Google Flow, and YouTube Shorts, and supports text, image, audio, and video inputs with video output.
- Google public pages do not expose Flow's internal `videoModelKey` values or request schema.
- Public OSS evidence from `crisng95/flowboard` identifies Omni Flash R2V keys as `abra_r2v_4s`, `abra_r2v_6s`, `abra_r2v_8s`, and `abra_r2v_10s`, using `/v1/video:batchAsyncGenerateVideoReferenceImages` with `referenceImages[]` and V2 config.
- Third-party API docs for Gemini Omni Flash Video show duration values `4`, `6`, `8`, `10`, aspect ratios `16:9` and `9:16`, and state that start/end frame fields are not enabled for Omni Flash video generation.

## File Responsibility Map

| File | Responsibility in this change |
|------|-------------------------------|
| `src/services/generation_handler.py` | Define Omni model configs and ensure TIER_TWO does not auto-upgrade `abra_r2v_*` into fake Ultra keys. |
| `src/core/model_resolver.py` | Parse `duration` and `aspectRatio` for `gemini-omni-flash`, then resolve to an internal model key. |
| `src/api/routes.py` | Keep request normalization compatible with Gemini/OpenAI inputs; reject unsupported audio/video parts with clear errors. |
| `src/core/models.py` | Optionally document `generationConfig.duration` via Pydantic fields while preserving `extra="allow"`. |
| `src/services/flow_client.py` | Reuse or wrap `generate_video_reference_images()` for Omni's `referenceImages[]` V2 payload. |
| `src/core/account_tiers.py` | Decide whether `gemini-omni-flash` requires Pro tier and encode that rule if required. |
| `README.md` | Document the new model alias, supported parameters, unsupported modes, and examples. |
| `tests/test_gemini_omni_flash_support.py` | New focused regression tests for resolver, config, tier, route, and Flow payload behavior. |

---

## Task 1: Add Resolver Coverage for Omni Duration and Aspect

**Files:**
- Modify: `src/core/model_resolver.py`
- Create: `tests/test_gemini_omni_flash_support.py`

- [ ] **Step 1: Write failing resolver tests**

Add this initial test class to `tests/test_gemini_omni_flash_support.py`:

```python
import types
import unittest

from src.core.model_resolver import resolve_model_name
from src.services.generation_handler import MODEL_CONFIG


class GeminiOmniFlashResolverTests(unittest.TestCase):
    def test_resolve_default_alias_to_4s_landscape(self):
        request = types.SimpleNamespace(generationConfig=types.SimpleNamespace())

        resolved = resolve_model_name(
            "gemini-omni-flash",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "gemini-omni-flash-4s-landscape")

    def test_resolve_duration_and_portrait_aspect(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(duration=10, aspectRatio="9:16")
        )

        resolved = resolve_model_name(
            "gemini-omni-flash",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "gemini-omni-flash-10s-portrait")

    def test_invalid_duration_falls_back_to_default_4s(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(duration=5, aspectRatio="16:9")
        )

        resolved = resolve_model_name(
            "gemini-omni-flash",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "gemini-omni-flash-4s-landscape")
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashResolverTests
```

Expected before implementation: tests fail because `gemini-omni-flash` is not in `VIDEO_BASE_MODELS` and Omni variants are not in `MODEL_CONFIG`.

- [ ] **Step 3: Extend resolver helper return value**

In `src/core/model_resolver.py`, change `_extract_generation_params()` to return `(aspect_ratio, image_size, duration)` instead of `(aspect_ratio, image_size)`.

Add duration helpers near `_normalize_image_size()`:

```python
    def _normalize_duration(value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            text = value.strip().lower().removesuffix("s")
            if text.isdigit():
                return int(text)
        return None
```

Initialize and read duration alongside aspect and image size:

```python
    duration: Optional[int] = None

    gen_config = getattr(request, "generationConfig", None)
    if gen_config is not None:
        duration = _normalize_duration(_read_value(gen_config, "duration", "videoDuration", "video_duration"))
```

When parsing extra fields, also read duration:

```python
        if isinstance(gen_config_raw, dict) and duration is None:
            duration = _normalize_duration(
                gen_config_raw.get("duration")
                or gen_config_raw.get("videoDuration")
                or gen_config_raw.get("video_duration")
            )

        if duration is None:
            duration = _normalize_duration(
                extra.get("duration")
                or extra.get("videoDuration")
                or extra.get("video_duration")
            )
```

Return:

```python
    return aspect_ratio, image_size, duration
```

Update existing call sites in `resolve_model_name()`:

```python
        aspect_ratio, image_size, _duration = (
            _extract_generation_params(request) if request else (None, None, None)
        )
```

```python
        aspect_ratio, image_size, duration = (
            _extract_generation_params(request) if request else (None, None, None)
        )
```

- [ ] **Step 4: Add Omni alias resolution**

In `src/core/model_resolver.py`, add constants near `VIDEO_BASE_MODELS`:

```python
OMNI_FLASH_DURATIONS = (4, 6, 8, 10)
OMNI_FLASH_DEFAULT_DURATION = 4
```

Add the alias map:

```python
    "gemini-omni-flash": {
        "landscape": "gemini-omni-flash-4s-landscape",
        "portrait": "gemini-omni-flash-4s-portrait",
    },
```

Before `orientation_map = VIDEO_BASE_MODELS[model]`, add duration-aware resolution:

```python
        if model == "gemini-omni-flash":
            seconds = duration if duration in OMNI_FLASH_DURATIONS else OMNI_FLASH_DEFAULT_DURATION
            resolved = f"gemini-omni-flash-{seconds}s-{aspect_ratio}"
            if model_config and resolved in model_config:
                debug_logger.log_info(
                    f"[MODEL_RESOLVER] Omni Flash 模型名转换: {model} → {resolved} "
                    f"(aspectRatio={aspect_ratio}, duration={seconds}s)"
                )
                return resolved
            return model
```

- [ ] **Step 5: Run resolver tests again**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashResolverTests
```

Expected after Task 2 model config is also present: 3 tests pass.

---

## Task 2: Add Omni Flash Model Configs

**Files:**
- Modify: `src/services/generation_handler.py`
- Modify: `tests/test_gemini_omni_flash_support.py`

- [ ] **Step 1: Add model config tests**

Append this test class:

```python
class GeminiOmniFlashModelConfigTests(unittest.TestCase):
    def test_duration_variants_have_expected_model_keys(self):
        expected = {
            4: "abra_r2v_4s",
            6: "abra_r2v_6s",
            8: "abra_r2v_8s",
            10: "abra_r2v_10s",
        }

        for seconds, model_key in expected.items():
            for aspect in ("landscape", "portrait"):
                cfg = MODEL_CONFIG[f"gemini-omni-flash-{seconds}s-{aspect}"]
                self.assertEqual(cfg["type"], "video")
                self.assertEqual(cfg["video_type"], "r2v")
                self.assertEqual(cfg["model_key"], model_key)
                self.assertTrue(cfg["supports_images"])
                self.assertEqual(cfg["min_images"], 1)
                self.assertEqual(cfg["max_images"], 3)
                self.assertTrue(cfg["use_v2_model_config"])
                self.assertFalse(cfg["allow_tier_upgrade"])

    def test_portrait_and_landscape_aspect_constants(self):
        self.assertEqual(
            MODEL_CONFIG["gemini-omni-flash-4s-landscape"]["aspect_ratio"],
            "VIDEO_ASPECT_RATIO_LANDSCAPE",
        )
        self.assertEqual(
            MODEL_CONFIG["gemini-omni-flash-4s-portrait"]["aspect_ratio"],
            "VIDEO_ASPECT_RATIO_PORTRAIT",
        )
```

- [ ] **Step 2: Run model config tests and confirm failure**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashModelConfigTests
```

Expected before implementation: tests fail with missing `gemini-omni-flash-*` keys.

- [ ] **Step 3: Add config helpers**

In `src/services/generation_handler.py`, add constants after `MODEL_CONFIG` or near `_make_i2v_config()`:

```python
OMNI_FLASH_DURATION_KEYS = {
    4: "abra_r2v_4s",
    6: "abra_r2v_6s",
    8: "abra_r2v_8s",
    10: "abra_r2v_10s",
}

OMNI_FLASH_CREDIT_COST = {4: 15, 6: 20, 8: 25, 10: 30}
```

Add helper:

```python
def _make_omni_flash_config(model_key: str, aspect_ratio: str) -> Dict[str, Any]:
    return {
        "type": "video",
        "video_type": "r2v",
        "model_key": model_key,
        "aspect_ratio": aspect_ratio,
        "supports_images": True,
        "min_images": 1,
        "max_images": 3,
        "use_v2_model_config": True,
        "allow_tier_upgrade": False,
    }
```

Add registration function before `_apply_veo_3_1_model_updates()` is called:

```python
def _apply_gemini_omni_flash_model_updates():
    landscape = "VIDEO_ASPECT_RATIO_LANDSCAPE"
    portrait = "VIDEO_ASPECT_RATIO_PORTRAIT"

    for seconds, model_key in OMNI_FLASH_DURATION_KEYS.items():
        MODEL_CONFIG[f"gemini-omni-flash-{seconds}s-landscape"] = _make_omni_flash_config(
            model_key,
            landscape,
        )
        MODEL_CONFIG[f"gemini-omni-flash-{seconds}s-portrait"] = _make_omni_flash_config(
            model_key,
            portrait,
        )
```

Call it before or after `_apply_veo_3_1_model_updates()`:

```python
_apply_gemini_omni_flash_model_updates()
_apply_veo_3_1_model_updates()
```

- [ ] **Step 4: Run model config tests again**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashModelConfigTests
```

Expected: tests pass.

---

## Task 3: Preserve Omni Model Keys Across Tier Resolution

**Files:**
- Modify: `tests/test_gemini_omni_flash_support.py`
- Modify: `src/services/generation_handler.py` only if tests reveal a regression

- [ ] **Step 1: Add tier behavior test**

Append:

```python
class GeminiOmniFlashTierTests(unittest.TestCase):
    def test_tier_two_does_not_upgrade_omni_to_fake_ultra(self):
        handler = GenerationHandler.__new__(GenerationHandler)

        model_key, message = handler._resolve_video_model_key_for_tier(
            MODEL_CONFIG["gemini-omni-flash-10s-landscape"],
            "PAYGATE_TIER_TWO",
        )

        self.assertEqual(model_key, "abra_r2v_10s")
        self.assertIsNone(message)
```

- [ ] **Step 2: Run tier test**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashTierTests
```

Expected: pass because `allow_tier_upgrade` is false in Omni config.

- [ ] **Step 3: If the test fails, make tier upgrade opt-out authoritative**

If the test fails, keep `_resolve_video_model_key_for_tier()` behavior aligned with the existing lite-model pattern:

```python
        allow_tier_upgrade = bool(model_config.get("allow_tier_upgrade", True))

        if user_tier == "PAYGATE_TIER_TWO":
            if allow_tier_upgrade and "ultra" not in model_key:
                upgraded_model_key = _resolve_tier_two_model_key(model_key)
                if upgraded_model_key != model_key:
                    return upgraded_model_key, f"TIER_TWO 账号自动切换到 ultra 模型: {upgraded_model_key}"
            return model_key, None
```

---

## Task 4: Make R2V Validation Enforce Omni's Minimum Image Count

**Files:**
- Modify: `src/services/generation_handler.py`
- Modify: `tests/test_gemini_omni_flash_support.py`

- [ ] **Step 1: Add handler validation tests**

Append:

```python
class GeminiOmniFlashValidationTests(unittest.TestCase):
    def test_omni_requires_at_least_one_reference_image(self):
        cfg = MODEL_CONFIG["gemini-omni-flash-4s-landscape"]

        self.assertEqual(cfg["video_type"], "r2v")
        self.assertEqual(cfg["min_images"], 1)
        self.assertEqual(cfg["max_images"], 3)
```

This test pins the contract at config level. The implementation change below ensures runtime validation uses it.

- [ ] **Step 2: Update R2V runtime validation**

In `_handle_video_generation()` inside the `elif video_type == "r2v":` branch, replace the current max-only check with min/max validation:

```python
            elif video_type == "r2v":
                if image_count < min_images:
                    error_msg = f"❌ 多图视频模型至少需要 {min_images} 张参考图,当前提供了 {image_count} 张"
                    if stream:
                        yield self._create_stream_chunk(f"{error_msg}\n")
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=400)
                    return

                if max_images is not None and image_count > max_images:
                    error_msg = f"❌ 多图视频模型最多支持 {max_images} 张参考图,当前提供了 {image_count} 张"
                    if stream:
                        yield self._create_stream_chunk(f"{error_msg}\n")
                    self._mark_generation_failed(generation_result, error_msg)
                    yield self._create_error_response(error_msg, status_code=400)
                    return
```

- [ ] **Step 3: Run targeted support tests**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support
```

Expected: all tests in the new file pass.

---

## Task 5: Verify FlowClient Payload Compatibility

**Files:**
- Modify: `tests/test_gemini_omni_flash_support.py`
- Modify: `src/services/flow_client.py` only if the existing payload lacks required V2 fields

- [ ] **Step 1: Add payload test**

Append:

```python
from unittest.mock import AsyncMock

from src.services.flow_client import FlowClient


class GeminiOmniFlashFlowClientTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = FlowClient(proxy_manager=None)
        self.client._acquire_video_launch_gate = AsyncMock(return_value=(True, None, None))
        self.client._release_video_launch_gate = AsyncMock()
        self.client._get_recaptcha_token = AsyncMock(return_value=("recaptcha-token", "browser-1"))
        self.client._notify_browser_captcha_request_finished = AsyncMock()

    async def test_reference_images_payload_uses_omni_model_key(self):
        captured = {}

        async def fake_make_request(method, url, json_data, use_at, at_token, **kwargs):
            captured["url"] = url
            captured["json_data"] = json_data
            return {"operations": [{"operation": {"name": "task-omni"}}]}

        self.client._make_request = AsyncMock(side_effect=fake_make_request)

        await self.client.generate_video_reference_images(
            at="at-token",
            project_id="project-1",
            prompt="角色在霓虹街道跳舞",
            model_key="abra_r2v_10s",
            aspect_ratio="VIDEO_ASPECT_RATIO_PORTRAIT",
            reference_images=[
                {"imageUsageType": "IMAGE_USAGE_TYPE_ASSET", "mediaId": "media-1"},
                {"imageUsageType": "IMAGE_USAGE_TYPE_ASSET", "mediaId": "media-2"},
            ],
            user_paygate_tier="PAYGATE_TIER_ONE",
        )

        self.assertIn("batchAsyncGenerateVideoReferenceImages", captured["url"])
        json_data = captured["json_data"]
        request_data = json_data["requests"][0]
        self.assertTrue(json_data["useV2ModelConfig"])
        self.assertIn("batchId", json_data["mediaGenerationContext"])
        self.assertEqual(request_data["videoModelKey"], "abra_r2v_10s")
        self.assertEqual(request_data["aspectRatio"], "VIDEO_ASPECT_RATIO_PORTRAIT")
        self.assertEqual(len(request_data["referenceImages"]), 2)
        self.assertEqual(
            request_data["textInput"]["structuredPrompt"]["parts"][0]["text"],
            "角色在霓虹街道跳舞",
        )
```

- [ ] **Step 2: Run payload test**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashFlowClientTests
```

Expected: pass if existing R2V FlowClient payload is sufficient.

- [ ] **Step 3: Add a wrapper only if isolation is preferred**

If the team wants an Omni-specific method for future voice/character references, add this thin wrapper to `src/services/flow_client.py`:

```python
    async def generate_video_omni_reference_images(
        self,
        at: str,
        project_id: str,
        prompt: str,
        model_key: str,
        aspect_ratio: str,
        reference_images: List[Dict],
        user_paygate_tier: str = "PAYGATE_TIER_ONE",
        token_id: Optional[int] = None,
        token_video_concurrency: Optional[int] = None,
    ) -> dict:
        return await self.generate_video_reference_images(
            at=at,
            project_id=project_id,
            prompt=prompt,
            model_key=model_key,
            aspect_ratio=aspect_ratio,
            reference_images=reference_images,
            user_paygate_tier=user_paygate_tier,
            token_id=token_id,
            token_video_concurrency=token_video_concurrency,
        )
```

Do not add this wrapper if the existing method is clear enough; a direct reuse is smaller and matches project style.

---

## Task 6: Route-Level Gemini/OpenAI Compatibility

**Files:**
- Modify: `src/api/routes.py`
- Modify: `src/core/models.py`
- Modify: `tests/test_gemini_omni_flash_support.py`

- [ ] **Step 1: Add optional duration field for documentation clarity**

In `src/core/models.py`, extend `GenerationConfigParam`:

```python
class GenerationConfigParam(BaseModel):
    """Gemini generationConfig parameters (for model name resolution)"""

    responseModalities: Optional[List[str]] = None  # ["IMAGE", "TEXT"]
    imageConfig: Optional[ImageConfig] = None
    duration: Optional[Union[int, str]] = None  # Gemini Omni Flash: 4, 6, 8, 10
    aspectRatio: Optional[str] = None  # Video aliases may read this directly

    model_config = ConfigDict(extra="allow")
```

- [ ] **Step 2: Keep non-image Gemini parts explicitly unsupported**

In `src/api/routes.py`, keep the existing image-only extraction behavior. Update the error text in `_extract_prompt_and_images_from_gemini_contents()` so audio/video failures explain first-stage support:

```python
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Unsupported inlineData mime type for Flow2API media generation: "
                        f"{part.inlineData.mimeType}. Gemini Omni Flash first-stage support "
                        "accepts text plus image references only."
                    ),
                )
```

Apply the same wording for `fileData` non-image MIME types.

- [ ] **Step 3: Add route catalog tests**

Append lightweight catalog tests that do not require live Flow credentials:

```python
from src.api.routes import _get_gemini_model_catalog, _get_openai_model_catalog


class GeminiOmniFlashCatalogTests(unittest.TestCase):
    def test_openai_catalog_contains_omni_variant(self):
        ids = {item["id"] for item in _get_openai_model_catalog()}

        self.assertIn("gemini-omni-flash-4s-landscape", ids)
        self.assertIn("gemini-omni-flash-10s-portrait", ids)

    def test_gemini_catalog_contains_omni_alias(self):
        catalog = _get_gemini_model_catalog()

        self.assertIn("gemini-omni-flash", catalog)
```

- [ ] **Step 4: Run route/catalog tests**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashCatalogTests
```

Expected: pass after model config and resolver alias are implemented.

---

## Task 7: Account Tier Decision

**Files:**
- Modify: `src/core/account_tiers.py` if Omni should require paid accounts
- Modify: `tests/test_gemini_omni_flash_support.py`

- [ ] **Step 1: Choose the first-stage tier policy**

Use this policy for the first implementation: Gemini Omni Flash requires Pro tier because Google describes Flow access as available to Google AI subscribers, while YouTube Shorts availability is not relevant to this Flow API bridge.

- [ ] **Step 2: Add tier tests**

Append:

```python
from src.core.account_tiers import get_required_paygate_tier_for_model, supports_model_for_tier


class GeminiOmniFlashAccountTierTests(unittest.TestCase):
    def test_omni_requires_pro_tier(self):
        self.assertEqual(
            get_required_paygate_tier_for_model("gemini-omni-flash-4s-landscape"),
            "PAYGATE_TIER_ONE",
        )
        self.assertEqual(
            get_required_paygate_tier_for_model("abra_r2v_10s"),
            "PAYGATE_TIER_ONE",
        )

    def test_free_tier_cannot_use_omni(self):
        self.assertFalse(
            supports_model_for_tier(
                "gemini-omni-flash-4s-landscape",
                "PAYGATE_TIER_NOT_PAID",
            )
        )
        self.assertTrue(
            supports_model_for_tier(
                "gemini-omni-flash-4s-landscape",
                "PAYGATE_TIER_ONE",
            )
        )
```

- [ ] **Step 3: Implement tier rule**

In `src/core/account_tiers.py`, add this before the `_4k/_1080p/_ultra` checks:

```python
    if normalized.startswith("gemini-omni-flash") or normalized.startswith("abra_r2v_"):
        return PAYGATE_TIER_ONE
```

- [ ] **Step 4: Run tier tests**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support.GeminiOmniFlashAccountTierTests
```

Expected: pass.

---

## Task 8: README Documentation and Usage Examples

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add model table section under R2V**

Add after the existing R2V model table:

```markdown
#### Gemini Omni Flash（第一阶段）

🖼️ **支持 prompt + 1-3 张参考图片生成视频**

> 当前实现走 Flow 的 `batchAsyncGenerateVideoReferenceImages` 请求体。第一阶段不支持 audio/video 输入、对话式视频编辑、首帧/尾帧字段和角色对象。
> `generationConfig.duration` 支持 `4`、`6`、`8`、`10` 秒；`generationConfig.aspectRatio` 支持 `16:9` / `9:16`。

| 模型名称 | 说明 | 尺寸 |
|---------|------|------|
| `gemini-omni-flash` | Gemini Omni Flash 简化别名，默认 4 秒横屏 | 由参数决定 |
| `gemini-omni-flash-4s-landscape` | Omni Flash 4 秒 | 横屏 |
| `gemini-omni-flash-4s-portrait` | Omni Flash 4 秒 | 竖屏 |
| `gemini-omni-flash-6s-landscape` | Omni Flash 6 秒 | 横屏 |
| `gemini-omni-flash-6s-portrait` | Omni Flash 6 秒 | 竖屏 |
| `gemini-omni-flash-8s-landscape` | Omni Flash 8 秒 | 横屏 |
| `gemini-omni-flash-8s-portrait` | Omni Flash 8 秒 | 竖屏 |
| `gemini-omni-flash-10s-landscape` | Omni Flash 10 秒 | 横屏 |
| `gemini-omni-flash-10s-portrait` | Omni Flash 10 秒 | 竖屏 |
```

- [ ] **Step 2: Add OpenAI-compatible example**

Add near the multi-image video example:

````markdown
### Gemini Omni Flash 多图参考视频

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-omni-flash",
    "generationConfig": {
      "duration": 10,
      "aspectRatio": "9:16"
    },
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "让参考图中的角色在霓虹街道中跳舞，镜头平滑推进，保持角色身份一致"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<参考图1base64>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```
````

- [ ] **Step 3: Add Gemini generateContent example**

Add near existing Gemini official examples:

````markdown
### Gemini 官方 generateContent（Gemini Omni Flash 视频）

```bash
curl -X POST "http://localhost:8000/models/gemini-omni-flash:generateContent" \
  -H "x-goog-api-key: han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "根据参考图生成 10 秒竖屏视频，角色在雨夜街头缓慢转身"
          },
          {
            "inlineData": {
              "mimeType": "image/jpeg",
              "data": "<参考图base64>"
            }
          }
        ]
      }
    ],
    "generationConfig": {
      "duration": 10,
      "aspectRatio": "9:16"
    }
  }'
```
````

---

## Task 9: Full Verification

**Files:**
- Verify: `src/core/model_resolver.py`
- Verify: `src/services/generation_handler.py`
- Verify: `src/services/flow_client.py`
- Verify: `src/api/routes.py`
- Verify: `src/core/models.py`
- Verify: `src/core/account_tiers.py`
- Verify: `tests/test_gemini_omni_flash_support.py`
- Verify: `README.md`

- [ ] **Step 1: Run the new focused test file**

Run:

```bash
py -3.11 -m unittest tests.test_gemini_omni_flash_support
```

Expected: all tests pass.

- [ ] **Step 2: Run existing related video tests**

Run:

```bash
py -3.11 -m unittest tests.test_veo_lite_support
```

Expected: existing Veo 3.1 tests continue to pass.

- [ ] **Step 3: Run full unit suite**

Run:

```bash
py -3.11 -m unittest discover tests
```

Expected: all tests pass.

- [ ] **Step 4: Run compile check**

Run:

```bash
py -3.11 -m compileall main.py src tests
```

Expected: compileall completes without syntax errors.

- [ ] **Step 5: Run LSP diagnostics on changed Python files**

Check diagnostics for each changed Python file:

```text
src/core/model_resolver.py
src/services/generation_handler.py
src/services/flow_client.py
src/api/routes.py
src/core/models.py
src/core/account_tiers.py
tests/test_gemini_omni_flash_support.py
```

Expected: no diagnostics in the changed Python files.

- [ ] **Step 6: Manual API surface check with a stubbed handler**

Because real Flow credentials may not be available, manually verify the app surface by running a small in-process driver that calls resolver/catalog functions and a mocked handler route path. The minimum acceptable surface proof is:

```python
import types
from src.core.model_resolver import resolve_model_name
from src.services.generation_handler import MODEL_CONFIG
from src.api.routes import _get_gemini_model_catalog

request = types.SimpleNamespace(
    generationConfig=types.SimpleNamespace(duration=10, aspectRatio="9:16")
)
resolved = resolve_model_name("gemini-omni-flash", request=request, model_config=MODEL_CONFIG)
assert resolved == "gemini-omni-flash-10s-portrait"
assert MODEL_CONFIG[resolved]["model_key"] == "abra_r2v_10s"
assert "gemini-omni-flash" in _get_gemini_model_catalog()
print("surface_ok")
```

Run it with:

```bash
py -3.11 -c "import types; from src.core.model_resolver import resolve_model_name; from src.services.generation_handler import MODEL_CONFIG; from src.api.routes import _get_gemini_model_catalog; request=types.SimpleNamespace(generationConfig=types.SimpleNamespace(duration=10, aspectRatio='9:16')); resolved=resolve_model_name('gemini-omni-flash', request=request, model_config=MODEL_CONFIG); assert resolved == 'gemini-omni-flash-10s-portrait'; assert MODEL_CONFIG[resolved]['model_key'] == 'abra_r2v_10s'; assert 'gemini-omni-flash' in _get_gemini_model_catalog(); print('surface_ok')"
```

Expected: `surface_ok`.

---

## Commit Plan

Use focused Conventional Commit messages in Chinese:

1. `test: 增加 Gemini Omni Flash 接入测试`
2. `feat: 接入 Gemini Omni Flash R2V 模型`
3. `docs: 记录 Gemini Omni Flash 使用方式`

Before each commit, inspect:

```bash
git status --short
git diff --check
git diff --stat
```

## Self-Review Checklist

- [ ] The plan implements only first-stage Omni Flash R2V support.
- [ ] Audio/video input and conversational editing are explicitly excluded from the first stage.
- [ ] Duration mapping is concrete: 4/6/8/10 seconds to `abra_r2v_*` keys.
- [ ] Aspect mapping is concrete: landscape/portrait only.
- [ ] Omni configs opt out of fake Ultra key upgrades.
- [ ] Runtime R2V validation enforces at least one reference image.
- [ ] FlowClient payload verification asserts `referenceImages[]`, `useV2ModelConfig`, and `videoModelKey`.
- [ ] Documentation shows both OpenAI-compatible and Gemini-compatible examples.
- [ ] Verification includes focused tests, related existing tests, full unit tests, compile check, LSP diagnostics, and a small surface driver.
