import unittest

from src.api.routes import _get_model_alias_catalog, _get_openai_model_catalog


class ModelCatalogMetadataTests(unittest.TestCase):
    def test_openai_catalog_includes_concrete_metadata_for_omni(self):
        models = {item["id"]: item for item in _get_openai_model_catalog()}

        omni = models["gemini-omni-flash-10s-portrait"]
        self.assertFalse(omni["is_alias"])
        self.assertEqual(omni["type"], "video")
        self.assertEqual(omni["video_type"], "r2v")
        self.assertTrue(omni["supports_images"])
        self.assertEqual(omni["min_images"], 0)
        self.assertEqual(omni["max_images"], 3)

    def test_alias_catalog_exposes_omni_variant_parameters(self):
        aliases = {item["id"]: item for item in _get_model_alias_catalog()}

        omni = aliases["gemini-omni-flash"]
        self.assertTrue(omni["is_alias"])
        self.assertEqual(omni["video_type"], "r2v")
        self.assertEqual(omni["durations"], [4, 6, 8, 10])
        self.assertEqual(omni["aspects"], ["landscape", "portrait"])
        self.assertEqual(omni["min_images"], 0)
        self.assertEqual(omni["max_images"], 3)

    def test_alias_catalog_exposes_interpolation_and_extend_capabilities(self):
        aliases = {item["id"]: item for item in _get_model_alias_catalog()}

        interpolation = aliases["veo_3_1_interpolation_lite"]
        self.assertEqual(interpolation["video_type"], "i2v")
        self.assertEqual(interpolation["min_images"], 2)
        self.assertEqual(interpolation["max_images"], 2)
        self.assertEqual(interpolation["durations"], [4, 6])

        extend = aliases["veo_3_1_extend"]
        self.assertEqual(extend["video_type"], "extend")
        self.assertTrue(extend["requires_video_id"])


if __name__ == "__main__":
    unittest.main()
