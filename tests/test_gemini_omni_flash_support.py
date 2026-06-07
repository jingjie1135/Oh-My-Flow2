import json
import types
import unittest
from unittest.mock import AsyncMock

from fastapi import HTTPException

from src.api.routes import (
    _extract_prompt_and_images_from_gemini_contents,
    _get_gemini_model_catalog,
    _get_openai_model_catalog,
)
from src.core.account_tiers import (
    get_required_paygate_tier_for_model,
    supports_model_for_tier,
)
from src.core.model_resolver import resolve_model_name
from src.core.models import GeminiContent, GeminiInlineData, GeminiPart
from src.services.flow_client import FlowClient
from src.services.generation_handler import MODEL_CONFIG, GenerationHandler


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

    def test_resolve_string_duration_and_snake_case_aspect(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(duration="6s", aspect_ratio="portrait")
        )

        resolved = resolve_model_name(
            "gemini-omni-flash",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "gemini-omni-flash-6s-portrait")

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
                self.assertEqual(cfg["min_images"], 0)
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


class GeminiOmniFlashTierTests(unittest.TestCase):
    def test_tier_two_does_not_upgrade_omni_to_fake_ultra(self):
        handler = GenerationHandler.__new__(GenerationHandler)

        model_key, message = handler._resolve_video_model_key_for_tier(
            MODEL_CONFIG["gemini-omni-flash-10s-landscape"],
            "PAYGATE_TIER_TWO",
        )

        self.assertEqual(model_key, "abra_r2v_10s")
        self.assertIsNone(message)


class GeminiOmniFlashValidationTests(unittest.IsolatedAsyncioTestCase):
    def test_omni_allows_optional_reference_images(self):
        cfg = MODEL_CONFIG["gemini-omni-flash-4s-landscape"]

        self.assertEqual(cfg["video_type"], "r2v")
        self.assertEqual(cfg["min_images"], 0)
        self.assertEqual(cfg["max_images"], 3)

    async def test_omni_without_reference_images_uses_text_video(self):
        handler = GenerationHandler.__new__(GenerationHandler)
        handler.flow_client = types.SimpleNamespace(
            generate_video_text=AsyncMock(
                return_value={
                    "operations": [
                        {
                            "operation": {"name": "task-omni-text"},
                            "sceneId": "scene-1",
                        }
                    ]
                }
            )
        )
        handler._update_request_log_progress = AsyncMock()
        handler._resolve_video_model_key_for_tier = GenerationHandler._resolve_video_model_key_for_tier.__get__(
            handler,
            GenerationHandler,
        )
        handler._mark_generation_failed = GenerationHandler._mark_generation_failed.__get__(
            handler,
            GenerationHandler,
        )
        handler._create_error_response = GenerationHandler._create_error_response.__get__(
            handler,
            GenerationHandler,
        )
        handler._create_stream_chunk = GenerationHandler._create_stream_chunk.__get__(
            handler,
            GenerationHandler,
        )
        async def fake_poll_video_result(*args, **kwargs):
            yield json.dumps({"ok": True})

        handler._poll_video_result = fake_poll_video_result
        handler.db = types.SimpleNamespace(create_task=AsyncMock())

        token = types.SimpleNamespace(
            id=1,
            at="at-token",
            user_paygate_tier="PAYGATE_TIER_ONE",
            video_concurrency=-1,
        )
        generation_result = handler._create_generation_result()

        chunks = []
        async for chunk in handler._handle_video_generation(
            token=token,
            project_id="project-1",
            model_config=MODEL_CONFIG["gemini-omni-flash-4s-landscape"],
            prompt="生成视频",
            images=None,
            stream=False,
            generation_result=generation_result,
            request_log_state={},
        ):
            chunks.append(json.loads(chunk))

        handler.flow_client.generate_video_text.assert_awaited_once()
        kwargs = handler.flow_client.generate_video_text.await_args.kwargs
        self.assertEqual(kwargs["model_key"], "abra_r2v_4s")
        self.assertEqual(kwargs["aspect_ratio"], "VIDEO_ASPECT_RATIO_LANDSCAPE")
        self.assertEqual(kwargs["prompt"], "生成视频")
        self.assertEqual(chunks[-1], {"ok": True})


class GeminiOmniFlashFlowClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_reference_images_payload_uses_omni_model_key(self):
        client = FlowClient(proxy_manager=None)
        client._acquire_video_launch_gate = AsyncMock(return_value=(True, None, None))
        client._release_video_launch_gate = AsyncMock()
        client._get_recaptcha_token = AsyncMock(return_value=("recaptcha-token", "browser-1"))
        client._notify_browser_captcha_request_finished = AsyncMock()
        captured = {}

        async def fake_make_request(**kwargs):
            captured["url"] = kwargs["url"]
            captured["json_data"] = kwargs["json_data"]
            return {"operations": [{"operation": {"name": "task-omni"}}]}

        client._make_request = AsyncMock(side_effect=fake_make_request)

        await client.generate_video_reference_images(
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
        self.assertEqual(json_data["clientContext"]["userPaygateTier"], "PAYGATE_TIER_ONE")
        self.assertEqual(request_data["videoModelKey"], "abra_r2v_10s")
        self.assertEqual(request_data["aspectRatio"], "VIDEO_ASPECT_RATIO_PORTRAIT")
        self.assertEqual(len(request_data["referenceImages"]), 2)
        self.assertEqual(
            request_data["textInput"]["structuredPrompt"]["parts"][0]["text"],
            "角色在霓虹街道跳舞",
        )


class GeminiOmniFlashCatalogTests(unittest.TestCase):
    def test_openai_catalog_contains_omni_variant(self):
        ids = {item["id"] for item in _get_openai_model_catalog()}

        self.assertIn("gemini-omni-flash-4s-landscape", ids)
        self.assertIn("gemini-omni-flash-10s-portrait", ids)

    def test_gemini_catalog_contains_omni_alias(self):
        catalog = _get_gemini_model_catalog()

        self.assertIn("gemini-omni-flash", catalog)


class GeminiOmniFlashRouteBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_audio_inline_data_error_mentions_first_stage_image_only_support(self):
        contents = [
            GeminiContent(
                role="user",
                parts=[
                    GeminiPart(text="配音生成视频"),
                    GeminiPart(
                        inlineData=GeminiInlineData(
                            mimeType="audio/wav",
                            data="AAAA",
                        )
                    ),
                ],
            )
        ]

        with self.assertRaises(HTTPException) as exc_info:
            await _extract_prompt_and_images_from_gemini_contents(contents)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("Gemini Omni Flash first-stage support", exc_info.exception.detail)
        self.assertIn("text plus image references only", exc_info.exception.detail)


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


if __name__ == "__main__":
    unittest.main()
