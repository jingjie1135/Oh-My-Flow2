"""Model name resolver - converts simplified model names + generationConfig params to internal MODEL_CONFIG keys.

When upstream services (e.g. New API) send requests with a generic model name
along with generationConfig containing aspectRatio / imageSize, this module
resolves them to the specific internal model name used by flow2api.

Example:
    model = "gemini-3.0-pro-image"
    generationConfig.imageConfig.aspectRatio = "16:9"
    generationConfig.imageConfig.imageSize = "2k"
    → resolved to "gemini-3.0-pro-image-landscape-2k"
"""

import re
from typing import Optional, Dict, Any, Tuple, List
from ..core.logger import debug_logger

# ──────────────────────────────────────────────
# 简化模型名 → 基础模型名前缀 的映射
# ──────────────────────────────────────────────
IMAGE_BASE_MODELS = {
    # Gemini 3.0 Pro (GEM_PIX_2)
    "gemini-3.0-pro-image": "gemini-3.0-pro-image",
    # Gemini 3.1 Flash (NARWHAL)
    "gemini-3.1-flash-image": "gemini-3.1-flash-image",
    # Imagen 4.0 (IMAGEN_3_5)
    "imagen-4.0-generate-preview": "imagen-4.0-generate-preview",
}

# ──────────────────────────────────────────────
# aspectRatio 转换映射
# 支持 Gemini 原生格式 ("16:9") 和内部格式 ("landscape")
# ──────────────────────────────────────────────
ASPECT_RATIO_MAP = {
    # Gemini 标准 ratio 格式
    "16:9": "landscape",
    "9:16": "portrait",
    "1:1": "square",
    "4:3": "four-three",
    "3:4": "three-four",
    # 英文名直接映射
    "landscape": "landscape",
    "portrait": "portrait",
    "square": "square",
    "four-three": "four-three",
    "three-four": "three-four",
    "four_three": "four-three",
    "three_four": "three-four",
    # 大写形式
    "LANDSCAPE": "landscape",
    "PORTRAIT": "portrait",
    "SQUARE": "square",
}

# 每个基础模型支持的 aspectRatio 列表
# 如果请求的 ratio 不在支持列表中，降级到默认值
MODEL_SUPPORTED_ASPECTS = {
    "gemini-3.0-pro-image": [
        "landscape",
        "portrait",
        "square",
        "four-three",
        "three-four",
    ],
    "gemini-3.1-flash-image": [
        "landscape",
        "portrait",
        "square",
        "four-three",
        "three-four",
    ],
    "imagen-4.0-generate-preview": ["landscape", "portrait"],
}

# 每个基础模型支持的 imageSize（分辨率）列表
MODEL_SUPPORTED_SIZES = {
    "gemini-3.0-pro-image": ["2k", "4k"],
    "gemini-3.1-flash-image": ["2k", "4k"],
    "imagen-4.0-generate-preview": [],  # 不支持放大
}

# imageSize 归一化映射
IMAGE_SIZE_MAP = {
    "1k": "1k",
    "1K": "1k",
    "2k": "2k",
    "2K": "2k",
    "4k": "4k",
    "4K": "4k",
    "1080p": "1080p",
    "1080P": "1080p",
    "": "",
}

# 默认 aspectRatio
DEFAULT_ASPECT = "landscape"

OMNI_FLASH_DURATIONS = (4, 6, 8, 10)
OMNI_FLASH_DEFAULT_DURATION = 4

OPENAI_IMAGE_SIZE_RE = re.compile(r"^(?P<w>\d{2,5})\s*[xX]\s*(?P<h>\d{2,5})$")

# OpenAI 常见 quality → imageSize 映射
# - 这里的 imageSize 是 flow2api 的“放大档位”，并不等价于 OpenAI 的像素尺寸；
#   但可用作“画质/清晰度”的近似映射。
OPENAI_QUALITY_MAP = {
    "low": None,
    "standard": None,
    "medium": "2k",
    "high": "4k",
    "hd": "4k",
    "ultra": "4k",
}

# 用于把 OpenAI size（如 1024x1792）映射到最接近的 flow2api aspect 选项
ASPECT_RATIO_FLOAT_MAP = {
    "landscape": 16 / 9,
    "portrait": 9 / 16,
    "square": 1.0,
    "four-three": 4 / 3,
    "three-four": 3 / 4,
}


# ──────────────────────────────────────────────
# 视频模型简化名映射
# ──────────────────────────────────────────────
VIDEO_BASE_MODELS = {
    # T2V models
    "veo_3_1_t2v_fast": {
        "landscape": "veo_3_1_t2v_fast_landscape",
        "portrait": "veo_3_1_t2v_fast_portrait",
    },
    "veo_3_1_t2v_fast_4s": {
        "landscape": "veo_3_1_t2v_fast_4s",
        "portrait": "veo_3_1_t2v_fast_portrait_4s",
    },
    "veo_3_1_t2v_fast_6s": {
        "landscape": "veo_3_1_t2v_fast_6s",
        "portrait": "veo_3_1_t2v_fast_portrait_6s",
    },
    "veo_3_1_t2v_fast_ultra": {
        "landscape": "veo_3_1_t2v_fast_ultra",
        "portrait": "veo_3_1_t2v_fast_portrait_ultra",
    },
    "veo_3_1_t2v_fast_ultra_relaxed": {
        "landscape": "veo_3_1_t2v_fast_ultra_relaxed",
        "portrait": "veo_3_1_t2v_fast_portrait_ultra_relaxed",
    },
    "veo_3_1_t2v": {
        "landscape": "veo_3_1_t2v_landscape",
        "portrait": "veo_3_1_t2v_portrait",
    },
    "veo_3_1_t2v_4s": {
        "landscape": "veo_3_1_t2v_4s",
        "portrait": "veo_3_1_t2v_portrait_4s",
    },
    "veo_3_1_t2v_6s": {
        "landscape": "veo_3_1_t2v_6s",
        "portrait": "veo_3_1_t2v_portrait_6s",
    },
    "veo_3_1_t2v_4s_4k": {
        "landscape": "veo_3_1_t2v_4s_4k",
        "portrait": "veo_3_1_t2v_portrait_4s_4k",
    },
    "veo_3_1_t2v_4s_1080p": {
        "landscape": "veo_3_1_t2v_4s_1080p",
        "portrait": "veo_3_1_t2v_portrait_4s_1080p",
    },
    "veo_3_1_t2v_6s_4k": {
        "landscape": "veo_3_1_t2v_6s_4k",
        "portrait": "veo_3_1_t2v_portrait_6s_4k",
    },
    "veo_3_1_t2v_6s_1080p": {
        "landscape": "veo_3_1_t2v_6s_1080p",
        "portrait": "veo_3_1_t2v_portrait_6s_1080p",
    },
    "veo_3_1_t2v_4k": {
        "landscape": "veo_3_1_t2v_4k",
        "portrait": "veo_3_1_t2v_portrait_4k",
    },
    "veo_3_1_t2v_1080p": {
        "landscape": "veo_3_1_t2v_1080p",
        "portrait": "veo_3_1_t2v_portrait_1080p",
    },
    "veo_3_1_t2v_lite": {
        "landscape": "veo_3_1_t2v_lite_landscape",
        "portrait": "veo_3_1_t2v_lite_portrait",
    },
    "veo_3_1_t2v_lite_4s": {
        "landscape": "veo_3_1_t2v_lite_4s_landscape",
        "portrait": "veo_3_1_t2v_lite_4s_portrait",
    },
    "veo_3_1_t2v_lite_6s": {
        "landscape": "veo_3_1_t2v_lite_6s_landscape",
        "portrait": "veo_3_1_t2v_lite_6s_portrait",
    },
    # I2V models
    "veo_3_1_i2v_s_fast_fl": {
        "landscape": "veo_3_1_i2v_s_fast_fl",
        "portrait": "veo_3_1_i2v_s_fast_portrait_fl",
    },
    "veo_3_1_i2v_s_fast_4s_fl": {
        "landscape": "veo_3_1_i2v_s_fast_4s_fl",
        "portrait": "veo_3_1_i2v_s_fast_portrait_4s_fl",
    },
    "veo_3_1_i2v_s_fast_6s_fl": {
        "landscape": "veo_3_1_i2v_s_fast_6s_fl",
        "portrait": "veo_3_1_i2v_s_fast_portrait_6s_fl",
    },
    "veo_3_1_i2v_s_fast_ultra_fl": {
        "landscape": "veo_3_1_i2v_s_fast_ultra_fl",
        "portrait": "veo_3_1_i2v_s_fast_portrait_ultra_fl",
    },
    "veo_3_1_i2v_s_fast_ultra_relaxed": {
        "landscape": "veo_3_1_i2v_s_fast_ultra_relaxed",
        "portrait": "veo_3_1_i2v_s_fast_portrait_ultra_relaxed",
    },
    "veo_3_1_i2v_s": {
        "landscape": "veo_3_1_i2v_s_landscape",
        "portrait": "veo_3_1_i2v_s_portrait",
    },
    "veo_3_1_i2v_s_4s": {
        "landscape": "veo_3_1_i2v_s_4s",
        "portrait": "veo_3_1_i2v_s_portrait_4s",
    },
    "veo_3_1_i2v_s_6s": {
        "landscape": "veo_3_1_i2v_s_6s",
        "portrait": "veo_3_1_i2v_s_portrait_6s",
    },
    "veo_3_1_i2v_s_4s_4k": {
        "landscape": "veo_3_1_i2v_s_4s_4k",
        "portrait": "veo_3_1_i2v_s_portrait_4s_4k",
    },
    "veo_3_1_i2v_s_4s_1080p": {
        "landscape": "veo_3_1_i2v_s_4s_1080p",
        "portrait": "veo_3_1_i2v_s_portrait_4s_1080p",
    },
    "veo_3_1_i2v_s_6s_4k": {
        "landscape": "veo_3_1_i2v_s_6s_4k",
        "portrait": "veo_3_1_i2v_s_portrait_6s_4k",
    },
    "veo_3_1_i2v_s_6s_1080p": {
        "landscape": "veo_3_1_i2v_s_6s_1080p",
        "portrait": "veo_3_1_i2v_s_portrait_6s_1080p",
    },
    "veo_3_1_i2v_s_4k": {
        "landscape": "veo_3_1_i2v_s_4k",
        "portrait": "veo_3_1_i2v_s_portrait_4k",
    },
    "veo_3_1_i2v_s_1080p": {
        "landscape": "veo_3_1_i2v_s_1080p",
        "portrait": "veo_3_1_i2v_s_portrait_1080p",
    },
    "veo_3_1_i2v_lite": {
        "landscape": "veo_3_1_i2v_lite_landscape",
        "portrait": "veo_3_1_i2v_lite_portrait",
    },
    "veo_3_1_i2v_lite_4s": {
        "landscape": "veo_3_1_i2v_lite_4s_landscape",
        "portrait": "veo_3_1_i2v_lite_4s_portrait",
    },
    "veo_3_1_i2v_lite_6s": {
        "landscape": "veo_3_1_i2v_lite_6s_landscape",
        "portrait": "veo_3_1_i2v_lite_6s_portrait",
    },
    "veo_3_1_interpolation_lite": {
        "landscape": "veo_3_1_interpolation_lite_landscape",
        "portrait": "veo_3_1_interpolation_lite_portrait",
    },
    "veo_3_1_interpolation_lite_4s": {
        "landscape": "veo_3_1_interpolation_lite_4s_landscape",
        "portrait": "veo_3_1_interpolation_lite_4s_portrait",
    },
    "veo_3_1_interpolation_lite_6s": {
        "landscape": "veo_3_1_interpolation_lite_6s_landscape",
        "portrait": "veo_3_1_interpolation_lite_6s_portrait",
    },
    # R2V models
    "veo_3_1_r2v_fast": {
        "landscape": "veo_3_1_r2v_fast",
        "portrait": "veo_3_1_r2v_fast_portrait",
    },
    "veo_3_1_r2v_fast_ultra": {
        "landscape": "veo_3_1_r2v_fast_ultra",
        "portrait": "veo_3_1_r2v_fast_portrait_ultra",
    },
    "veo_3_1_r2v_fast_ultra_relaxed": {
        "landscape": "veo_3_1_r2v_fast_ultra_relaxed",
        "portrait": "veo_3_1_r2v_fast_portrait_ultra_relaxed",
    },
    "gemini-omni-flash": {
        "landscape": "gemini-omni-flash-4s-landscape",
        "portrait": "gemini-omni-flash-4s-portrait",
    },
    # Extend models (视频续写)
    "veo_3_1_extend": {
        "landscape": "veo_3_1_extend",
        "portrait": "veo_3_1_extend_portrait",
    },
}


def _aspect_pair(landscape: str, portrait: str) -> Dict[str, str]:
    return {"landscape": landscape, "portrait": portrait}


def _video_selector(
    video_type: str,
    variants: Dict[Tuple[Optional[int], Optional[str]], Dict[str, str]],
    *,
    durations: Optional[List[int]] = None,
    resolutions: Optional[List[str]] = None,
    min_images: Optional[int] = None,
    max_images: Optional[int] = None,
    supports_images: bool = False,
    requires_video_id: bool = False,
    default_duration: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "type": "video",
        "video_type": video_type,
        "aspects": ["landscape", "portrait"],
        "durations": durations or [],
        "resolutions": resolutions or [],
        "min_images": min_images,
        "max_images": max_images,
        "supports_images": supports_images,
        "requires_video_id": requires_video_id,
        "default_duration": default_duration,
        "variants": variants,
    }


VIDEO_ALIAS_SELECTORS: Dict[str, Dict[str, Any]] = {
    "veo_3_1_t2v_fast": _video_selector(
        "t2v",
        {
            (None, None): _aspect_pair("veo_3_1_t2v_fast_landscape", "veo_3_1_t2v_fast_portrait"),
            (4, None): _aspect_pair("veo_3_1_t2v_fast_4s", "veo_3_1_t2v_fast_portrait_4s"),
            (6, None): _aspect_pair("veo_3_1_t2v_fast_6s", "veo_3_1_t2v_fast_portrait_6s"),
            (None, "4k"): _aspect_pair("veo_3_1_t2v_fast_4k", "veo_3_1_t2v_fast_portrait_4k"),
            (None, "1080p"): _aspect_pair("veo_3_1_t2v_fast_1080p", "veo_3_1_t2v_fast_portrait_1080p"),
        },
        durations=[4, 6],
        resolutions=["1080p", "4k"],
    ),
    "veo_3_1_t2v_fast_ultra": _video_selector(
        "t2v",
        {
            (None, None): _aspect_pair("veo_3_1_t2v_fast_ultra", "veo_3_1_t2v_fast_portrait_ultra"),
            (None, "4k"): _aspect_pair("veo_3_1_t2v_fast_ultra_4k", "veo_3_1_t2v_fast_portrait_ultra_4k"),
            (None, "1080p"): _aspect_pair("veo_3_1_t2v_fast_ultra_1080p", "veo_3_1_t2v_fast_portrait_ultra_1080p"),
        },
        resolutions=["1080p", "4k"],
    ),
    "veo_3_1_t2v_fast_ultra_relaxed": _video_selector(
        "t2v",
        {
            (None, None): _aspect_pair(
                "veo_3_1_t2v_fast_ultra_relaxed",
                "veo_3_1_t2v_fast_portrait_ultra_relaxed",
            )
        },
    ),
    "veo_3_1_t2v": _video_selector(
        "t2v",
        {
            (None, None): _aspect_pair("veo_3_1_t2v_landscape", "veo_3_1_t2v_portrait"),
            (4, None): _aspect_pair("veo_3_1_t2v_4s", "veo_3_1_t2v_portrait_4s"),
            (6, None): _aspect_pair("veo_3_1_t2v_6s", "veo_3_1_t2v_portrait_6s"),
            (None, "4k"): _aspect_pair("veo_3_1_t2v_4k", "veo_3_1_t2v_portrait_4k"),
            (None, "1080p"): _aspect_pair("veo_3_1_t2v_1080p", "veo_3_1_t2v_portrait_1080p"),
            (4, "4k"): _aspect_pair("veo_3_1_t2v_4s_4k", "veo_3_1_t2v_portrait_4s_4k"),
            (4, "1080p"): _aspect_pair("veo_3_1_t2v_4s_1080p", "veo_3_1_t2v_portrait_4s_1080p"),
            (6, "4k"): _aspect_pair("veo_3_1_t2v_6s_4k", "veo_3_1_t2v_portrait_6s_4k"),
            (6, "1080p"): _aspect_pair("veo_3_1_t2v_6s_1080p", "veo_3_1_t2v_portrait_6s_1080p"),
        },
        durations=[4, 6],
        resolutions=["1080p", "4k"],
    ),
    "veo_3_1_t2v_lite": _video_selector(
        "t2v",
        {
            (None, None): _aspect_pair("veo_3_1_t2v_lite_landscape", "veo_3_1_t2v_lite_portrait"),
            (4, None): _aspect_pair("veo_3_1_t2v_lite_4s_landscape", "veo_3_1_t2v_lite_4s_portrait"),
            (6, None): _aspect_pair("veo_3_1_t2v_lite_6s_landscape", "veo_3_1_t2v_lite_6s_portrait"),
        },
        durations=[4, 6],
    ),
    "veo_3_1_i2v_s_fast_fl": _video_selector(
        "i2v",
        {
            (None, None): _aspect_pair("veo_3_1_i2v_s_fast_fl", "veo_3_1_i2v_s_fast_portrait_fl"),
            (4, None): _aspect_pair("veo_3_1_i2v_s_fast_4s_fl", "veo_3_1_i2v_s_fast_portrait_4s_fl"),
            (6, None): _aspect_pair("veo_3_1_i2v_s_fast_6s_fl", "veo_3_1_i2v_s_fast_portrait_6s_fl"),
        },
        durations=[4, 6],
        supports_images=True,
        min_images=1,
        max_images=2,
    ),
    "veo_3_1_i2v_s_fast_ultra_fl": _video_selector(
        "i2v",
        {
            (None, None): _aspect_pair("veo_3_1_i2v_s_fast_ultra_fl", "veo_3_1_i2v_s_fast_portrait_ultra_fl"),
            (None, "4k"): _aspect_pair("veo_3_1_i2v_s_fast_ultra_fl_4k", "veo_3_1_i2v_s_fast_portrait_ultra_fl_4k"),
            (None, "1080p"): _aspect_pair("veo_3_1_i2v_s_fast_ultra_fl_1080p", "veo_3_1_i2v_s_fast_portrait_ultra_fl_1080p"),
        },
        resolutions=["1080p", "4k"],
        supports_images=True,
        min_images=1,
        max_images=2,
    ),
    "veo_3_1_i2v_s_fast_ultra_relaxed": _video_selector(
        "i2v",
        {
            (None, None): _aspect_pair(
                "veo_3_1_i2v_s_fast_ultra_relaxed",
                "veo_3_1_i2v_s_fast_portrait_ultra_relaxed",
            )
        },
        supports_images=True,
        min_images=1,
        max_images=2,
    ),
    "veo_3_1_i2v_s": _video_selector(
        "i2v",
        {
            (None, None): _aspect_pair("veo_3_1_i2v_s_landscape", "veo_3_1_i2v_s_portrait"),
            (4, None): _aspect_pair("veo_3_1_i2v_s_4s", "veo_3_1_i2v_s_portrait_4s"),
            (6, None): _aspect_pair("veo_3_1_i2v_s_6s", "veo_3_1_i2v_s_portrait_6s"),
            (None, "4k"): _aspect_pair("veo_3_1_i2v_s_4k", "veo_3_1_i2v_s_portrait_4k"),
            (None, "1080p"): _aspect_pair("veo_3_1_i2v_s_1080p", "veo_3_1_i2v_s_portrait_1080p"),
            (4, "4k"): _aspect_pair("veo_3_1_i2v_s_4s_4k", "veo_3_1_i2v_s_portrait_4s_4k"),
            (4, "1080p"): _aspect_pair("veo_3_1_i2v_s_4s_1080p", "veo_3_1_i2v_s_portrait_4s_1080p"),
            (6, "4k"): _aspect_pair("veo_3_1_i2v_s_6s_4k", "veo_3_1_i2v_s_portrait_6s_4k"),
            (6, "1080p"): _aspect_pair("veo_3_1_i2v_s_6s_1080p", "veo_3_1_i2v_s_portrait_6s_1080p"),
        },
        durations=[4, 6],
        resolutions=["1080p", "4k"],
        supports_images=True,
        min_images=1,
        max_images=2,
    ),
    "veo_3_1_i2v_lite": _video_selector(
        "i2v",
        {
            (None, None): _aspect_pair("veo_3_1_i2v_lite_landscape", "veo_3_1_i2v_lite_portrait"),
            (4, None): _aspect_pair("veo_3_1_i2v_lite_4s_landscape", "veo_3_1_i2v_lite_4s_portrait"),
            (6, None): _aspect_pair("veo_3_1_i2v_lite_6s_landscape", "veo_3_1_i2v_lite_6s_portrait"),
        },
        durations=[4, 6],
        supports_images=True,
        min_images=1,
        max_images=1,
    ),
    "veo_3_1_interpolation_lite": _video_selector(
        "i2v",
        {
            (None, None): _aspect_pair("veo_3_1_interpolation_lite_landscape", "veo_3_1_interpolation_lite_portrait"),
            (4, None): _aspect_pair("veo_3_1_interpolation_lite_4s_landscape", "veo_3_1_interpolation_lite_4s_portrait"),
            (6, None): _aspect_pair("veo_3_1_interpolation_lite_6s_landscape", "veo_3_1_interpolation_lite_6s_portrait"),
        },
        durations=[4, 6],
        supports_images=True,
        min_images=2,
        max_images=2,
    ),
    "veo_3_1_r2v_fast": _video_selector(
        "r2v",
        {(None, None): _aspect_pair("veo_3_1_r2v_fast", "veo_3_1_r2v_fast_portrait")},
        supports_images=True,
        min_images=0,
        max_images=3,
    ),
    "veo_3_1_r2v_fast_ultra": _video_selector(
        "r2v",
        {
            (None, None): _aspect_pair("veo_3_1_r2v_fast_ultra", "veo_3_1_r2v_fast_portrait_ultra"),
            (None, "4k"): _aspect_pair("veo_3_1_r2v_fast_ultra_4k", "veo_3_1_r2v_fast_portrait_ultra_4k"),
            (None, "1080p"): _aspect_pair("veo_3_1_r2v_fast_ultra_1080p", "veo_3_1_r2v_fast_portrait_ultra_1080p"),
        },
        resolutions=["1080p", "4k"],
        supports_images=True,
        min_images=0,
        max_images=3,
    ),
    "veo_3_1_r2v_fast_ultra_relaxed": _video_selector(
        "r2v",
        {
            (None, None): _aspect_pair(
                "veo_3_1_r2v_fast_ultra_relaxed",
                "veo_3_1_r2v_fast_portrait_ultra_relaxed",
            )
        },
        supports_images=True,
        min_images=0,
        max_images=3,
    ),
    "gemini-omni-flash": _video_selector(
        "r2v",
        {
            (4, None): _aspect_pair("gemini-omni-flash-4s-landscape", "gemini-omni-flash-4s-portrait"),
            (6, None): _aspect_pair("gemini-omni-flash-6s-landscape", "gemini-omni-flash-6s-portrait"),
            (8, None): _aspect_pair("gemini-omni-flash-8s-landscape", "gemini-omni-flash-8s-portrait"),
            (10, None): _aspect_pair("gemini-omni-flash-10s-landscape", "gemini-omni-flash-10s-portrait"),
        },
        durations=[4, 6, 8, 10],
        supports_images=True,
        min_images=0,
        max_images=3,
        default_duration=OMNI_FLASH_DEFAULT_DURATION,
    ),
    "veo_3_1_extend": _video_selector(
        "extend",
        {(None, None): _aspect_pair("veo_3_1_extend", "veo_3_1_extend_portrait")},
        requires_video_id=True,
    ),
}


def _infer_video_alias_metadata(alias: str) -> Dict[str, Any]:
    if "r2v" in alias:
        video_type = "r2v"
        supports_images = True
        min_images = 0
        max_images = 3
    elif "interpolation" in alias:
        video_type = "i2v"
        supports_images = True
        min_images = 2
        max_images = 2
    elif "i2v" in alias:
        video_type = "i2v"
        supports_images = True
        min_images = 1
        max_images = 1 if "i2v_lite" in alias else 2
    elif "extend" in alias:
        video_type = "extend"
        supports_images = False
        min_images = None
        max_images = None
    else:
        video_type = "t2v"
        supports_images = False
        min_images = None
        max_images = None

    durations = []
    for seconds in (4, 6, 8, 10):
        if f"_{seconds}s" in alias or f"-{seconds}s" in alias:
            durations.append(seconds)

    resolutions = []
    for resolution in ("1080p", "4k"):
        if resolution in alias:
            resolutions.append(resolution)

    return {
        "type": "video",
        "video_type": video_type,
        "aspects": list(VIDEO_BASE_MODELS.get(alias, {}).keys()) or ["landscape", "portrait"],
        "durations": durations,
        "resolutions": resolutions,
        "supports_images": supports_images,
        "min_images": min_images,
        "max_images": max_images,
        "requires_video_id": "extend" in alias,
    }


def _select_video_variant(
    selector: Dict[str, Any],
    aspect_ratio: str,
    duration: Optional[int],
    resolution: Optional[str],
) -> Optional[str]:
    durations = selector.get("durations") or []
    resolutions = selector.get("resolutions") or []
    default_duration = selector.get("default_duration")
    selected_duration = duration if duration in durations else default_duration
    selected_resolution = resolution if resolution in resolutions else None
    variants = selector.get("variants") or {}

    for key in (
        (selected_duration, selected_resolution),
        (selected_duration, None),
        (None, selected_resolution),
        (None, None),
    ):
        aspect_map = variants.get(key)
        if aspect_map and aspect_ratio in aspect_map:
            return aspect_map[aspect_ratio]
    return None


def get_model_alias_metadata() -> Dict[str, Dict[str, Any]]:
    """返回所有简化模型别名及其可选参数能力，用于目录和测试页。"""
    aliases: Dict[str, Dict[str, Any]] = {}

    for alias, base in IMAGE_BASE_MODELS.items():
        aliases[alias] = {
            "id": alias,
            "type": "image",
            "is_alias": True,
            "aspects": MODEL_SUPPORTED_ASPECTS.get(base, []),
            "sizes": MODEL_SUPPORTED_SIZES.get(base, []),
            "supports_images": True,
            "min_images": 0,
            "max_images": 5,
            "default_model": f"{base}-{DEFAULT_ASPECT}",
        }

    for alias in VIDEO_BASE_MODELS:
        selector = VIDEO_ALIAS_SELECTORS.get(alias)
        meta = dict(selector) if selector else _infer_video_alias_metadata(alias)
        meta.pop("variants", None)
        meta.pop("default_duration", None)
        default_target = _select_video_variant(
            selector,
            "landscape",
            selector.get("default_duration") if selector else None,
            None,
        ) if selector else VIDEO_BASE_MODELS[alias].get("landscape")
        meta.update({"id": alias, "is_alias": True, "default_model": default_target})
        aliases[alias] = meta

    return aliases


def _extract_generation_params(request) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """从请求中提取 aspectRatio、imageSize 和 duration 参数。

    优先级：
    1. request.generationConfig.imageConfig (顶层 Gemini 参数)
    2. extra fields 中的 generationConfig (extra_body 透传)
    3. OpenAI 风格字段（size/quality）兼容：可在 generationConfig/imageConfig 或顶层 extra 中出现

    Returns:
        (aspect_ratio, image_size, duration) 归一化后的值
    """
    def _normalize_str(value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        text = value.strip()
        return text if text else None

    def _read_value(obj: Any, *keys: str) -> Any:
        if obj is None:
            return None
        if isinstance(obj, dict):
            for key in keys:
                if key in obj:
                    return obj.get(key)
            return None

        for key in keys:
            if hasattr(obj, key):
                value = getattr(obj, key, None)
                if value is not None:
                    return value

        extra = getattr(obj, "__pydantic_extra__", None) or {}
        for key in keys:
            if key in extra:
                return extra.get(key)
        return None

    def _normalize_aspect_ratio(value: Any) -> Optional[str]:
        raw = _normalize_str(value)
        if not raw:
            return None

        token = (
            raw.replace("：", ":")
            .replace("/", ":")
            .replace("x", ":")
            .replace("X", ":")
            .replace(" ", "")
            .strip()
        )

        mapped = ASPECT_RATIO_MAP.get(token)
        if mapped:
            return mapped
        mapped = ASPECT_RATIO_MAP.get(token.lower())
        if mapped:
            return mapped
        mapped = ASPECT_RATIO_MAP.get(token.upper())
        if mapped:
            return mapped
        return token

    def _normalize_image_size(value: Any) -> Optional[str]:
        raw = _normalize_str(value)
        if not raw:
            return None

        token = raw.replace(" ", "").strip()
        mapped = IMAGE_SIZE_MAP.get(token)
        if mapped is not None:
            return mapped or None
        mapped = IMAGE_SIZE_MAP.get(token.lower())
        if mapped is not None:
            return mapped or None
        mapped = IMAGE_SIZE_MAP.get(token.upper())
        if mapped is not None:
            return mapped or None
        return token.lower()

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

    def _aspect_from_openai_size(value: Any) -> Optional[str]:
        raw = _normalize_str(value)
        if not raw:
            return None

        match = OPENAI_IMAGE_SIZE_RE.match(raw)
        if not match:
            return None

        try:
            width = int(match.group("w"))
            height = int(match.group("h"))
        except Exception:
            return None

        if width <= 0 or height <= 0:
            return None

        ratio = width / height
        best = min(
            ASPECT_RATIO_FLOAT_MAP.items(),
            key=lambda item: abs(ratio - item[1]),
        )[0]
        return best

    def _image_size_from_openai_quality(value: Any) -> Optional[str]:
        raw = _normalize_str(value)
        if not raw:
            return None

        token = raw.strip().lower()
        if token in IMAGE_SIZE_MAP:
            return _normalize_image_size(token)

        mapped = OPENAI_QUALITY_MAP.get(token)
        if mapped:
            return mapped
        return None

    def _apply_image_config(image_config: Any, aspect_ratio: Optional[str], image_size: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        # 显式 aspectRatio/imageSize
        if not aspect_ratio:
            aspect_ratio = _normalize_aspect_ratio(
                _read_value(image_config, "aspectRatio", "aspect_ratio", "aspect")
            )
        if not image_size:
            image_size = _normalize_image_size(
                _read_value(image_config, "imageSize", "image_size", "resolution")
            )

        # OpenAI size/quality
        if not aspect_ratio:
            aspect_ratio = _aspect_from_openai_size(_read_value(image_config, "size"))
        if not image_size:
            image_size = _image_size_from_openai_quality(
                _read_value(image_config, "quality", "imageQuality", "image_quality")
            )

        return aspect_ratio, image_size

    aspect_ratio: Optional[str] = None
    image_size: Optional[str] = None
    duration: Optional[int] = None

    # 1) 优先从 request.generationConfig 解析
    gen_config = getattr(request, "generationConfig", None)
    if gen_config is not None:
        duration = _normalize_duration(
            _read_value(gen_config, "duration", "videoDuration", "video_duration", "durationSeconds", "duration_seconds")
        )
        image_config = _read_value(gen_config, "imageConfig", "image_config")
        if image_config is not None:
            aspect_ratio, image_size = _apply_image_config(
                image_config, aspect_ratio, image_size
            )

        # 有些上游会把字段放在 generationConfig 顶层
        if not aspect_ratio:
            aspect_ratio = _normalize_aspect_ratio(
                _read_value(gen_config, "aspectRatio", "aspect_ratio")
            )
        if not image_size:
            image_size = _normalize_image_size(
                _read_value(
                    gen_config,
                    "imageSize",
                    "image_size",
                    "resolution",
                    "videoResolution",
                    "video_resolution",
                )
            )

        if not aspect_ratio:
            aspect_ratio = _aspect_from_openai_size(_read_value(gen_config, "size"))
        if not image_size:
            image_size = _image_size_from_openai_quality(_read_value(gen_config, "quality"))

    # 2) 顶层没有时，再尝试从 extra fields (Pydantic extra="allow") 中透传的 generationConfig
    if (aspect_ratio is None or image_size is None or duration is None) and hasattr(request, "__pydantic_extra__"):
        extra = request.__pydantic_extra__ or {}
        gen_config_raw = extra.get("generationConfig")
        if not isinstance(gen_config_raw, dict):
            extra_body = extra.get("extra_body") or extra.get("extraBody")
            if isinstance(extra_body, dict):
                gen_config_raw = extra_body.get("generationConfig")

        if isinstance(gen_config_raw, dict):
            if duration is None:
                duration = _normalize_duration(
                    gen_config_raw.get("duration")
                    or gen_config_raw.get("videoDuration")
                    or gen_config_raw.get("video_duration")
                    or gen_config_raw.get("durationSeconds")
                    or gen_config_raw.get("duration_seconds")
                )
            image_config_raw = (
                gen_config_raw.get("imageConfig")
                or gen_config_raw.get("image_config")
                or {}
            )
            if image_config_raw:
                aspect_ratio, image_size = _apply_image_config(
                    image_config_raw, aspect_ratio, image_size
                )

            if aspect_ratio is None:
                aspect_ratio = _normalize_aspect_ratio(
                    gen_config_raw.get("aspectRatio") or gen_config_raw.get("aspect_ratio")
                )
            if image_size is None:
                image_size = _normalize_image_size(
                    gen_config_raw.get("imageSize")
                    or gen_config_raw.get("image_size")
                    or gen_config_raw.get("resolution")
                    or gen_config_raw.get("videoResolution")
                    or gen_config_raw.get("video_resolution")
                )

            if aspect_ratio is None:
                aspect_ratio = _aspect_from_openai_size(gen_config_raw.get("size"))
            if image_size is None:
                image_size = _image_size_from_openai_quality(gen_config_raw.get("quality"))

    # 3) OpenAI 风格 size/quality（顶层 extra）兼容
    if (aspect_ratio is None or image_size is None or duration is None) and hasattr(request, "__pydantic_extra__"):
        extra = request.__pydantic_extra__ or {}
        if aspect_ratio is None:
            aspect_ratio = _aspect_from_openai_size(extra.get("size"))
        if image_size is None:
            image_size = _image_size_from_openai_quality(extra.get("quality"))

        # 一些上游可能直接传 aspect_ratio/image_size
        if aspect_ratio is None:
            aspect_ratio = _normalize_aspect_ratio(extra.get("aspect_ratio") or extra.get("aspectRatio"))
        if image_size is None:
            image_size = _normalize_image_size(
                extra.get("image_size")
                or extra.get("imageSize")
                or extra.get("resolution")
                or extra.get("videoResolution")
                or extra.get("video_resolution")
            )

        if duration is None:
            duration = _normalize_duration(
                extra.get("duration")
                or extra.get("videoDuration")
                or extra.get("video_duration")
                or extra.get("durationSeconds")
                or extra.get("duration_seconds")
            )

    return aspect_ratio, image_size, duration


def resolve_model_name(
    model: str, request=None, model_config: Optional[Dict[str, Any]] = None
) -> str:
    """将简化模型名 + generationConfig 参数解析为内部 MODEL_CONFIG key。

    如果 model 已经是有效的 MODEL_CONFIG key，直接返回。
    如果 model 是简化名（基础模型名），则根据 generationConfig 中的
    aspectRatio / imageSize 拼接出完整的内部模型名。

    Args:
        model: 请求中的模型名
        request: ChatCompletionRequest 实例（用于提取 generationConfig）
        model_config: MODEL_CONFIG 字典（用于验证解析后的模型名）

    Returns:
        解析后的内部模型名
    """
    # ────── 图片模型解析 ──────
    if model in IMAGE_BASE_MODELS:
        base = IMAGE_BASE_MODELS[model]
        aspect_ratio, image_size, _duration = (
            _extract_generation_params(request) if request else (None, None, None)
        )

        # 默认 aspect ratio
        if not aspect_ratio:
            aspect_ratio = DEFAULT_ASPECT

        # 检查支持的 aspect ratio
        supported_aspects = MODEL_SUPPORTED_ASPECTS.get(base, [])
        if aspect_ratio not in supported_aspects and supported_aspects:
            debug_logger.log_warning(
                f"[MODEL_RESOLVER] 模型 {base} 不支持 aspectRatio={aspect_ratio}，"
                f"降级到 {DEFAULT_ASPECT}"
            )
            aspect_ratio = DEFAULT_ASPECT

        # 拼接模型名
        resolved = f"{base}-{aspect_ratio}"

        # 检查支持的 imageSize
        if image_size and image_size != "1k":
            supported_sizes = MODEL_SUPPORTED_SIZES.get(base, [])
            if image_size in supported_sizes:
                resolved = f"{resolved}-{image_size}"
            else:
                debug_logger.log_warning(
                    f"[MODEL_RESOLVER] 模型 {base} 不支持 imageSize={image_size}，忽略"
                )

        # 最终验证
        if model_config and resolved not in model_config:
            debug_logger.log_warning(
                f"[MODEL_RESOLVER] 解析后的模型名 {resolved} 不在 MODEL_CONFIG 中，"
                f"回退到原始模型名 {model}"
            )
            return model

        debug_logger.log_info(
            f"[MODEL_RESOLVER] 模型名转换: {model} → {resolved} "
            f"(aspectRatio={aspect_ratio}, imageSize={image_size or 'default'})"
        )
        return resolved

    # ────── 视频模型解析 ──────
    if model in VIDEO_BASE_MODELS:
        aspect_ratio, image_size, duration = (
            _extract_generation_params(request) if request else (None, None, None)
        )

        # 视频默认横屏
        if not aspect_ratio or aspect_ratio not in ("landscape", "portrait"):
            aspect_ratio = "landscape"

        selector = VIDEO_ALIAS_SELECTORS.get(model)
        if selector:
            resolved = _select_video_variant(selector, aspect_ratio, duration, image_size)
            if model_config and resolved in model_config:
                debug_logger.log_info(
                    f"[MODEL_RESOLVER] 视频模型名转换: {model} → {resolved} "
                    f"(aspectRatio={aspect_ratio}, duration={duration or 'default'}, "
                    f"resolution={image_size or 'default'})"
                )
                return resolved

        if image_size in ("4k", "1080p") and f"{model}_{image_size}" in VIDEO_BASE_MODELS:
            model = f"{model}_{image_size}"

        orientation_map = VIDEO_BASE_MODELS[model]
        resolved = orientation_map.get(aspect_ratio)

        if resolved and model_config and resolved in model_config:
            debug_logger.log_info(
                f"[MODEL_RESOLVER] 视频模型名转换: {model} → {resolved} "
                f"(aspectRatio={aspect_ratio})"
            )
            return resolved

        debug_logger.log_warning(
            f"[MODEL_RESOLVER] 视频模型 {model} 解析失败 (aspect={aspect_ratio})，"
            f"使用原始模型名"
        )
        return model

    # 如果已经是有效的 MODEL_CONFIG key，直接返回
    if model_config and model in model_config:
        return model

    # 未知模型名，原样返回（由下游 MODEL_CONFIG 校验报错）
    return model


def get_base_model_aliases() -> Dict[str, str]:
    """返回所有简化模型名（别名）及其描述，用于 /v1/models 接口展示。"""
    aliases = {}

    for alias, meta in get_model_alias_metadata().items():
        if meta.get("type") == "image":
            desc_parts = [f"aspects: {', '.join(meta.get('aspects') or [])}"]
            sizes = meta.get("sizes") or []
            if sizes:
                desc_parts.append(f"sizes: {', '.join(sizes)}")
            aliases[alias] = f"Image generation (alias) - {'; '.join(desc_parts)}"
            continue

        desc_parts = ["supports landscape/portrait via generationConfig"]
        durations = meta.get("durations") or []
        resolutions = meta.get("resolutions") or []
        if durations:
            desc_parts.append(f"durations: {', '.join(str(item) + 's' for item in durations)}")
        if resolutions:
            desc_parts.append(f"resolutions: {', '.join(resolutions)}")
        aliases[alias] = f"Video generation (alias) - {'; '.join(desc_parts)}"

    return aliases
