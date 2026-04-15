# Flow2API Docker 部署指南

Flow2API 采用 **Docker-First（Docker 优先）** 的架构模式。由于项目内置了高级的反爬（reCAPTCHA）打码机制和多样的网络代理需求，因此项目提供了多个定制化的 Dockerfile 和 Docker Compose 编排文件，以适应不同的服务器环境和部署需求。

本指南将详细解析这些文件的区别，并带您快速选择适合的部署模式。

---

## 🚀 快速选择指引

| 部署场景 | 推荐使用的命令 | 适用情况 |
| :--- | :--- | :--- |
| **标准线上部署** (最推荐) | `docker compose up -d` | 拥有优质海外服务器 IP，不需要强力打码环境的普通部署。基于极简的无头环境。 |
| **有头浏览器打码部署** | `docker compose -f docker-compose.headed.yml up -d --build` | 出现频繁的 403 / reCAPTCHA 错误，需要启动带真实屏幕的完整 Chromium 实例辅助进行复杂的验证码计算验证。 |
| **本地开发构建部署** | `docker compose -f docker-compose.local.yml up -d --build` | 修改了项目的 Python 源码，不希望使用官方远端镜像，想在本机当场构建并运行测试。 |
| **绑定 WARP 代理部署** | `docker compose -f docker-compose.proxy.yml up -d` | 宿主机本机 IP 存在严重的风控或被墙，需要利用 Cloudflare WARP 将所有出口流量进行二次代理，以绕过 Google IP 限制。 |

---

## 🐳 深入解析：Dockerfile 核心构建文件

项目中包含两个基础构建文件，主要区分在是否集成图形界面缓冲层。

### 1. `Dockerfile` (基础无头版)
这是默认构建体系。
* **特性**：轻量化构建，仅包含基本的系统依赖和 Python 环境，预装了供 Playwright 工作的基础包。
* **适用**：API 代理功能、API 打码模式、Remote Browser 模式以及基础的无头浏览器操作。不包含需要渲染真实图像桌面的组件。

### 2. `Dockerfile.headed` (图形界面强化版)
这是专为 `browser` 与部分严苛验证环境打造的版本。
* **特性**：开启了 `ALLOW_DOCKER_HEADED_CAPTCHA=true` 环境变量。其内部包含了启动脚本 `entrypoint.headed.sh`，在容器启动时会拉起 `Xvfb` (X virtual framebuffer) 提供一张虚拟网卡和虚拟显示器。
* **适用**：需要浏览器能够进行真实的页面渲染（有头模式），避免 Google reCAPTCHA v3 企业版检测出"无头特征"而拦截。

---

## ⚓ 深入解析：Docker Compose 编排文件

### 1. `docker-compose.yml` (官方直连)
最基础的部署方式。它直接拉取 GitHub Container Registry 上的打包镜像：
```yaml
image: ghcr.io/thesmallhancat/flow2api:latest
```
* **优势**：启动最快，不消耗本地编译资源。

### 2. `docker-compose.local.yml` (本地自行构建)
与基础版相比，将 `image` 获取方式修改为从同级目录下的 `Dockerfile` 构建：
```yaml
build:
  context: .
  dockerfile: Dockerfile
```
* **优势**：随时同步最新代码修改。

### 3. `docker-compose.headed.yml` (本地有头强化构建)
它是本地构建的变体强化版。除了指向 `Dockerfile.headed` 外，它还在内存和环境中做了配置：
```yaml
environment:
  - ALLOW_DOCKER_HEADED_CAPTCHA=true
shm_size: "2gb"  # 核心！为虚拟显示的 Chromium 提供足够的共享内存，防止崩溃
```

### 4. `docker-compose.proxy.yml` (双容器 WARP 代理)
它采用双容器编排将主应用和代理网关解耦：
* 启动一个 `warp` 容器（提供 Cloudflare 的 Socks5 代理服务）。
* 启动主要的 `flow2api` 服务，并通过 `depends_on` 依赖 warp，且配置内部使用 warp 暴露的 `1080` 端口作为上游代理。
* 它需要独立的配置文件 `./config/setting_warp.toml` 来实现特定的转发策略。

---

## 🛠️ 后续维护与调试建议

无论您选择了上述哪种部署方式，都可以通过以下核心命令查看日志与调试服务（以基础构架为例）：

**拉取更新并重启服务**：
```bash
docker compose pull
docker compose down
docker compose up -d
```

**查看实时运行日志**（可帮助判断由于验证码或风控导致的错误）：
```bash
docker compose logs -f
```

*(如果使用了 `docker-compose.headed.yml` 等特殊形式，请在对应命令中间加上 `-f xxx.yml`)*
