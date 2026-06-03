#!/bin/sh
set -eu

DISPLAY_VALUE="${DISPLAY:-:99}"
XVFB_SCREEN_VALUE="${XVFB_SCREEN:-1440x900x24}"
export DISPLAY="${DISPLAY_VALUE}"

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
    detected_browser_path="$(resolve_browser_path 2>/dev/null | tr -d '' | tail -n 1)"
    if [ -n "${detected_browser_path}" ] && [ -x "${detected_browser_path}" ]; then
        export BROWSER_EXECUTABLE_PATH="${detected_browser_path}"
    fi
fi

if [ "${ALLOW_DOCKER_HEADED_CAPTCHA:-true}" = "true" ] || [ "${ALLOW_DOCKER_HEADED_CAPTCHA:-1}" = "1" ]; then
    display_suffix="$(printf '%s' "${DISPLAY}" | sed 's/^://; s/\..*$//')"
    socket_path="/tmp/.X11-unix/X${display_suffix}"

    mkdir -p /tmp/.X11-unix
    rm -f "/tmp/.X${display_suffix}-lock"

    echo "[entrypoint] starting Xvfb on DISPLAY=${DISPLAY} (${XVFB_SCREEN_VALUE})"
    Xvfb "${DISPLAY}" -screen 0 "${XVFB_SCREEN_VALUE}" -ac +extension RANDR >/tmp/xvfb.log 2>&1 &
    XVFB_PID=$!

    waited=0
    while [ ! -S "${socket_path}" ] && [ "${waited}" -lt 100 ]; do
        sleep 0.1
        waited=$((waited + 1))
    done

    if [ ! -S "${socket_path}" ]; then
        echo "[entrypoint] failed to start Xvfb, socket not ready: ${socket_path}" >&2
        exit 1
    fi

    echo "[entrypoint] starting Fluxbox on DISPLAY=${DISPLAY}"
    fluxbox >/tmp/fluxbox.log 2>&1 &
    FLUXBOX_PID=$!
fi

echo "[entrypoint] starting flow2api (headed browser mode)"
if [ -n "${BROWSER_EXECUTABLE_PATH:-}" ] && [ -x "${BROWSER_EXECUTABLE_PATH}" ]; then
    echo "[entrypoint] browser executable: ${BROWSER_EXECUTABLE_PATH}"
    "${BROWSER_EXECUTABLE_PATH}" --version || true
else
    echo "[entrypoint] warning: no valid browser executable found for personal/browser captcha" >&2
fi

exec python main.py
