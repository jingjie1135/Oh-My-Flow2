# Upstream Main Merge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge `upstream/main` (`ab3b2c9`) into local `main` (`15de984`) without losing local Docker/headed captcha, diagnostics, documentation, and deployment-template work.

**Architecture:** Use a dedicated integration branch, perform one explicit `--no-ff` merge from `upstream/main`, resolve conflicts by subsystem, and commit each resolved subsystem independently. Treat upstream's functional fixes as the base for runtime behavior, then reapply local deployment/diagnostic/documentation additions where they are still needed.

**Tech Stack:** Git, Python 3.8+, FastAPI, SQLite runtime config, Docker Compose, browser captcha services, standard-library `unittest`.

---

## Current Merge Facts

- Local branch checked during analysis: `main` at `15de984 docs: 增加 browser 有头模式复现步骤`.
- Remote target: `upstream/main` at `ab3b2c9 fix(video): 兼容 Flow 视频媒体协议更新`.
- Merge base: `53565ec Beta (#116)`.
- Divergence: local has 20 commits not in upstream; upstream has 23 commits not in local.
- Upstream was force-updated during fetch from `bc9ebfa` to `ab3b2c9`.
- Simulated merge command used in an isolated worktree: `git merge --no-commit --no-ff upstream/main`.
- Direct merge result: conflict exit code `1`; main worktree stayed clean.

## Conflict Matrix

| File | Conflict type | Conflict hunks | Resolution owner | Resolution rule |
|---|---:|---:|---|---|
| `Dockerfile.headed` | content | 1 | deployment | Preserve local headed/root startup fixes; absorb upstream browser dependency/runtime updates. |
| `README.md` | content | 1 | documentation | Preserve local Docker captcha-mode documentation links; add upstream capability notes that still apply. |
| `config/setting.toml` | modify/delete | 1 | config | Accept upstream deletion from Git tracking; do not keep a real runtime config tracked. |
| `config/setting_example.toml` | content | 1 | config | Merge local captcha-mode fields with upstream runtime/model/YesCaptcha fields. |
| `docker/entrypoint.headed.sh` | content | 2 | deployment | Preserve local headed container bootstrap; add upstream stale-browser cleanup behavior. |
| `src/api/admin.py` | content | 12 | admin API | Merge local health/debug dashboard with upstream debug-log-tail and new health/admin surfaces. |
| `src/core/config.py` | content | 1 | core config | Keep both local captcha-mode settings and upstream runtime model/debug/max-retry settings. |
| `src/core/database.py` | content | 16 | persistence | Merge schema/runtime-config migrations so admin/config code has matching database fields. |
| `src/services/browser_captcha_personal.py` | content | 75 | captcha service | Start from upstream implementation, then reapply local resident warmup, root/headed readiness, and Docker constraints. |

## Non-Conflicting Upstream Changes To Review

These files auto-merge or add cleanly, but still need review because they affect runtime behavior:

- `extension/background.js`
- `extension/content.js`
- `extension/manifest.json`
- `extension/options.html`
- `extension/options.js`
- `requirements.txt`
- `src/api/routes.py`
- `src/core/model_resolver.py`
- `src/core/models.py`
- `src/core/monitoring.py`
- `src/main.py`
- `src/services/browser_captcha_extension.py`
- `src/services/browser_cookie_utils.py`
- `src/services/flow_client.py`
- `src/services/generation_handler.py`
- `src/services/load_balancer.py`
- `src/services/proxy_manager.py`
- `src/services/token_manager.py`
- `static/manage.html`
- `static/test.html`
- `tests/test_browser_captcha_personal.py`
- `tests/test_daily_stats_reset.py`
- `tests/test_flow_client_upload.py`
- `tests/test_veo_lite_support.py`
- `tests/test_yescaptcha_task_type.py`
- `tests/testgeneration_config_max_retries.py`

## File Responsibility Map

- `Dockerfile.headed`, `docker/entrypoint.headed.sh`, `docker-compose*.yml`: headed browser runtime and deployment wiring.
- `README.md`, `docs/*.md`, `AGENTS.md`: local operator documentation and AI/project guidance.
- `config/setting_example.toml`: versioned configuration contract for operators.
- `config/setting.toml`: runtime-local config; must not remain tracked after merge.
- `src/core/config.py`: config loading, defaults, and runtime key normalization.
- `src/core/database.py`: SQLite schema, migrations, persisted runtime/admin config.
- `src/api/admin.py`: admin APIs and management/health/debug data surfaces.
- `src/services/browser_captcha_personal.py`: personal/browser captcha orchestration, resident warmup, cleanup, concurrency, ST refresh.
- `src/services/flow_client.py`, `src/services/generation_handler.py`, `src/core/model_resolver.py`: upstream Flow/VideoFX protocol and model behavior.
- `static/manage.html`, `static/test.html`: web UI surfaces for admin/health/model testing.
- `tests/*.py`: regression coverage for merge-sensitive behavior.

---

### Task 1: Create the Integration Branch and Reproduce Conflicts

**Files:**
- No source edits in this task.

- [ ] **Step 1: Confirm the main worktree is clean**

Run:

```powershell
$env:GIT_MASTER='1'; git status --short --branch
```

Expected output begins with:

```text
## main...origin/main
```

Expected output has no modified file lines after the branch line.

- [ ] **Step 2: Create an integration branch**

Run:

```powershell
$env:GIT_MASTER='1'; git switch -c merge/upstream-main
```

Expected output:

```text
Switched to a new branch 'merge/upstream-main'
```

- [ ] **Step 3: Refresh upstream refs**

Run:

```powershell
$env:GIT_MASTER='1'; git fetch upstream --prune
```

Expected: `upstream/main` exists and points at, or newer than, `ab3b2c9`.

- [ ] **Step 4: Start the merge without committing**

Run:

```powershell
$env:GIT_MASTER='1'; git merge --no-commit --no-ff upstream/main
```

Expected output includes these conflicts:

```text
CONFLICT (content): Merge conflict in Dockerfile.headed
CONFLICT (content): Merge conflict in README.md
CONFLICT (modify/delete): config/setting.toml deleted in upstream/main and modified in HEAD
CONFLICT (content): Merge conflict in config/setting_example.toml
CONFLICT (content): Merge conflict in docker/entrypoint.headed.sh
CONFLICT (content): Merge conflict in src/api/admin.py
CONFLICT (content): Merge conflict in src/core/config.py
CONFLICT (content): Merge conflict in src/core/database.py
CONFLICT (content): Merge conflict in src/services/browser_captcha_personal.py
```

- [ ] **Step 5: Record the merge status**

Run:

```powershell
$env:GIT_MASTER='1'; git status --short
$env:GIT_MASTER='1'; git diff --name-only --diff-filter=U
```

Expected unmerged list:

```text
Dockerfile.headed
README.md
config/setting.toml
config/setting_example.toml
docker/entrypoint.headed.sh
src/api/admin.py
src/core/config.py
src/core/database.py
src/services/browser_captcha_personal.py
```

---

### Task 2: Resolve Runtime Config Tracking and Example Config

**Files:**
- Modify: `config/setting_example.toml`
- Delete from tracking: `config/setting.toml`
- Review: `.gitignore`

- [ ] **Step 1: Accept upstream deletion of tracked runtime config**

Run:

```powershell
$env:GIT_MASTER='1'; git rm config/setting.toml
```

Expected output includes:

```text
rm 'config/setting.toml'
```

Resolution rule: real runtime secrets and mutable runtime config must not be tracked. Operators should copy from `config/setting_example.toml` into local config or use Docker environment/volume wiring.

- [ ] **Step 2: Resolve `config/setting_example.toml` by keeping both sides' public config contract**

Open `config/setting_example.toml` and remove all conflict markers.

Keep these local captcha-mode fields if present in the conflicted file:

```toml
captcha_mode = "browser"
yescaptcha_api_key = ""
remote_browser_base_url = ""
remote_browser_api_key = ""
browser_captcha_headless = false
personal_warmup_resident_tabs = 1
```

Keep these upstream runtime/model fields if present in the conflicted file:

```toml
max_retries = 3
yescaptcha_task_type = "NoCaptchaTaskProxyless"
enable_debug_logging = false
debug_log_tail_lines = 200
```

If the exact key names differ in the conflicted file, use the names already referenced by `src/core/config.py` and `src/core/database.py` after their conflicts are resolved.

- [ ] **Step 3: Verify there are no markers in config files**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- config/setting_example.toml .gitignore
```

Expected output: no matches.

- [ ] **Step 4: Stage the config resolution**

Run:

```powershell
$env:GIT_MASTER='1'; git add .gitignore config/setting_example.toml
$env:GIT_MASTER='1'; git add -u config/setting.toml
$env:GIT_MASTER='1'; git diff --staged --stat -- .gitignore config/setting.toml config/setting_example.toml
```

Expected staged stat includes `config/setting.toml` deletion and `config/setting_example.toml` modification.

- [ ] **Step 5: Commit the config resolution**

Run:

```powershell
$env:GIT_MASTER='1'; git commit -m "chore(config): 合并上游配置契约" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected commit scope: only config tracking/example-config changes.

---

### Task 3: Resolve Headed Docker Runtime

**Files:**
- Modify: `Dockerfile.headed`
- Modify: `docker/entrypoint.headed.sh`
- Review: `docker-compose.headed.yml`
- Review: `docker-compose.local.yml`
- Review: `docker-compose.proxy.yml`
- Review: `docker-compose.yml`

- [ ] **Step 1: Resolve `Dockerfile.headed`**

Open `Dockerfile.headed` and remove the single conflict hunk.

Resolution rule:

```text
Use the upstream dependency/runtime package list when it adds browser or media runtime support.
Keep local container behavior that enables headed captcha inside Docker, especially non-interactive startup, root-safe browser execution, Xvfb/Fluxbox support, and entrypoint compatibility.
Do not reintroduce obsolete Compose version declarations.
```

- [ ] **Step 2: Resolve `docker/entrypoint.headed.sh`**

Open `docker/entrypoint.headed.sh` and remove both conflict hunks.

Resolution rule:

```text
Keep local startup order for Xvfb/Fluxbox/headed browser readiness.
Add upstream stale-browser-process cleanup before browser/session warmup.
Preserve environment variables required by local Docker captcha modes, including ALLOW_DOCKER_HEADED_CAPTCHA when present.
```

- [ ] **Step 3: Review auto-merged Compose files**

Run:

```powershell
$env:GIT_MASTER='1'; git diff -- docker-compose.headed.yml docker-compose.local.yml docker-compose.proxy.yml docker-compose.yml
```

Expected: no accidental port or volume loss for local headed/browser deployment. Keep mode-specific Compose files already present locally unless an upstream file intentionally replaces the same deployment entrypoint.

- [ ] **Step 4: Verify no Docker conflict markers remain**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- Dockerfile.headed docker/entrypoint.headed.sh docker-compose.headed.yml docker-compose.local.yml docker-compose.proxy.yml docker-compose.yml
```

Expected output: no matches.

- [ ] **Step 5: Stage and commit Docker runtime resolution**

Run:

```powershell
$env:GIT_MASTER='1'; git add Dockerfile.headed docker/entrypoint.headed.sh docker-compose.headed.yml docker-compose.local.yml docker-compose.proxy.yml docker-compose.yml
$env:GIT_MASTER='1'; git diff --staged --stat -- Dockerfile.headed docker/entrypoint.headed.sh docker-compose.headed.yml docker-compose.local.yml docker-compose.proxy.yml docker-compose.yml
$env:GIT_MASTER='1'; git commit -m "fix(deploy): 合并有头浏览器运行时" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected commit scope: headed Docker runtime and Compose wiring only.

---

### Task 4: Resolve Core Config, Database, and Admin API Together

**Files:**
- Modify: `src/core/config.py`
- Modify: `src/core/database.py`
- Modify: `src/api/admin.py`
- Review: `src/core/monitoring.py`
- Review: `src/main.py`
- Review: `static/manage.html`

- [ ] **Step 1: Resolve `src/core/config.py`**

Resolution rule:

```text
Keep upstream fields for model/runtime/debug/max-retry behavior.
Keep local fields for browser/personal/remote_browser captcha modes.
Ensure every key exposed in config/setting_example.toml has one read path or documented default here.
Do not add fallback branches for formats that no current config file or database row uses.
```

- [ ] **Step 2: Resolve `src/core/database.py`**

Resolution rule:

```text
Keep upstream schema migrations for monitoring, debug logging, daily stats reset, max_retries, and new token/model metadata.
Keep local persisted fields required by captcha mode selection, headed browser diagnostics, resident warmup state, and remote browser configuration.
Ensure migration order is monotonic and idempotent for existing SQLite databases.
```

After resolving, search for duplicate migration identifiers or duplicate `ALTER TABLE` blocks by running:

```powershell
$env:GIT_MASTER='1'; git grep -n -e 'ALTER TABLE' -e 'CREATE TABLE' -- src/core/database.py
```

Expected: duplicate-looking schema changes are intentionally guarded by existing idempotent helper logic.

- [ ] **Step 3: Resolve `src/api/admin.py`**

Resolution rule:

```text
Keep local runtime health dashboard and browser startup diagnostics.
Keep upstream debug log tail, monitoring summaries, and admin config endpoints.
When two endpoints overlap, prefer the route shape already used by static/manage.html after the merge, and keep the response fields consumed by both local and upstream UI code.
```

- [ ] **Step 4: Align `static/manage.html` with admin response shape**

Run:

```powershell
$env:GIT_MASTER='1'; git diff -- static/manage.html src/api/admin.py
```

Expected: every new field read by `static/manage.html` is produced by an endpoint in `src/api/admin.py`, and every changed endpoint still returns JSON shapes expected by the page.

- [ ] **Step 5: Verify no core/admin conflict markers remain**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- src/core/config.py src/core/database.py src/api/admin.py src/core/monitoring.py src/main.py static/manage.html
```

Expected output: no matches.

- [ ] **Step 6: Run focused import diagnostics**

Run:

```powershell
python -m py_compile src/core/config.py src/core/database.py src/api/admin.py src/core/monitoring.py src/main.py
```

Expected output: no syntax errors.

- [ ] **Step 7: Stage and commit core/admin resolution**

Run:

```powershell
$env:GIT_MASTER='1'; git add src/core/config.py src/core/database.py src/api/admin.py src/core/monitoring.py src/main.py static/manage.html
$env:GIT_MASTER='1'; git diff --staged --stat -- src/core/config.py src/core/database.py src/api/admin.py src/core/monitoring.py src/main.py static/manage.html
$env:GIT_MASTER='1'; git commit -m "fix(admin): 合并运行时配置与健康诊断" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected commit scope: admin/config/database/monitoring integration only.

---

### Task 5: Resolve Personal Browser Captcha Service

**Files:**
- Modify: `src/services/browser_captcha_personal.py`
- Review: `src/services/browser_captcha_extension.py`
- Review: `src/services/browser_cookie_utils.py`
- Review: `tests/test_browser_captcha_personal.py`

- [ ] **Step 1: Resolve imports and module-level constants first**

Resolution rule:

```text
Prefer upstream imports when they support nodriver compatibility, cookie utilities, extension support, or process cleanup.
Keep local imports/constants used by headed Docker readiness, resident tab warmup, and root container operation.
Delete duplicate imports introduced by conflict resolution.
```

- [ ] **Step 2: Resolve browser startup and cleanup sections**

Resolution rule:

```text
Keep upstream cleanup of residual browser processes.
Keep local startup behavior that allows personal/browser captcha modes to run in Docker headed mode.
Keep local resident warmup behavior when it is not superseded by an upstream method with the same user-visible behavior.
```

- [ ] **Step 3: Resolve captcha dispatch and concurrency sections**

Resolution rule:

```text
Prefer upstream fixes for fresh restart races, concurrent dispatch cleanup, nodriver connected-state checks, and personal scheduling.
Reapply local resident-tab readiness checks where they prevent Docker personal mode from reporting ready before the browser is usable.
```

- [ ] **Step 4: Resolve ST refresh and token state sections**

Resolution rule:

```text
Prefer upstream token/ST refresh fixes when they address known Flow/VideoFX protocol changes.
Keep local behavior that exposes useful startup diagnostics to admin APIs.
Do not keep two code paths that both refresh the same token state unless one is explicitly for remote_browser mode and one is for personal mode.
```

- [ ] **Step 5: Verify no captcha conflict markers remain**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- src/services/browser_captcha_personal.py src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py tests/test_browser_captcha_personal.py
```

Expected output: no matches.

- [ ] **Step 6: Run focused syntax check**

Run:

```powershell
python -m py_compile src/services/browser_captcha_personal.py src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py
```

Expected output: no syntax errors.

- [ ] **Step 7: Stage and commit captcha service resolution**

Run:

```powershell
$env:GIT_MASTER='1'; git add src/services/browser_captcha_personal.py src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py tests/test_browser_captcha_personal.py
$env:GIT_MASTER='1'; git diff --staged --stat -- src/services/browser_captcha_personal.py src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py tests/test_browser_captcha_personal.py
$env:GIT_MASTER='1'; git commit -m "fix(captcha): 合并 personal 浏览器调度修复" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected commit scope: personal/browser captcha implementation and its direct tests only.

---

### Task 6: Resolve README and Preserve Local Operator Docs

**Files:**
- Modify: `README.md`
- Preserve unless intentionally replaced: `AGENTS.md`
- Preserve unless intentionally replaced: `docs/Docker部署指南.md`
- Preserve unless intentionally replaced: `docs/Flow2API 架构分析.md`
- Preserve unless intentionally replaced: `docs/有头模式部署复现步骤.md`
- Preserve unless intentionally replaced: `docs/验证码模式 Docker 对照表.md`

- [ ] **Step 1: Resolve `README.md`**

Resolution rule:

```text
Keep local Docker captcha-mode deployment section and links to local docs.
Add upstream notes for extension support, monitoring/debug log tail, current model behavior, and Flow video protocol updates where those features are present after code merge.
Remove any README instructions that point to deleted tracked runtime config files.
```

- [ ] **Step 2: Keep local docs unless a section becomes false after merge**

Run:

```powershell
$env:GIT_MASTER='1'; git status --short -- AGENTS.md docs
```

Expected: local docs are not deleted by the merge unless the content has been intentionally replaced by a more accurate upstream file.

- [ ] **Step 3: Verify README links still target existing files**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e './docs/' -- README.md
```

Expected: every referenced `docs/...` path exists in the worktree.

- [ ] **Step 4: Verify no documentation conflict markers remain**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- README.md AGENTS.md docs
```

Expected output: no matches.

- [ ] **Step 5: Stage and commit documentation resolution**

Run:

```powershell
$env:GIT_MASTER='1'; git add README.md AGENTS.md docs
$env:GIT_MASTER='1'; git diff --staged --stat -- README.md AGENTS.md docs
$env:GIT_MASTER='1'; git commit -m "docs: 合并上游说明与本地部署文档" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected commit scope: docs and README only.

---

### Task 7: Review Auto-Merged Flow, Model, Extension, and UI Changes

**Files:**
- Review/stage as applicable: `extension/*`
- Review/stage as applicable: `requirements.txt`
- Review/stage as applicable: `src/api/routes.py`
- Review/stage as applicable: `src/core/model_resolver.py`
- Review/stage as applicable: `src/core/models.py`
- Review/stage as applicable: `src/services/browser_captcha_extension.py`
- Review/stage as applicable: `src/services/browser_cookie_utils.py`
- Review/stage as applicable: `src/services/flow_client.py`
- Review/stage as applicable: `src/services/generation_handler.py`
- Review/stage as applicable: `src/services/load_balancer.py`
- Review/stage as applicable: `src/services/proxy_manager.py`
- Review/stage as applicable: `src/services/token_manager.py`
- Review/stage as applicable: `static/test.html`
- Review/stage as applicable: new/updated `tests/*.py`

- [ ] **Step 1: Inspect auto-merged runtime changes**

Run:

```powershell
$env:GIT_MASTER='1'; git diff -- src/api/routes.py src/core/model_resolver.py src/core/models.py src/services/flow_client.py src/services/generation_handler.py src/services/load_balancer.py src/services/proxy_manager.py src/services/token_manager.py static/test.html
```

Expected: upstream Flow video protocol and model changes are retained; local model and Gemini compatibility behavior is not removed.

- [ ] **Step 2: Inspect extension additions**

Run:

```powershell
$env:GIT_MASTER='1'; git diff -- extension src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py
```

Expected: extension files are complete and service code imports them without missing package dependencies.

- [ ] **Step 3: Run syntax checks for auto-merged Python files**

Run:

```powershell
python -m py_compile src/api/routes.py src/core/model_resolver.py src/core/models.py src/services/flow_client.py src/services/generation_handler.py src/services/load_balancer.py src/services/proxy_manager.py src/services/token_manager.py src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py
```

Expected output: no syntax errors.

- [ ] **Step 4: Stage and commit auto-merged upstream feature set**

Run:

```powershell
$env:GIT_MASTER='1'; git add extension requirements.txt src/api/routes.py src/core/model_resolver.py src/core/models.py src/services/browser_captcha_extension.py src/services/browser_cookie_utils.py src/services/flow_client.py src/services/generation_handler.py src/services/load_balancer.py src/services/proxy_manager.py src/services/token_manager.py static/test.html tests/test_daily_stats_reset.py tests/test_flow_client_upload.py tests/test_veo_lite_support.py tests/test_yescaptcha_task_type.py tests/testgeneration_config_max_retries.py
$env:GIT_MASTER='1'; git diff --staged --stat
$env:GIT_MASTER='1'; git commit -m "feat(upstream): 合并视频协议与扩展支持" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected commit scope: upstream feature/test additions and non-conflicting runtime updates.

---

### Task 8: Final Conflict Scan and Merge Commit Completion

**Files:**
- All files in merge result.

- [ ] **Step 1: Confirm there are no conflict markers anywhere**

Run:

```powershell
$env:GIT_MASTER='1'; git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- .
```

Expected output: no matches.

- [ ] **Step 2: Confirm no unmerged paths remain**

Run:

```powershell
$env:GIT_MASTER='1'; git diff --name-only --diff-filter=U
$env:GIT_MASTER='1'; git status --short
```

Expected: no `UU`, `UD`, `DU`, `AA`, `AU`, `UA`, or `DD` status lines.

- [ ] **Step 3: Commit the merge if Git still has an active merge state**

Run:

```powershell
$env:GIT_MASTER='1'; git status --short
$env:GIT_MASTER='1'; git commit -m "merge: 合并 upstream/main 更新" -m "Ultraworked with [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent)" -m "Co-authored-by: Sisyphus <clio-agent@sisyphuslabs.ai>"
```

Expected: merge commit is created only after all subsystem commits have resolved and staged their files. If the earlier subsystem commits already consumed the merge state cleanly, this command reports there is nothing to commit; in that case continue to verification.

---

### Task 9: Verification Gate

**Files:**
- No planned source edits in this task.

- [ ] **Step 1: Run the full test suite**

Run:

```powershell
python -m unittest discover tests
```

Expected: all discovered tests pass. If tests fail, fix the failing behavior in the same subsystem commit that introduced the failure; do not delete or weaken tests.

- [ ] **Step 2: Run a syntax sweep over source**

Run:

```powershell
python -m compileall src
```

Expected: compileall completes without syntax errors.

- [ ] **Step 3: Manually QA the HTTP surface**

Run in one terminal:

```powershell
python main.py
```

Expected: FastAPI/Uvicorn starts without import or migration errors.

In another terminal, run:

```powershell
curl.exe -i http://127.0.0.1:8000/
curl.exe -i http://127.0.0.1:8000/test
```

Expected: the root/admin UI and model test page return HTTP `200` or the expected login/static page response. Record any route that returns an unexpected `5xx`.

- [ ] **Step 4: Manually QA the Docker headed surface enough to catch startup regressions**

Run:

```powershell
docker compose -f docker-compose.headed.yml config
```

Expected: Compose config renders successfully. If Docker is available and the environment is intended for container QA, also run:

```powershell
docker compose -f docker-compose.headed.yml build
```

Expected: headed image builds without missing packages or script permission errors.

- [ ] **Step 5: Review final history and worktree**

Run:

```powershell
$env:GIT_MASTER='1'; git log --oneline --decorate -10
$env:GIT_MASTER='1'; git status --short --branch
```

Expected: branch is `merge/upstream-main`, merge commits are visible, and worktree is clean.

---

## Commit Plan Summary

Planned commits are intentionally split by subsystem:

1. `chore(config): 合并上游配置契约`
   - `config/setting.toml`
   - `config/setting_example.toml`
   - `.gitignore`
2. `fix(deploy): 合并有头浏览器运行时`
   - `Dockerfile.headed`
   - `docker/entrypoint.headed.sh`
   - relevant `docker-compose*.yml`
3. `fix(admin): 合并运行时配置与健康诊断`
   - `src/core/config.py`
   - `src/core/database.py`
   - `src/api/admin.py`
   - `src/core/monitoring.py`
   - `src/main.py`
   - `static/manage.html`
4. `fix(captcha): 合并 personal 浏览器调度修复`
   - `src/services/browser_captcha_personal.py`
   - `src/services/browser_captcha_extension.py`
   - `src/services/browser_cookie_utils.py`
   - `tests/test_browser_captcha_personal.py`
5. `docs: 合并上游说明与本地部署文档`
   - `README.md`
   - `AGENTS.md`
   - `docs/*.md`
6. `feat(upstream): 合并视频协议与扩展支持`
   - non-conflicting upstream feature/runtime/test additions
7. `merge: 合并 upstream/main 更新`
   - final merge commit if required by Git's merge state

## Stop Conditions

- Stop and inspect before committing if `git diff --name-only --diff-filter=U` prints any path.
- Stop and inspect before committing if `git grep -n -e '<<<<<<<' -e '=======' -e '>>>>>>>' -- .` prints any path.
- Stop and inspect if `python -m py_compile` fails on any resolved Python file.
- Stop and ask for a decision before deleting local documentation or mode-specific Compose templates.
- Stop and ask for a decision before force-pushing; the recommended merge branch should use normal push, not force push.

## Expected Outcome

After execution, the repo has a clean `merge/upstream-main` branch that contains upstream Flow/video/captcha/model fixes plus the local deployment diagnostics and documentation. The tracked runtime config file `config/setting.toml` is removed, public config examples are complete, tests pass, and the admin/test HTTP surfaces start successfully.
