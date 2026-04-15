#!/bin/sh
set -eu

XVFB_DISPLAY="${DISPLAY:-:99}"
XVFB_SCREEN="${XVFB_SCREEN:-1280x720x24}"

cleanup() {
    if [ -n "${FLUXBOX_PID:-}" ] && kill -0 "${FLUXBOX_PID}" 2>/dev/null; then
        kill "${FLUXBOX_PID}" 2>/dev/null || true
    fi
    if [ -n "${XVFB_PID:-}" ] && kill -0 "${XVFB_PID}" 2>/dev/null; then
        kill "${XVFB_PID}" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

resolve_browser_path() {
python - <<'PY'
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    print(p.chromium.executable_path or "")
PY
}

if [ -z "${BROWSER_EXECUTABLE_PATH:-}" ] || [ ! -x "${BROWSER_EXECUTABLE_PATH:-}" ]; then
    detected_browser_path="$(resolve_browser_path 2>/dev/null | tr -d '\r' | tail -n 1)"
    if [ -n "${detected_browser_path}" ] && [ -x "${detected_browser_path}" ]; then
        export BROWSER_EXECUTABLE_PATH="${detected_browser_path}"
    fi
fi

export DISPLAY="${XVFB_DISPLAY}"

echo "[entrypoint] starting virtual display ${DISPLAY} (${XVFB_SCREEN})"
Xvfb "${DISPLAY}" -screen 0 "${XVFB_SCREEN}" -ac +extension RANDR >/tmp/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 1

echo "[entrypoint] starting fluxbox window manager"
fluxbox >/tmp/fluxbox.log 2>&1 &
FLUXBOX_PID=$!
sleep 1

echo "[entrypoint] starting flow2api (headed browser mode)"
if [ -n "${BROWSER_EXECUTABLE_PATH:-}" ] && [ -x "${BROWSER_EXECUTABLE_PATH}" ]; then
    echo "[entrypoint] browser executable: ${BROWSER_EXECUTABLE_PATH}"
    "${BROWSER_EXECUTABLE_PATH}" --version || true
else
    echo "[entrypoint] warning: no valid browser executable found for personal/browser captcha" >&2
fi

exec python main.py
