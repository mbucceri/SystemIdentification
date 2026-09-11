#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/../.." && pwd)"

TARGET="${1:-linux}"
MODE="${2:-debug}"

case "${TARGET}" in
    linux|linux_rt) ;;
    *)
        echo "Unsupported target: ${TARGET}" >&2
        echo "Supported targets: linux, linux_rt" >&2
        exit 2
        ;;
esac

case "${MODE}" in
    debug) CMAKE_BUILD_TYPE="Debug" ;;
    release) CMAKE_BUILD_TYPE="Release" ;;
    *)
        echo "Unsupported build mode: ${MODE}" >&2
        echo "Supported modes: debug, release" >&2
        exit 2
        ;;
esac

BUILD_DIR="${REPO_ROOT}/build/${TARGET}-${MODE}"

cmake \
    -S "${PROJECT_DIR}" \
    -B "${BUILD_DIR}" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
    -DSYSTEMID_TARGET="${TARGET}"

cmake --build "${BUILD_DIR}"

ctest \
    --test-dir "${BUILD_DIR}" \
    --output-on-failure