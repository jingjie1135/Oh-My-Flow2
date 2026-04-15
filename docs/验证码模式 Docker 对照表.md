# 验证码模式 Docker 对照表

本文档汇总 Flow2API 当前支持的 4 种验证码模式对应的 Docker / Compose 配置、依赖要求、端口映射和验证结果，便于部署时快速选择。

## 总览

| 模式 | Compose 文件 | 配置文件 | 端口 | 关键依赖 | 当前验证结果 |
|---|---|---|---|---|---|
| `yescaptcha` | `docker-compose.yescaptcha.yml` | `config/setting.yescaptcha.toml` | `38100` | `yescaptcha_api_key` | 容器启动成功，`/` 和 `/login` 返回 `200` |
| `browser` | `docker-compose.browser.yml` | `config/setting.browser.toml` | `38101` | Docker 内 `Xvfb + Fluxbox`、Playwright | 已修复 X server 问题，浏览器 slot 预热成功 |
| `personal` | `docker-compose.personal.yml` | `config/setting.personal.toml` | `38102` | Docker 内显示环境、nodriver | 成功预热 5 个常驻标签页 |
| `remote_browser` | `docker-compose.remote-browser.yml` | `config/setting.remote_browser.toml` | `38103` | 外部 `remote_browser_base_url` + `remote_browser_api_key` | 容器启动成功，接口返回 `200`；真正打码仍依赖外部服务 |

## 各模式说明

### 1. yescaptcha

- 适合最简单的第三方打码接入场景。
- 启动前需要在 `config/setting.yescaptcha.toml` 中填写 `yescaptcha_api_key`。
- 本地验证结果：
  - 容器启动成功
  - `http://localhost:38100/` 返回 `200`
  - `http://localhost:38100/login` 返回 `200`

启动命令：

```bash
docker compose -f docker-compose.yescaptcha.yml up -d --build
```

### 2. browser

- 适合按请求启动浏览器进行验证码处理的场景。
- 依赖 Docker 内有头显示环境，因此对应镜像已补齐 `Xvfb + Fluxbox`。
- 本次已修复此前 `Missing X server or $DISPLAY` 的问题。
- 本地验证结果：
  - 容器启动成功
  - 浏览器 slot 预热成功
  - `http://localhost:38101/` 返回 `200`
  - `http://localhost:38101/login` 返回 `200`

启动命令：

```bash
docker compose -f docker-compose.browser.yml up -d --build
```

### 3. personal

- 适合常驻标签页模式，支持更稳定的验证码处理和 ST 自动续期。
- 同样依赖 Docker 内显示环境。
- 本地验证结果：
  - 容器启动成功
  - 成功预热 5 个常驻标签页
  - `http://localhost:38102/` 返回 `200`
  - `http://localhost:38102/login` 返回 `200`

启动命令：

```bash
docker compose -f docker-compose.personal.yml up -d --build
```

### 4. remote_browser

- 适合把验证码处理转发到外部远程浏览器 / token 池服务的场景。
- 启动前需要在 `config/setting.remote_browser.toml` 中至少填写：
  - `remote_browser_base_url`
  - `remote_browser_api_key`
- 本地验证结果：
  - 容器启动成功
  - `http://localhost:38103/` 返回 `200`
  - `http://localhost:38103/login` 返回 `200`
- 注意：当前仓库只能验证服务容器和 HTTP 接口是否正常启动，真正的远程打码是否可用仍取决于外部服务是否已正确部署。

启动命令：

```bash
docker compose -f docker-compose.remote-browser.yml up -d --build
```

## 目录隔离说明

每种模式都使用了独立的数据目录与临时目录：

- `data/yescaptcha`
- `data/browser`
- `data/personal`
- `data/remote-browser`
- `tmp/yescaptcha`
- `tmp/browser`
- `tmp/personal`
- `tmp/remote-browser`

这样做的目的是避免 SQLite 把某一种模式的配置持久化后污染另一种模式。

## 建议选择

- 想最快部署：选 `yescaptcha`
- 想直接在容器里跑浏览器：选 `browser`
- 想要更稳定、支持常驻标签页：选 `personal`
- 已经有外部 token 池基础设施：选 `remote_browser`
