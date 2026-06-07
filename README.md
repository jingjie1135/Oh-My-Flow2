# Flow2API

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.119.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

**一个功能完整的 OpenAI 兼容 API 服务，为 Flow 提供统一的接口**

</div>

## ✨ 核心特性

- 🎨 **文生图** / **图生图**
- 🎬 **文生视频** / **图生视频**
- 🎞️ **首尾帧视频**
- 🔄 **AT/ST自动刷新** - AT 过期自动刷新，ST 过期时自动通过浏览器更新（personal 模式）
- 📊 **余额显示** - 实时查询和显示 VideoFX Credits
- 🚀 **负载均衡** - 多 Token 轮询和并发控制
- 🌐 **代理支持** - 支持 HTTP/SOCKS5 代理
- 📱 **Web 管理界面** - 直观的 Token 和配置管理
- 🎨 **图片生成连续对话**
- 🧩 **Gemini 官方请求体兼容** - 支持 `generateContent` / `streamGenerateContent`、`systemInstruction`、`contents.parts.text/inlineData/fileData`
- ✅ **Gemini 官方格式已实测出图** - 已使用真实 Token 验证 `/models/{model}:generateContent` 可正常返回官方 `candidates[].content.parts[].inlineData`

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose（推荐）
- 或 Python 3.8+

- 由于Flow增加了额外的验证码，你可以自行选择使用浏览器打码或第三发打码：
注册[YesCaptcha](https://yescaptcha.com/i/13Xd8K)并获取api key，将其填入系统配置页面```YesCaptcha API密钥```区域
- YesCaptcha 支持在管理页切换 `type`：`RecaptchaV3TaskProxyless`、`RecaptchaV3TaskProxylessM1`、`RecaptchaV3TaskProxylessM1S7`、`RecaptchaV3TaskProxylessM1S9`；S7/S9 会强制提交 `minScore` 0.7/0.9。
- 默认 `docker-compose.yml` 建议搭配第三方打码（yescaptcha/capmonster/ezcaptcha/capsolver），仍可作为通用部署入口。
- 如果你想按验证码模式隔离部署，仓库保留 4 套独立 Compose 配置。
- `browser` / `personal` 模式在 Docker 中需要有头浏览器环境，请使用对应的模式专用 Compose 文件或 `docker-compose.headed.yml`。

- 自动更新st浏览器拓展：[Flow2API-Token-Updater](https://github.com/TheSmallHanCat/Flow2API-Token-Updater)

### 方式一：Docker 部署（推荐）

#### 相关文档

- [验证码模式 Docker 对照表](./docs/%E9%AA%8C%E8%AF%81%E7%A0%81%E6%A8%A1%E5%BC%8F%20Docker%20%E5%AF%B9%E7%85%A7%E8%A1%A8.md)
- [Docker 部署指南](./docs/Docker%E9%83%A8%E7%BD%B2%E6%8C%87%E5%8D%97.md)
- [Flow2API 架构分析](./docs/Flow2API%20%E6%9E%B6%E6%9E%84%E5%88%86%E6%9E%90.md)

#### 按验证码模式部署（推荐）

| 打码模式 | Compose 文件 | 配置文件 | 主机端口 | 说明 |
|---------|--------------|----------|----------|------|
| yescaptcha | `docker-compose.yescaptcha.yml` | `config/setting.yescaptcha.toml` | `38100` | 第三方打码平台，适合最简单部署 |
| browser | `docker-compose.browser.yml` | `config/setting.browser.toml` | `38101` | Playwright 按请求启动浏览器，要求 Docker 有头环境 |
| personal | `docker-compose.personal.yml` | `config/setting.personal.toml` | `38102` | 常驻标签页模式，支持 ST 自动续期，要求 Docker 有头环境 |
| remote_browser | `docker-compose.remote-browser.yml` | `config/setting.remote_browser.toml` | `38103` | 依赖外部远程 token 池服务 |

> 说明：每种模式都挂载独立的 `data/<mode>` 和 `tmp/<mode>`，避免 SQLite 把一种模式的配置持久化后污染另一种模式。

#### yescaptcha 模式

```bash
# 首次启动前，先编辑 config/setting.yescaptcha.toml，填入 yescaptcha_api_key
docker compose -f docker-compose.yescaptcha.yml up -d --build

# 查看日志
docker compose -f docker-compose.yescaptcha.yml logs -f
```

访问地址：`http://localhost:38100`

#### browser 模式

```bash
# 启动 browser 模式（Docker 有头环境）
docker compose -f docker-compose.browser.yml up -d --build

# 查看日志
docker compose -f docker-compose.browser.yml logs -f
```

访问地址：`http://localhost:38101`

#### personal 模式

> 适用于你希望在容器里使用常驻标签页维持更稳定的验证码 / ST 自动续期能力。  
> 该模式默认启动 `Xvfb + Fluxbox` 实现容器内部可视化，并设置 `ALLOW_DOCKER_HEADED_CAPTCHA=true`。  
> 仅开放应用端口，不提供任何远程桌面连接端口。
> `personal` 内置浏览器现在默认按有头模式启动；如需临时切回无头，可额外设置环境变量 `PERSONAL_BROWSER_HEADLESS=true`。

```bash
# 启动 personal 模式（首次建议带 --build）
docker compose -f docker-compose.personal.yml up -d --build

# 查看日志
docker compose -f docker-compose.personal.yml logs -f
```

访问地址：`http://localhost:38102`

#### remote_browser 模式

> 该模式只负责调用外部远程浏览器 / token 池服务。启动前请先编辑 `config/setting.remote_browser.toml`，至少填写：
>
> - `remote_browser_base_url`
> - `remote_browser_api_key`

```bash
docker compose -f docker-compose.remote-browser.yml up -d --build

# 查看日志
docker compose -f docker-compose.remote-browser.yml logs -f
```

访问地址：`http://localhost:38103`

#### 通用模式（兼容旧文档）

```bash
# 保留原有默认 compose 用法
docker compose up -d

# 查看日志
docker compose logs -f
```

#### WARP 模式（使用代理）

```bash
docker compose -f docker-compose.proxy.yml up -d

# 查看日志
docker compose -f docker-compose.proxy.yml logs -f
```

### 方式二：本地部署

```bash
# 克隆项目
git clone https://github.com/TheSmallHanCat/flow2api.git
cd flow2api

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 首次访问

服务启动后,访问管理后台: **http://localhost:8000**,首次登录后请立即修改密码!

- **用户名**: `admin`
- **密码**: `admin`

## 📈 监控接口

- `GET /health`：公开健康检查，返回服务是否存活、活跃 Token 数、即将过期 Token 数、已过期 Token 数、429 禁用数等摘要
- `GET /metrics`：Prometheus 指标接口
- `GET /api/tokens`：管理接口，返回 `at_expires`、`at_expired`、`at_expiring_within_1h`、`ban_reason`、`consecutive_error_count` 等 Token 状态

Prometheus 可直接抓 `/metrics`。如果部署到 Kubernetes，建议只在集群内抓取，并在 Ingress/Gateway 层单独限制 `/metrics` 的外部访问。

### 模型测试页面

访问 **http://localhost:8000/test** 可打开内置的模型测试页面，支持：

- 按分类浏览所有可用模型（图片生成、文/图生视频、多图视频、视频放大等）
- 显示参数自动选择 Alias，并可在页面选择宽高比、时长、图片清晰度或视频输出分辨率
- 输入提示词一键测试，流式显示生成进度
- 图生图 / 图生视频场景支持上传图片
- 生成完成后直接预览图片或视频

## 📋 支持的模型

### 图片生成

| 模型名称 | 说明| 尺寸 |
|---------|--------|--------|
| `gemini-3.0-pro-image-landscape` | 图/文生图 | 横屏 |
| `gemini-3.0-pro-image-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.0-pro-image-square` | 图/文生图 | 方图 |
| `gemini-3.0-pro-image-four-three` | 图/文生图 | 横屏 4:3 |
| `gemini-3.0-pro-image-three-four` | 图/文生图 | 竖屏 3:4 |
| `gemini-3.0-pro-image-landscape-2k` | 图/文生图(2K) | 横屏 |
| `gemini-3.0-pro-image-portrait-2k` | 图/文生图(2K) | 竖屏 |
| `gemini-3.0-pro-image-square-2k` | 图/文生图(2K) | 方图 |
| `gemini-3.0-pro-image-four-three-2k` | 图/文生图(2K) | 横屏 4:3 |
| `gemini-3.0-pro-image-three-four-2k` | 图/文生图(2K) | 竖屏 3:4 |
| `gemini-3.0-pro-image-landscape-4k` | 图/文生图(4K) | 横屏 |
| `gemini-3.0-pro-image-portrait-4k` | 图/文生图(4K) | 竖屏 |
| `gemini-3.0-pro-image-square-4k` | 图/文生图(4K) | 方图 |
| `gemini-3.0-pro-image-four-three-4k` | 图/文生图(4K) | 横屏 4:3 |
| `gemini-3.0-pro-image-three-four-4k` | 图/文生图(4K) | 竖屏 3:4 |
| `imagen-4.0-generate-preview-landscape` | 图/文生图 | 横屏 |
| `imagen-4.0-generate-preview-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.1-flash-image-landscape` | 图/文生图 | 横屏 |
| `gemini-3.1-flash-image-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.1-flash-image-square` | 图/文生图 | 方图 |
| `gemini-3.1-flash-image-four-three` | 图/文生图 | 横屏 4:3 |
| `gemini-3.1-flash-image-three-four` | 图/文生图 | 竖屏 3:4 |
| `gemini-3.1-flash-image-landscape-2k` | 图/文生图(2K) | 横屏 |
| `gemini-3.1-flash-image-portrait-2k` | 图/文生图(2K) | 竖屏 |
| `gemini-3.1-flash-image-square-2k` | 图/文生图(2K) | 方图 |
| `gemini-3.1-flash-image-four-three-2k` | 图/文生图(2K) | 横屏 4:3 |
| `gemini-3.1-flash-image-three-four-2k` | 图/文生图(2K) | 竖屏 3:4 |
| `gemini-3.1-flash-image-landscape-4k` | 图/文生图(4K) | 横屏 |
| `gemini-3.1-flash-image-portrait-4k` | 图/文生图(4K) | 竖屏 |
| `gemini-3.1-flash-image-square-4k` | 图/文生图(4K) | 方图 |
| `gemini-3.1-flash-image-four-three-4k` | 图/文生图(4K) | 横屏 4:3 |
| `gemini-3.1-flash-image-three-four-4k` | 图/文生图(4K) | 竖屏 3:4 |

### 视频生成

#### 文生视频 (T2V - Text to Video)
⚠️ **不支持上传图片**

| 模型名称 | 说明| 尺寸 |
|---------|---------|--------|
| `veo_3_1_t2v_fast_portrait` | 文生视频 | 竖屏 |
| `veo_3_1_t2v_fast_landscape` | 文生视频 | 横屏 |
| `veo_3_1_t2v_fast_portrait_ultra` | 文生视频 | 竖屏 |
| `veo_3_1_t2v_fast_ultra` | 文生视频 | 横屏 |
| `veo_3_1_t2v_fast_portrait_ultra_relaxed` | 文生视频 | 竖屏 |
| `veo_3_1_t2v_fast_ultra_relaxed` | 文生视频 | 横屏 |
| `veo_3_1_t2v_portrait` | 文生视频 | 竖屏 |
| `veo_3_1_t2v_landscape` | 文生视频 | 横屏 |
| `veo_3_1_t2v_landscape_4s` | 文生视频 4秒 | 横屏 |
| `veo_3_1_t2v_portrait_4s` | 文生视频 4秒 | 竖屏 |
| `veo_3_1_t2v_landscape_6s` | 文生视频 6秒 | 横屏 |
| `veo_3_1_t2v_portrait_6s` | 文生视频 6秒 | 竖屏 |
| `veo_3_1_t2v_fast_landscape_4s` | 文生视频 Fast 4秒 | 横屏 |
| `veo_3_1_t2v_fast_portrait_4s` | 文生视频 Fast 4秒 | 竖屏 |
| `veo_3_1_t2v_fast_landscape_6s` | 文生视频 Fast 6秒 | 横屏 |
| `veo_3_1_t2v_fast_portrait_6s` | 文生视频 Fast 6秒 | 竖屏 |
| `veo_3_1_t2v_lite_portrait` | 文生视频 Lite | 竖屏 |
| `veo_3_1_t2v_lite_landscape` | 文生视频 Lite | 横屏 |
| `veo_3_1_t2v_lite_4s_portrait` | 文生视频 Lite 4秒 | 竖屏 |
| `veo_3_1_t2v_lite_4s_landscape` | 文生视频 Lite 4秒 | 横屏 |
| `veo_3_1_t2v_lite_6s_portrait` | 文生视频 Lite 6秒 | 竖屏 |
| `veo_3_1_t2v_lite_6s_landscape` | 文生视频 Lite 6秒 | 横屏 |

#### 首尾帧模型 (I2V - Image to Video)
📸 **支持1-2张图片：1张作为首帧，2张作为首尾帧**

> 💡 **自动适配**：系统会根据图片数量自动选择对应的 model_key
> - **单帧模式**（1张图）：使用首帧生成视频
> - **双帧模式**（2张图）：使用首帧+尾帧生成过渡视频
> - `veo_3_1_i2v_lite_*` 仅支持 **1 张** 首帧图片
> - `veo_3_1_interpolation_lite_*` 仅支持 **2 张** 首尾帧图片

| 模型名称 | 说明| 尺寸 |
|---------|---------|--------|
| `veo_3_1_i2v_s_fast_portrait_fl` | 图生视频 | 竖屏 |
| `veo_3_1_i2v_s_fast_fl` | 图生视频 | 横屏 |
| `veo_3_1_i2v_s_fast_portrait_ultra_fl` | 图生视频 | 竖屏 |
| `veo_3_1_i2v_s_fast_ultra_fl` | 图生视频 | 横屏 |
| `veo_3_1_i2v_s_fast_portrait_ultra_relaxed` | 图生视频 | 竖屏 |
| `veo_3_1_i2v_s_fast_ultra_relaxed` | 图生视频 | 横屏 |
| `veo_3_1_i2v_s_portrait` | 图生视频 | 竖屏 |
| `veo_3_1_i2v_s_landscape` | 图生视频 | 横屏 |
| `veo_3_1_i2v_s_landscape_4s` | 图生视频 4秒 | 横屏 |
| `veo_3_1_i2v_s_portrait_4s` | 图生视频 4秒 | 竖屏 |
| `veo_3_1_i2v_s_landscape_6s` | 图生视频 6秒 | 横屏 |
| `veo_3_1_i2v_s_portrait_6s` | 图生视频 6秒 | 竖屏 |
| `veo_3_1_i2v_s_fast_landscape_4s_fl` | 图生视频 Fast 4秒 | 横屏 |
| `veo_3_1_i2v_s_fast_portrait_4s_fl` | 图生视频 Fast 4秒 | 竖屏 |
| `veo_3_1_i2v_s_fast_landscape_6s_fl` | 图生视频 Fast 6秒 | 横屏 |
| `veo_3_1_i2v_s_fast_portrait_6s_fl` | 图生视频 Fast 6秒 | 竖屏 |
| `veo_3_1_i2v_lite_portrait` | 图生视频 Lite（仅首帧） | 竖屏 |
| `veo_3_1_i2v_lite_landscape` | 图生视频 Lite（仅首帧） | 横屏 |
| `veo_3_1_i2v_lite_4s_portrait` | 图生视频 Lite 4秒（仅首帧） | 竖屏 |
| `veo_3_1_i2v_lite_4s_landscape` | 图生视频 Lite 4秒（仅首帧） | 横屏 |
| `veo_3_1_i2v_lite_6s_portrait` | 图生视频 Lite 6秒（仅首帧） | 竖屏 |
| `veo_3_1_i2v_lite_6s_landscape` | 图生视频 Lite 6秒（仅首帧） | 横屏 |
| `veo_3_1_interpolation_lite_portrait` | 图生视频 Lite（首尾帧过渡） | 竖屏 |
| `veo_3_1_interpolation_lite_landscape` | 图生视频 Lite（首尾帧过渡） | 横屏 |
| `veo_3_1_interpolation_lite_4s_portrait` | 图生视频 Lite 4秒（首尾帧过渡） | 竖屏 |
| `veo_3_1_interpolation_lite_4s_landscape` | 图生视频 Lite 4秒（首尾帧过渡） | 横屏 |
| `veo_3_1_interpolation_lite_6s_portrait` | 图生视频 Lite 6秒（首尾帧过渡） | 竖屏 |
| `veo_3_1_interpolation_lite_6s_landscape` | 图生视频 Lite 6秒（首尾帧过渡） | 横屏 |

#### 多图生成 (R2V - Reference Images to Video)
🖼️ **支持多张图片**

> **2026-03-06 更新**
>
> - 已同步上游新版 `R2V` 视频请求体
> - `textInput` 已切换为 `structuredPrompt.parts`
> - 顶层新增 `mediaGenerationContext.batchId`
> - 顶层新增 `useV2ModelConfig: true`
> - 横屏 / 竖屏 `R2V` 模型共用同一套新版请求体
> - 横屏 `R2V` 的上游 `videoModelKey` 已切换为 `*_landscape` 形式
> - 根据当前上游协议，`referenceImages` 当前最多传 **3 张**
> - `gemini-omni-flash` 第一阶段按 R2V 接入：参考图可选，支持 **0-3 张参考图**，支持 `duration` 为 `4` / `6` / `8` / `10` 秒，支持 `16:9` / `9:16`

| 模型名称 | 说明| 尺寸 |
|---------|---------|--------|
| `veo_3_1_r2v_fast_portrait` | 图生视频 | 竖屏 |
| `veo_3_1_r2v_fast_landscape` | 图生视频 | 横屏 |
| `veo_3_1_r2v_fast_portrait_ultra` | 图生视频 | 竖屏 |
| `veo_3_1_r2v_fast_landscape_ultra` | 图生视频 | 横屏 |
| `veo_3_1_r2v_fast_portrait_ultra_relaxed` | 图生视频 | 竖屏 |
| `veo_3_1_r2v_fast_landscape_ultra_relaxed` | 图生视频 | 横屏 |
| `gemini-omni-flash` | Gemini Omni Flash R2V（按参数自动解析） | 横屏/竖屏 |
| `gemini-omni-flash-4s-landscape` | Gemini Omni Flash R2V 4秒 | 横屏 |
| `gemini-omni-flash-4s-portrait` | Gemini Omni Flash R2V 4秒 | 竖屏 |
| `gemini-omni-flash-6s-landscape` | Gemini Omni Flash R2V 6秒 | 横屏 |
| `gemini-omni-flash-6s-portrait` | Gemini Omni Flash R2V 6秒 | 竖屏 |
| `gemini-omni-flash-8s-landscape` | Gemini Omni Flash R2V 8秒 | 横屏 |
| `gemini-omni-flash-8s-portrait` | Gemini Omni Flash R2V 8秒 | 竖屏 |
| `gemini-omni-flash-10s-landscape` | Gemini Omni Flash R2V 10秒 | 横屏 |
| `gemini-omni-flash-10s-portrait` | Gemini Omni Flash R2V 10秒 | 竖屏 |

#### 视频放大模型 (Upsample)

这些模型不是直接调用上游 upsampler key，而是先用对应的 Veo 3.1 普通模型生成视频，再提交 1080P/4K 放大请求。

| 模型名称 | 说明 | 输出 |
|---------|---------|--------|
| `veo_3_1_t2v_landscape_4k` | 文生视频放大 | 4K |
| `veo_3_1_t2v_portrait_4k` | 文生视频放大 | 4K |
| `veo_3_1_t2v_landscape_1080p` | 文生视频放大 | 1080P |
| `veo_3_1_t2v_portrait_1080p` | 文生视频放大 | 1080P |
| `veo_3_1_t2v_landscape_4s_4k` | 文生视频 4秒放大 | 4K |
| `veo_3_1_t2v_portrait_4s_4k` | 文生视频 4秒放大 | 4K |
| `veo_3_1_t2v_landscape_4s_1080p` | 文生视频 4秒放大 | 1080P |
| `veo_3_1_t2v_portrait_4s_1080p` | 文生视频 4秒放大 | 1080P |
| `veo_3_1_t2v_landscape_6s_4k` | 文生视频 6秒放大 | 4K |
| `veo_3_1_t2v_portrait_6s_4k` | 文生视频 6秒放大 | 4K |
| `veo_3_1_t2v_landscape_6s_1080p` | 文生视频 6秒放大 | 1080P |
| `veo_3_1_t2v_portrait_6s_1080p` | 文生视频 6秒放大 | 1080P |
| `veo_3_1_t2v_fast_portrait_4k` | 文生视频放大 | 4K |
| `veo_3_1_t2v_fast_4k` | 文生视频放大 | 4K |
| `veo_3_1_t2v_fast_portrait_ultra_4k` | 文生视频放大 | 4K |
| `veo_3_1_t2v_fast_ultra_4k` | 文生视频放大 | 4K |
| `veo_3_1_t2v_fast_portrait_1080p` | 文生视频放大 | 1080P |
| `veo_3_1_t2v_fast_1080p` | 文生视频放大 | 1080P |
| `veo_3_1_t2v_fast_portrait_ultra_1080p` | 文生视频放大 | 1080P |
| `veo_3_1_t2v_fast_ultra_1080p` | 文生视频放大 | 1080P |
| `veo_3_1_i2v_s_fast_portrait_ultra_fl_4k` | 图生视频放大 | 4K |
| `veo_3_1_i2v_s_fast_ultra_fl_4k` | 图生视频放大 | 4K |
| `veo_3_1_i2v_s_fast_portrait_ultra_fl_1080p` | 图生视频放大 | 1080P |
| `veo_3_1_i2v_s_fast_ultra_fl_1080p` | 图生视频放大 | 1080P |
| `veo_3_1_i2v_s_landscape_4k` | 图生视频放大 | 4K |
| `veo_3_1_i2v_s_portrait_4k` | 图生视频放大 | 4K |
| `veo_3_1_i2v_s_landscape_1080p` | 图生视频放大 | 1080P |
| `veo_3_1_i2v_s_portrait_1080p` | 图生视频放大 | 1080P |
| `veo_3_1_i2v_s_landscape_4s_4k` | 图生视频 4秒放大 | 4K |
| `veo_3_1_i2v_s_portrait_4s_4k` | 图生视频 4秒放大 | 4K |
| `veo_3_1_i2v_s_landscape_4s_1080p` | 图生视频 4秒放大 | 1080P |
| `veo_3_1_i2v_s_portrait_4s_1080p` | 图生视频 4秒放大 | 1080P |
| `veo_3_1_i2v_s_landscape_6s_4k` | 图生视频 6秒放大 | 4K |
| `veo_3_1_i2v_s_portrait_6s_4k` | 图生视频 6秒放大 | 4K |
| `veo_3_1_i2v_s_landscape_6s_1080p` | 图生视频 6秒放大 | 1080P |
| `veo_3_1_i2v_s_portrait_6s_1080p` | 图生视频 6秒放大 | 1080P |
| `veo_3_1_r2v_fast_portrait_ultra_4k` | 多图视频放大 | 4K |
| `veo_3_1_r2v_fast_landscape_ultra_4k` | 多图视频放大 | 4K |
| `veo_3_1_r2v_fast_portrait_ultra_1080p` | 多图视频放大 | 1080P |
| `veo_3_1_r2v_fast_landscape_ultra_1080p` | 多图视频放大 | 1080P |

## 📡 API 使用示例（需要使用流式）

> 除了下方 `OpenAI-compatible` 示例，服务也支持 Gemini 官方格式：
> - `POST /v1beta/models/{model}:generateContent`
> - `POST /models/{model}:generateContent`
> - `POST /v1beta/models/{model}:streamGenerateContent`
> - `POST /models/{model}:streamGenerateContent`
>
> Gemini 官方格式支持以下认证方式：
> - `Authorization: Bearer <api_key>`
> - `x-goog-api-key: <api_key>`
> - `?key=<api_key>`
>
> Gemini 官方图片请求体已兼容：
> - `systemInstruction`
> - `contents[].parts[].text`
> - `contents[].parts[].inlineData`
> - `contents[].parts[].fileData.fileUri`
> - `generationConfig.responseModalities`
> - `generationConfig.imageConfig.aspectRatio`
> - `generationConfig.imageConfig.imageSize`
> - `generationConfig.duration` / `generationConfig.videoDuration`（视频别名解析）
> - `generationConfig.resolution` / `generationConfig.videoResolution`（视频放大别名解析）
>
> 模型目录：
> - `GET /v1/models` 返回具体可调用模型，并带有 `type`、`video_type`、图片数量限制等元数据。
> - `GET /v1/models/aliases` 返回可按参数自动选择具体变体的 Alias，并带有支持的 `aspects`、`durations`、`sizes`、`resolutions` 等元数据。

### Gemini 官方 generateContent（文生图）

> 已使用真实 Token 实测通过。
> 如需流式返回，可将路径替换为 `:streamGenerateContent?alt=sse`。

```bash
curl -X POST "http://localhost:8000/models/gemini-3.1-flash-image:generateContent" \
  -H "x-goog-api-key: han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "systemInstruction": {
      "parts": [
        {
          "text": "Return an image only."
        }
      ]
    },
    "contents": [
      {
        "role": "user",
        "parts": [
          {
            "text": "一颗放在木桌上的红苹果，棚拍光线，极简背景"
          }
        ]
      }
    ],
    "generationConfig": {
      "responseModalities": ["IMAGE"],
      "imageConfig": {
        "aspectRatio": "1:1",
        "imageSize": "1K"
      }
    }
  }'
```

### 文生图

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.1-flash-image-landscape",
    "messages": [
      {
        "role": "user",
        "content": "一只可爱的猫咪在花园里玩耍"
      }
    ],
    "stream": true
  }'
```

### 图生图

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.1-flash-image-landscape",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "将这张图片变成水彩画风格"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<base64_encoded_image>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

### 文生视频

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo_3_1_t2v_fast_landscape",
    "messages": [
      {
        "role": "user",
        "content": "一只小猫在草地上追逐蝴蝶"
      }
    ],
    "stream": true
  }'
```

### Gemini 官方 generateContent（Gemini Omni Flash R2V）

> 第一阶段支持纯文本或文本 + 图片参考的 R2V 调用；音频/视频输入、对话式视频编辑、首尾帧等能力暂未在本项目中接入。
> `duration` 支持 `4` / `6` / `8` / `10`，非法值会回退到默认 `4` 秒。

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
            "text": "参考这张角色图，生成一个镜头缓慢推进的 6 秒横屏视频"
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
      "duration": 6,
      "imageConfig": {
        "aspectRatio": "16:9"
      }
    }
  }'
```

### 首尾帧生成视频

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo_3_1_i2v_s_fast_fl_landscape",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "从第一张图过渡到第二张图"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<首帧base64>"
            }
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,<尾帧base64>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

### 多图生成视频

> `R2V` 会由服务端自动组装新版视频请求体，调用方仍然使用 OpenAI 兼容输入即可。
> 服务端会将横屏 `R2V` 自动映射到最新的 `*_landscape` 上游模型键。
> 当前最多传 **3 张参考图**。
> `gemini-omni-flash` 可作为 OpenAI 兼容别名使用，服务端会根据 `generationConfig.duration` 和 `generationConfig.imageConfig.aspectRatio` 解析到具体 `gemini-omni-flash-{duration}s-{orientation}` 变体。

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "veo_3_1_r2v_fast_portrait",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "以三张参考图的人物和场景为基础，生成一段镜头平滑推进的竖屏视频"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64/<参考图1base64>"
            }
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64/<参考图2base64>"
            }
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64/<参考图3base64>"
            }
          }
        ]
      }
    ],
    "stream": true
  }'
```

#### Gemini Omni Flash（OpenAI 兼容 R2V）

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer han1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-omni-flash",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "保留参考图中的角色造型，生成一段 9:16 的 8 秒动态视频"
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
    "generationConfig": {
      "duration": 8,
      "imageConfig": {
        "aspectRatio": "9:16"
      }
    },
    "stream": true
  }'
```

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [PearNoDec](https://github.com/PearNoDec) 提供的YesCaptcha打码方案
- [raomaiping](https://github.com/raomaiping) 提供的无头打码方案
感谢所有贡献者和使用者的支持！

---

## 📞 联系方式

- 提交 Issue：[GitHub Issues](https://github.com/TheSmallHanCat/flow2api/issues)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**

## 最近更新

- `9f1d712` 同步 personal 打码逻辑，包含清理、浏览器参数和打码方式配置。
- `da2ad06` 合并 PR #133。
- `abd0c00` 修复 PR #133 合并后的集成问题。
- `55431c9` 将 origin/main 同步到 PR #133。
- `4b7a0ad` 新增 Prometheus 服务指标和 Token 健康监控。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TheSmallHanCat/flow2api&type=date&legend=top-left)](https://www.star-history.com/#TheSmallHanCat/flow2api&type=date&legend=top-left)
