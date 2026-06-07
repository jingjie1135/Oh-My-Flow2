import types
import unittest

from src.core.model_resolver import get_model_alias_metadata, resolve_model_name
from src.services.generation_handler import MODEL_CONFIG


class ModelVariantResolverTests(unittest.TestCase):
    def test_quality_t2v_alias_uses_duration_resolution_and_aspect(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(
                duration=4,
                aspectRatio="9:16",
                imageSize="4k",
            )
        )

        resolved = resolve_model_name(
            "veo_3_1_t2v",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "veo_3_1_t2v_portrait_4s_4k")

    def test_quality_i2v_alias_uses_duration_resolution_and_aspect(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(
                duration="6s",
                aspectRatio="portrait",
                resolution="1080p",
            )
        )

        resolved = resolve_model_name(
            "veo_3_1_i2v_s",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "veo_3_1_i2v_s_portrait_6s_1080p")

    def test_lite_t2v_alias_uses_duration_and_aspect(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(duration=6, aspectRatio="9:16")
        )

        resolved = resolve_model_name(
            "veo_3_1_t2v_lite",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "veo_3_1_t2v_lite_6s_portrait")

    def test_r2v_ultra_alias_uses_resolution_and_aspect(self):
        request = types.SimpleNamespace(
            generationConfig=types.SimpleNamespace(aspectRatio="portrait", imageSize="4k")
        )

        resolved = resolve_model_name(
            "veo_3_1_r2v_fast_ultra",
            request=request,
            model_config=MODEL_CONFIG,
        )

        self.assertEqual(resolved, "veo_3_1_r2v_fast_portrait_ultra_4k")

    def test_interpolation_lite_alias_metadata_requires_two_images(self):
        metadata = get_model_alias_metadata()

        self.assertEqual(metadata["veo_3_1_interpolation_lite"]["video_type"], "i2v")
        self.assertEqual(metadata["veo_3_1_interpolation_lite"]["min_images"], 2)
        self.assertEqual(metadata["veo_3_1_interpolation_lite"]["max_images"], 2)
        self.assertEqual(metadata["veo_3_1_interpolation_lite"]["durations"], [4, 6])

    def test_omni_alias_metadata_exposes_duration_and_image_limits(self):
        metadata = get_model_alias_metadata()

        self.assertEqual(metadata["gemini-omni-flash"]["video_type"], "r2v")
        self.assertEqual(metadata["gemini-omni-flash"]["durations"], [4, 6, 8, 10])
        self.assertEqual(metadata["gemini-omni-flash"]["min_images"], 0)
        self.assertEqual(metadata["gemini-omni-flash"]["max_images"], 3)


if __name__ == "__main__":
    unittest.main()
